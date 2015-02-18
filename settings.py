from django.apps import AppConfig

class CarrotConfig(AppConfig):
	name = 'carrot'
	verbose_name = "Carrot's are better than celery"

	def ready(self):
		import carrot.signals.handlers

## Where functions can be found for an app
DEFAULT_TASK_MODULE="tasks"
