from collections.abc import Iterable
from collections import namedtuple

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# At the time of writing, the queue name was limited to 255 bytes of UTF-8 chars.
# https://www.rabbitmq.com/queues.html
MAX_BYTES_QUEUE_NAME = 255

DEFAULT_QUEUE = ('default', 'carrot.default', 1)

DEFAULTS = {
	'host': '127.0.0.1',
	'port': '5672',
	'user': 'guest',
	'password': 'guest',
	'exchange': 'carrot.direct',
	'queues': [DEFAULT_QUEUE],
	'durable_queues': True,
	'durable_exchange': True,
	'durable_messages': False,
}

# Structure for queue data
Queue = namedtuple('Queue', ['id', 'name', 'concurrency'])

carrot_settings = getattr(settings, 'CARROT', {})
assert isinstance(carrot_settings, dict), f'wrong type ({type(carrot_settings)}) for CARROT settings'
for k, v in DEFAULTS.items():
	carrot_settings.setdefault(k, v)

assert isinstance(carrot_settings['host'], str)
assert isinstance(carrot_settings['port'], (int, str))
assert isinstance(carrot_settings['user'], str)
assert isinstance(carrot_settings['user'], str)
assert isinstance(carrot_settings['password'], str)
assert isinstance(carrot_settings['exchange'], str)
assert isinstance(carrot_settings['queues'], Iterable)


# Queues shall have an `id` used internally by the app to identify which queue to use
# and shall have a `name` which is used by RabbitMQ as the queue name and routing_key
queues = []
for i in carrot_settings['queues']:
	try:
		q = Queue(*i)
	except TypeError:
		raise ImproperlyConfigured("Queues must be a tuple e.g.: ('my_queue', 'carrot.my_queue', 2)")

	assert isinstance(q.id, str), f'({q.id} is not a valid queue id'
	assert isinstance(q.name, str), f'({q.name} is not a valid queue name'
	assert isinstance(q.concurrency, int), f'({q.concurrency} is not a valid integer'
	assert q.id, 'queue id must not be empty string'
	assert q.name, 'queue name must not be empty string'
	assert q.concurrency, 'queue name must not be empty string'
	assert len(q.name.encode('utf-8')) <= MAX_BYTES_QUEUE_NAME, f"Queue names may be up to {MAX_BYTES_QUEUE_NAME} bytes of UTF-8 characters"

	queues.append(q)

carrot_settings['queues'] = queues
carrot_settings['queue_map'] = {q.id: q for q in queues}
