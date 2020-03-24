import logging
from django.apps import AppConfig

LOGGER = logging.getLogger(__name__)


class CarrotConfig(AppConfig):
	name = 'carrot'
	verbose_name = "Carrots are better than celery"

	def ready(self):
		from carrot.connections import publisher  # noqa
		from carrot.settings import carrot_settings  # noqa

		# Initialize queues, exchanges
		publisher.connect()
		for queue, queue_settings in carrot_settings['queues'].items():
			LOGGER.info(f"Initializing queue ({queue_settings['queue_name']})")
			publisher.setup_queue_exchange(
				exchange=carrot_settings['exchange'],
				queue=queue_settings['queue_name'],
				routing_key=queue_settings['queue_name'],
				durable_exchange=carrot_settings['durable_exchange'],
				durable_queue=queue_settings['durable_queue'],
			)
		publisher.close()
