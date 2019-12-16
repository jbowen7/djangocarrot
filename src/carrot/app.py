from django.apps import AppConfig
from django.db.models.signals import post_save


class CarrotConfig(AppConfig):
	name = 'carrot'
	verbose_name = "Carrots are better than celery"

	def ready(self):
		from carrot.models import Task  # noqa
		from carrot.signals import publish_task  # noqa

		post_save.connect(publish_task, Task)
