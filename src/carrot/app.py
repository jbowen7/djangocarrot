from django.apps import AppConfig


class CarrotConfig(AppConfig):
	name = 'carrot'
	verbose_name = "Carrots are better than celery"

	def ready(self):
		from carrot.connections import publisher  # noqa
		from carrot.settings import carrot_settings  # noqa

		# Setup RabbitMQ resources
		for queue in carrot_settings['queues']:
			publisher.setup_queue_exchange(
				exchange=carrot_settings['exchange'],
				queue=queue.name,
				routing_key=queue.name,
				durable_exchange=carrot_settings['durable_exchange'],
				durable_queue=carrot_settings['durable_queues'],
			)
