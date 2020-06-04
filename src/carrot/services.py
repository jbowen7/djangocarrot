import logging

from django.db import connections
from django.db.utils import OperationalError

from carrot.models import Task
from carrot.amqp import RabbitConsumer
from carrot.settings import carrot_settings


LOGGER = logging.getLogger(__name__)


class Worker(RabbitConsumer):
	"""
	Worker is a serial queued task consumer
	"""
	PREFETCH_COUNT = 1

	def __init__(self, queue, *args, **kwargs):
		assert queue in carrot_settings['queues'], f"{queue} is not a valid queue"

		kwargs['queue'] = carrot_settings['queues'][queue]['queue_name']
		kwargs['exchange'] = carrot_settings['exchange']
		kwargs['host'] = carrot_settings['host']
		kwargs['port'] = carrot_settings['port']
		kwargs['user'] = carrot_settings['user']
		kwargs['password'] = carrot_settings['password']

		kwargs['prefetch_count'] = self.PREFETCH_COUNT
		kwargs['callback'] = self.on_message

		super().__init__(*args, **kwargs)

	def run(self):
		# Ensure new db fds are opened since workers are commonly forks
		connections.close_all()
		return super().run()

	def on_message(self, message):
		try:
			task = Task.objects.get(id=message)
		except Task.DoesNotExist:
			LOGGER.error(f"task ({message}) does not exist, unable to execute task")
		except OperationalError:
			# client timeout might cause db connections to close. Attempt reconnect
			connections.close_all()
			task = Task.objects.get(id=message)

		try:
			task.execute()
		except: # noqa
			LOGGER.exception("Carrot Worker caught an exception, the task failed, but the worker does not die")
