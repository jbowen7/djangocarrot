import logging

from django.core.management.base import BaseCommand

from carrot.services import WorkerService, Worker
from carrot.settings import carrot_settings


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
	def handle(self, *args, **options):
		LOGGER.info("Carrot starting")

		workers = []
		for q in carrot_settings['queues']:
			for _ in range(q.concurrency):
				workers.append(Worker(q.id))

		WorkerService(workers).run()
		LOGGER.info("Carrot stopped")
