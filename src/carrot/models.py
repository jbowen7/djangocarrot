from django.db import models
from django.core.validators import ValidationError

from carrot.fields import ListField, DictField

import importlib


DEFAULT_WORKER_NAME = 'default'
DEFAULT_EXCHANGE = 'carrot'


def get_default_worker_id():
	"""
	Function is used to ensure we always have a default worker
	"""
	worker, created = Worker.objects.get_or_create(name=DEFAULT_WORKER_NAME, defaults={"name": DEFAULT_WORKER_NAME})
	return worker.id


class Task(models.Model):
	kallable = models.CharField(max_length=255)
	args = ListField(null=True, blank=True)
	kwargs = DictField(null=True, blank=True)
	worker = models.ForeignKey('Worker', default=get_default_worker_id, on_delete=models.PROTECT)
	status = models.CharField(max_length=255, null=True, blank=True)
	completed = models.BooleanField(default=False)
	date_created = models.DateTimeField(auto_now_add=True)
	date_processed = models.DateTimeField(null=True, blank=True)
	date_completed = models.DateTimeField(null=True, blank=True)

	def execute(self):
		split_path = self.kallable.split('.')
		module_name, callable_name = ".".join(split_path[:-1]), split_path[-1]
		module = importlib.import_module(module_name)
		func = getattr(module, callable_name)
		return func(*self.args, **self.kwargs)

	@property
	def exchange(self):
		return DEFAULT_EXCHANGE

	@property
	def queue(self):
		return "%s-%s" % (self.exchange, self.worker.name)

	@property
	def routing_key(self):
		return "%s-%s" % (self.exchange, self.worker.name)

	def clean(self, *args, **kwargs):
		try:
			split_path = self.kallable.split('.')
			module_name, callable_name = ".".join(split_path[:-1]), split_path[-1]
			module = importlib.import_module(module_name)
			kallable = getattr(module, callable_name)
			assert callable(kallable)
		except ValueError:
			raise ValidationError("Callable not valid. Requires full dot-notation path, e.g. app.utils.my_function" % self.kallable)
		except ImportError:
			raise ValidationError("Module (%s) cannot be imported" % module_name)
		except AttributeError:
			raise ValidationError("Callable (%s) not found in module (%s)" % (callable_name, module_name))
		except AssertionError:
			raise ValidationError("Callable (%s) is not callable" % (callable_name,))

		return super().clean(*args, **kwargs)

	def save(self, *args, **kwargs):
		self.clean()
		return super().save(*args, **kwargs)


class Worker(models.Model):
	name = models.CharField(max_length=255)
	description = models.CharField(max_length=255, blank=True, null=True)
	concurrency = models.IntegerField(default=4)
	enabled = models.BooleanField(default=True)

	@property
	def exchange(self):
		return DEFAULT_EXCHANGE

	@property
	def queue(self):
		return "%s-%s" % (self.exchange, self.name)

	@property
	def routing_key(self):
		return "%s-%s" % (self.exchange, self.name)
