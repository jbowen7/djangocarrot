from django.apps import AppConfig

class CarrotConfig(AppConfig):
	name = 'carrot'
	verbose_name = "Carrots are better than celery"

	def ready(self):
		import carrot.signals.handlers

