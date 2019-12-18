from carrot.amqp import RabbitPublisher
from carrot.settings import carrot_settings

publisher = RabbitPublisher(
	host=carrot_settings['host'],
	port=carrot_settings['port'],
	user=carrot_settings['user'],
	password=carrot_settings['password'],
	exchange=carrot_settings['exchange'],
)

# The publisher is a long lived connection w/ connection error handling
publisher.connect()


def close_all():
	publisher.close()
