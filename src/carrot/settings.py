from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# At the time of writing, the queue name was limited to 255 bytes of UTF-8 chars.
# https://www.rabbitmq.com/queues.html
MAX_BYTES_QUEUE_NAME = 255
DEFAULT_QUEUE_NAME = 'default'

DEFAULTS = {
	'host': '127.0.0.1',
	'port': '5672',
	'user': 'guest',
	'password': 'guest',
	'exchange': 'carrot.direct',
	'queue_prefix': 'carrot',
	'worker_concurrency': 1,
	'durable_queue': True,
	'durable_exchange': True,
	'durable_messages': False,
	'include_default_queue': True,
	'queues': {},
}

# Merge defaults with APP settings
carrot_settings = getattr(settings, 'CARROT', {})
assert isinstance(carrot_settings, dict), f'wrong type ({type(carrot_settings)}) for CARROT settings'
for k, v in DEFAULTS.items():
	carrot_settings.setdefault(k, v)

# Default queue
if carrot_settings['include_default_queue'] is True:
	carrot_settings['queues'].setdefault(DEFAULT_QUEUE_NAME, {})

# Setup and verify queues and their options
for queue, queue_settings in carrot_settings['queues'].items():
	assert isinstance(queue, str)
	assert isinstance(queue_settings, dict)

	# Set some defaults before validating
	queue_settings.setdefault('queue_name', f"{carrot_settings['queue_prefix']}.{queue}")
	queue_settings.setdefault('worker_concurrency', carrot_settings['worker_concurrency'])
	queue_settings.setdefault('durable_queue', carrot_settings['durable_queue'])

	# Validations
	queue_settings['worker_concurrency'] = int(queue_settings['worker_concurrency'])
	if not len(queue_settings['queue_name'].encode('utf-8')) <= MAX_BYTES_QUEUE_NAME:
		raise ImproperlyConfigured(f"Queue names may be up to {MAX_BYTES_QUEUE_NAME} bytes of UTF-8 characters")

assert isinstance(carrot_settings['host'], str)
assert isinstance(carrot_settings['port'], (int, str))
assert isinstance(carrot_settings['user'], str)
assert isinstance(carrot_settings['user'], str)
assert isinstance(carrot_settings['password'], str)
assert isinstance(carrot_settings['exchange'], str)
assert isinstance(carrot_settings['queue_prefix'], str)
assert isinstance(carrot_settings['worker_concurrency'], int)
assert isinstance(carrot_settings['durable_queue'], bool)
assert isinstance(carrot_settings['durable_exchange'], bool)
assert isinstance(carrot_settings['durable_messages'], bool)
assert isinstance(carrot_settings['include_default_queue'], bool)
assert isinstance(carrot_settings['queues'], dict)
