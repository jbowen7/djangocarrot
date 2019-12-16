from carrot.amqp import RabbitPublisher
from carrot.models import Task

#TODO:jbowen7 move this into a connectino class
publisher = RabbitPublisher(queue='carrot', exchange='carrot', routing_key='carrot')
publisher.connect()
publisher.setup_queue_exchange()


def publish_task(sender, instance, created, **kwargs):
	"""
	Signal handler responsible for publishing amqp messages for newly created models.Task
	"""
	assert isinstance(sender, Task)

	if created:
		publisher.publish(str(instance.id))
