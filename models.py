from django.db import models
from jsonfield import JSONField


class QueuedTask(models.Model):
	name = models.CharField(max_length=255)
	app = models.CharField(max_length=255)
	data = JSONField()
	user_id = models.IntegerField(null=True, blank=True)
	status = models.CharField(max_length=255, null=True, blank=True)
	completed = models.BooleanField(default=False)
	date_created = models.DateTimeField(auto_now_add=True)
	date_completed = models.DateTimeField(null=True, blank=True)

