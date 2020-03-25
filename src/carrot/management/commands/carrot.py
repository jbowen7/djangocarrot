import logging
import signal
import multiprocessing

from django.core.management.base import BaseCommand

from carrot.services import Worker
from carrot.settings import carrot_settings


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
	def handle(self, *args, **options):
		LOGGER.info("Carrot starting")

		signal.signal(signal.SIGTERM, self._sigterm)
		signal.signal(signal.SIGINT, self._sigterm)

		workers = []
		for queue, settings in carrot_settings['queues'].items():
			for _ in range(int(settings['worker_concurrency'])):
				workers.append(Worker(queue))

		processes = []
		for worker in workers:
			p = multiprocessing.Process(target=worker.run, daemon=True)
			p.start()
			processes.append(p)

		for p in processes:
			p.join()

		LOGGER.info("Carrot shutdown complete")

	def _sigterm(self, signum, frame):
		# Nothing needs to be done. The forked worker processes will handle their own signal
		# and eventually the processes will be joined (hopefully)
		LOGGER.info(f"Carrot received shutdown signal ({signum}). Waiting for children to join")
