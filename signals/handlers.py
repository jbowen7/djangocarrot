from django.db.models.signals import post_save
from django.dispatch import receiver
from carrot.utils import RabbitHelper
from carrot.models import Task

# Signals
@receiver(post_save, sender=Task)
def send_message_to_rabbitmq(sender, instance, created, **kwargs):
	if created:
		message = str(int(instance.id))
		try:
			RabbitHelper().send_message(instance.exchange, instance.routing_key, message)
		except Exception as e:
			instance.status = 'Error: could not deliver message. Reason: RabbitMQ Exception(%s)' % e.__class__.__name__
			instance.save()
