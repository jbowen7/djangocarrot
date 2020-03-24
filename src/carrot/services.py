import logging
#from multiprocessing import Process, active_children, Pool
import multiprocessing
import signal

from django.db import connections

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
			LOGGER.exception(f"task ({message}) does not exist, unable to execute task")
		else:
			task.execute()


class WorkerService:
	"""
	WorkerService is used to manage multipe Worker instances for Task concurrency
	"""
	def __init__(self, workers):
		assert all([isinstance(x, Worker) for x in workers]), "invalid arg (workers) must be an iterable of Worker instances"
		self.workers = workers

	def run(self):
		signal.signal(signal.SIGTERM, self._sigterm)
		signal.signal(signal.SIGINT, self._sigterm)

		processes = []
		for worker in self.workers:
			p = multiprocessing.Process(target=worker.run, daemon=True)
			p.start()
			processes.append(p)

		for p in processes:
			p.join()

	def _sigterm(self, signum, frame):
		# Nothing needs to be done. The forked worker processes will handle their own signal
		# and eventually the processes will be joined (hopefully)
		LOGGER.info(f"WorkerService received shutdown signal ({signum}). Waiting for children to join")
