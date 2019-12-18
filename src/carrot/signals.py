from carrot.models import Task


def publish_task(sender, instance, created, **kwargs):
	"""
	Signal handler responsible for publishing amqp messages for newly created models.Task
	"""
	assert isinstance(sender, Task)
	if created and instance.queue:
		instance.publish()
