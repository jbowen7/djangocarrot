import logging
import importlib

from django.db import models
from django.core.validators import ValidationError
from django.utils import timezone

from carrot.fields import ListField, DictField
from carrot.connections import publisher
from carrot.settings import carrot_settings


LOGGER = logging.getLogger(__name__)


class Task(models.Model):
	class Status(models.Choices):
		PENDING = 1
		RUNNING = 2
		COMPLETED = 3
		FAILED = 4

	class ExitCode(models.Choices):
		SUCCESS = 0
		UNKNOWN_ERROR = 1

	kallable = models.CharField(max_length=512)
	args = ListField(null=True, blank=True)
	kwargs = DictField(null=True, blank=True)

	queue = models.CharField(blank=True, null=True, max_length=255)
	created_by = models.CharField(max_length=512, blank=True, null=True)

	status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING, db_index=True)
	message = models.CharField(max_length=2048, blank=True, null=True)
	exit_code = models.SmallIntegerField(choices=ExitCode.choices, blank=True, null=True)

	created_on = models.DateTimeField(auto_now_add=True)
	started_on = models.DateTimeField(null=True, blank=True)
	completed_on = models.DateTimeField(null=True, blank=True)

	def execute(self):
		"""
		Execute the function that this task represents
		"""
		self.started_on = timezone.now()
		LOGGER.debug(f'Executing task ({self.id}) => ({self.kallable})')

		try:
			split_path = self.kallable.split('.')
			module_name, callable_name = ".".join(split_path[:-1]), split_path[-1]
			module = importlib.import_module(module_name)
			func = getattr(module, callable_name)
			func(*self.args, **self.kwargs)
			self.exit_code = self.ExitCode.SUCCESS

		except Exception as e:
			LOGGER.exception('Unknown exception processing task ({self.id})')
			self.exit_code = self.ExitCode.UNKNOWN_ERROR
			self.message = str(e)

		finally:
			self.status = self.Status.COMPLETED if self.exit_code == self.ExitCode.SUCCESS else self.Status.FAILED
			self.completed_on = timezone.now()

			# Transient tasks are valid. Only save fields if an id exists, i.e. it's stored in the db
			if self.id:
				self.save(update_fields={'exit_code', 'completed_on', 'message', 'started_on'})

		return self.exit_code == self.ExitCode.SUCCESS

	def publish(self):
		"""
		Publishes message to configured RabbitMQ connection if self.queue is a valid Queue member
		"""
		queue = carrot_settings['queue_map'].get(self.queue, None)
		assert queue is not None, f"({self.queue}) is not a valid carrot queue"

		publisher.publish(
			message=str(self.id),
			exchange=carrot_settings['exchange'],
			routing_key=queue.name,
		)

	def clean(self, *args, **kwargs):
		try:
			split_path = self.kallable.split('.')
			module_name, callable_name = ".".join(split_path[:-1]), split_path[-1]
			module = importlib.import_module(module_name)
			kallable = getattr(module, callable_name)
			assert callable(kallable)
		except ValueError:
			raise ValidationError(f"Callable not valid. Requires full dot-notation path, e.g. app.utils.my_function")
		except ImportError:
			raise ValidationError("Module (%s) cannot be imported" % module_name)
		except AttributeError:
			raise ValidationError("Callable (%s) not found in module (%s)" % (callable_name, module_name))
		except AssertionError:
			raise ValidationError("Callable (%s) is not callable" % (callable_name,))

		if self.queue and self.queue not in carrot_settings['queue_map']:
			raise ValidationError(f"({self.queue}) is not a valid carrot queue")

		return super().clean(*args, **kwargs)

	def save(self, *args, **kwargs):
		self.clean()
		return super().save(*args, **kwargs)
