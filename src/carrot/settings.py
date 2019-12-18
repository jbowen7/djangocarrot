from django.conf import settings
from collections.abc import Iterable

# At the time of writing, the queue name was limited to 255 bytes of UTF-8 chars.
# https://www.rabbitmq.com/queues.html
MAX_BYTES_QUEUE_NAME = 255

DEFAULTS = {
	'host': '127.0.0.1',
	'port': '5672',
	'user': 'guest',
	'pass': 'guest',
	'exchange': 'carrot.direct',
	'queues': ['carrot.default'],
	'durable_queues': True,
	'durable_exchanges': True,
	'durable_messages': False,
}

carrot_settings = getattr(settings, 'CARROT', {})
assert isinstance(carrot_settings, dict), f'wrong type ({type(carrot_settings)}) for CARROT settings'
for k, v in DEFAULTS.items():
	carrot_settings.setdefault(k, v)

assert isinstance(carrot_settings['host'], str)
assert isinstance(carrot_settings['port'], (int, str))
assert isinstance(carrot_settings['user'], str)
assert isinstance(carrot_settings['user'], str)
assert isinstance(carrot_settings['pass'], str)
assert isinstance(carrot_settings['exchange'], str)
assert isinstance(carrot_settings['queues'], Iterable)

for queue_name in carrot_settings['queues']:
	assert isinstance(queue_name, str), f'({queue_name} is not a valid queue name'
	assert queue_name, 'queue name must not be empty string'
	assert len(queue_name.encode('utf-8')) <= MAX_BYTES_QUEUE_NAME, f"Queue names may be up to {MAX_BYTES_QUEUE_NAME} bytes of UTF-8 characters"
