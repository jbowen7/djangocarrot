from django.db.models.signals import post_save
from django.dispatch import receiver
from carrot.utils import RabbitHelper
from carrot.models import QueuedTask

# Signals
@receiver(post_save, sender=QueuedTask)
def send_message_to_rabbitmq(sender, instance, created, **kwargs):
	if created:
		message_dict = dict()
		message_dict['task_id'] = int(instance.id)
		message_dict['task_name'] = instance.name
		message_dict['app'] = instance.app
		try:
			RabbitHelper().send_message('carrot', 'worker-manager', str(message_dict))
			instance.message_sent = True
		except:
			instance.message_sent = False
