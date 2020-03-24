import logging

from django.db import models
from django.core.validators import ValidationError
from django.utils import timezone

from carrot.fields import ListField, DictField
from carrot.connections import publisher
from carrot.settings import carrot_settings, DEFAULT_QUEUE_NAME
from carrot.utils import import_callable


LOGGER = logging.getLogger(__name__)
EMPTY_STRING = ''


class Task(models.Model):
	"""
	Instances of Task represent an unexecuted call to a function with pre-selected args and kwargs.
	Task instances can publish themselves to a queue for asynchronous consumption, or can be executed
	directly with self.execute()
	"""
	class Status(models.Choices):
		PENDING = 'pending'
		RUNNING = 'running'
		COMPLETED = 'completed'
		FAILED = 'failed'

	class ExitCode(models.IntegerChoices):
		SUCCESS = 0
		UNKNOWN_ERROR = 1

	kallable = models.CharField(max_length=512)
	args = ListField(blank=True, default=EMPTY_STRING)
	kwargs = DictField(blank=True, default=EMPTY_STRING)

	queue = models.CharField(max_length=255, blank=True, default=DEFAULT_QUEUE_NAME)

	status = models.CharField(max_length=255, choices=Status.choices, default=Status.PENDING)
	message = models.CharField(max_length=2048, default=EMPTY_STRING)
	exit_code = models.SmallIntegerField(choices=ExitCode.choices, blank=True, null=True)
	created_by = models.CharField(max_length=512, blank=True, default=EMPTY_STRING)

	created_on = models.DateTimeField(auto_now_add=True)
	started_on = models.DateTimeField(null=True, blank=True)
	completed_on = models.DateTimeField(null=True, blank=True)

	@property
	def can_publish(self):
		return self.queue in carrot_settings['queues']

	def execute(self):
		"""
		Execute the function that this task represents
		"""
		# List/Dict fields work as expect when initialized from db
		if not isinstance(self.args, list):
			self.refresh_from_db()
		elif not isinstance(self.kwargs, dict):
			self.refresh_from_db()

		self.started_on = timezone.now()
		self.status = self.Status.RUNNING
		if self.id:
			self.save(update_fields={'status', 'started_on'})

		LOGGER.info(f'Executing task ({self.id}) => ({self.kallable})')
		try:
			func = import_callable(self.kallable)
			func(*self.args, **self.kwargs)
			self.exit_code = self.ExitCode.SUCCESS
			self.message = ''

		except Exception as e:
			LOGGER.exception('Error processing task ({self.id})')
			self.exit_code = self.ExitCode.UNKNOWN_ERROR
			self.message = repr(e)

		finally:
			self.status = self.Status.COMPLETED if self.exit_code == self.ExitCode.SUCCESS else self.Status.FAILED
			self.completed_on = timezone.now()
			if self.id:
				self.save(update_fields={'status', 'exit_code', 'completed_on', 'message'})

		return self.exit_code == self.ExitCode.SUCCESS

	def publish(self):
		"""
		Publishes message to configured RabbitMQ connection if self.queue is a valid Queue member
		"""
		assert self.can_publish, f"queue ({self.queue}) is not a valid queue to publish to"
		publisher.publish(
			message=str(self.id),
			exchange=carrot_settings['exchange'],
			routing_key=carrot_settings['queues'][self.queue]['queue_name'],
		)

	def validate(self):
		"""
		Used to verify that a kallable is both importable and is callable
		Also, used to verify that a queue is valid, if set
		"""
		# Make sure self.kallable is importable and is a callable object
		func = import_callable(self.kallable)
		if not callable(func):
			raise ValidationError(f"Callable ({self.kallable}) is not callable")

		# If instance has `queue` set, require that it exists
		if self.queue and self.queue not in carrot_settings['queues']:
			raise ValidationError(f"({self.queue}) is not a valid carrot queue")

	def save(self, *args, **kwargs):
		"""
		Enforces validation and publishes to queue during creation if queue is set
		"""
		is_new = self._state.adding
		self.validate()
		super().save(*args, **kwargs)
		if is_new and self.can_publish:
			self.publish()
