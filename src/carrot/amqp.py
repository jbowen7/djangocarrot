import time
import logging
import signal

import pika

LOGGER = logging.getLogger(__name__)


class RabbitConnection:
	DEFAULT_EXCHANGE = ''
	DEFAULT_QUEUE = ''
	DEFAULT_ROUTING_KEY = ''
	DEFAULT_USER = 'guest'
	DEFAULT_PASSWORD = 'guest'
	DEFAULT_HOST = 'localhost'
	DEFAULT_PORT = '5672'
	DEFAULT_HEARTBEAT = 600
	DEFAULT_BLOCKED_CONNECTION_TIMEOUT = 300
	DEFAULT_MESSAGE_ENCODING = 'utf-8'
	DEFAULT_EXCHANGE_TYPE = 'direct'

	def __init__(
			self,
			user=DEFAULT_USER,
			password=DEFAULT_PASSWORD,
			host=DEFAULT_HOST,
			port=DEFAULT_PORT,
			queue=DEFAULT_QUEUE,
			exchange=DEFAULT_EXCHANGE,
			routing_key=DEFAULT_ROUTING_KEY,
			heartbeat=DEFAULT_HEARTBEAT,
			blocked_connection_timeout=DEFAULT_BLOCKED_CONNECTION_TIMEOUT,
			encoding=DEFAULT_MESSAGE_ENCODING,
	):
		# These must be able to cast as ints
		heartbeat = int(heartbeat)
		blocked_connection_timeout = int(blocked_connection_timeout)

		# The encoding for a message to use if no other is selected
		self.message_encoding = encoding

		# These aren't necessary during construction, but are useful for instance methods
		# If they aren't set here, those methods will expect their values passed in.
		self.queue = queue
		self.exchange = exchange
		self.routing_key = routing_key

		self._credentials = pika.PlainCredentials(username=user, password=password)
		self._parameters = pika.ConnectionParameters(**{
			'credentials': self._credentials,
			'host': host,
			'port': port,
			'heartbeat': heartbeat,
			'blocked_connection_timeout': blocked_connection_timeout,
		})

		self._connection = None
		self._channel = None

	def __enter__(self):
		self.connect()
		return self

	def __exit__(self, *args, **kwargs):
		self.close()

	@property
	def is_open(self):
		"""
		Test if channel is usable
		"""
		return self._channel is not None and self._channel.is_open

	def connect(self, parameters=None):
		"""
		Makes a connection to RabbitMQ server, and setups the the exchange and queue
		if it hasn't already been done.

		:param parameters: Optionally pass in ConnectionParameters if you want to override the defaults
		"""
		assert parameters is None or isinstance(parameters, pika.ConnectionParameters)
		parameters = parameters or self._parameters

		self._connection = pika.BlockingConnection(parameters)
		self._channel = self._connection.channel()

	def close(self):
		"""
		Close the RabbitMQ connection
		"""
		if self._connection is None:
			return

		try:
			if self._connection.is_open:
				self._connection.close()
		except (pika.exceptions.AMQPChannelError, pika.exceptions.AMQPConnectionError) as e:
			LOGGER.warning(f'Caught error while trying to close connection: {str(e)}')
			pass
		finally:
			self._connection = None
			self._channel = None

	def setup_queue_exchange(self, exchange=None, queue=None, routing_key=None, durable_queue=False, durable_exchange=False, exchange_type=DEFAULT_EXCHANGE_TYPE):
		"""
		Initialize the exchange and queue
		"""
		if not self.is_open:
			self.connect()

		exchange = exchange or self.exchange
		queue = queue or self.queue
		routing_key = routing_key or self.routing_key

		assert exchange, "You must provide a name for the exchange"
		assert queue, "You must provide a name for the queue"

		self._channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=durable_exchange)
		self._channel.queue_declare(queue, durable=durable_queue)
		self._channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)


class RabbitPublisher(RabbitConnection):
	"""
	A generic RabbitMQ publisher which can publish to any exchange

	Example:
	publisher = RabbitPublisher(exchange='task_queue')
	publisher.publish('loral igloo dolar')
	"""

	def publish(self, message, exchange=None, routing_key=None, encoding=None):
		"""
		Publish a message to rabbitmq. This is the main purpose of this class and it's main method
		If an attempt to publish fails because of a connection error, this will make one attempt
		to reconnect (which might be necessary due to a heartbeat timeout)

		:param str message: the body of the message to send
		"""
		assert isinstance(message, (str, bytes)), "The message must be a str or bytes object"
		if not self.is_open:
			self.connect()

		# This allows method kwarg overrides of self attrs (potentially publishing to another exchange)
		exchange = exchange or self.exchange
		routing_key = routing_key or self.routing_key

		# Exchange name is required, routing_key can be empty str
		assert exchange, "You must provide a name for the exchange"

		encoding = encoding or self.message_encoding
		properties = pika.BasicProperties(content_encoding=encoding)
		try:
			self._channel.basic_publish(exchange, routing_key, message, properties=properties)
		except pika.exceptions.AMQPConnectionError:
			LOGGER.warning(f'Connection was closed while publishing. Reconnecting...')
			self.connect()
			self._channel.basic_publish(exchange, routing_key, message, properties=properties)


class RabbitConsumer(RabbitConnection):
	"""
	A generic RabbitMQ consumer which gracefully handles SIGINTS and SIGTERMS

	Example:
	def print_article(x):
		print(x)
	consumer = RabbitConsumer(queue='newspaper', callback=print_article)
	consumer.run()
	...
	"""
	DEFAULT_RECONNECT_WAIT = 5
	DEFAULT_PREFETCH_COUNT = 2

	def __init__(self, callback=None, queue=None, prefetch_count=DEFAULT_PREFETCH_COUNT, *args, **kwargs):
		"""
		:param callback: callable function with w/ a single argument (the message body of a consumed message)
		:param queue: name of the queue to consume messages from
		:param prefetch_count: quantity of non-acked messages that can be obtained at any time
		"""
		super().__init__(*args, **kwargs)

		self.queue = queue or self.queue
		self.callback = callback

		self._prefetch_count = prefetch_count
		self._shutdown_flag = False

	def run(self, reconnect_wait=DEFAULT_RECONNECT_WAIT):
		if self.callback is None or callable(self.callback) is False:
			raise RuntimeError("A callback function must be set before running the consumer")

		# Signals to stop running (SIGINT, SIGTERM)
		LOGGER.info("Registering Signal handlers for: SIGINT, SIGTERM")
		signal.signal(signal.SIGTERM, self._sigterm)
		signal.signal(signal.SIGINT, self._sigterm)

		LOGGER.info("Starting consuming")
		self._shutdown_flag = False
		while self._shutdown_flag is False:
			try:
				self.connect()
				self._channel.basic_qos(prefetch_count=self._prefetch_count)

				self._channel.basic_consume(self.queue, self._on_message)
				self._channel.start_consuming()
				self._connection.close()

			except pika.exceptions.AMQPConnectionError as e:
				if not self._shutdown_flag:
					LOGGER.warning(f'Connection was closed. Reconnecting... ({e})')
					time.sleep(reconnect_wait)
				continue

			except pika.exceptions.ConnectionClosedByBroker:
				if not self._shutdown_flag:
					LOGGER.warning("Connection closed by broker. Will attempt reconnect shortly..")
					time.sleep(reconnect_wait)
				continue

			except pika.exceptions.AMQPChannelError:
				LOGGER.exception("Caught channel error. Stopping...")
				break

	def stop(self):
		self._shutdown_flag = True
		self._channel.stop_consuming()

	def _on_message(self, channel, method_frame, header_frame, body):
		"""
		WARNING: This normally shouldn't be overridden.
		The purpose of the consumer is to: retrieve messages, deliver them to a callback, and acknowledge message delivery.
		It is not the responsiblity of the consumer to ensure that the execution of the callable exited sucessfully.
		Therefore, this method serves as a callback wrapper to ensure that the consumer never dies, and that message delivery
		is always acknowledged. You have been warned.
		"""
		if not self._shutdown_flag:
			try:
				if self.message_encoding is not None:
					body = body.decode(self.message_encoding)
				self.callback(body)
			except:  # noqa
				LOGGER.exception("RabbitConsumer does not die, but the callable it delivers messages to raised an exception")
			channel.basic_ack(delivery_tag=method_frame.delivery_tag)

	def _sigterm(self, signum, frame):
		"""
		Gracefully handle SIGTERM and SIGINT
		"""
		LOGGER.info('Caught Sigterm. Shutting down gracefully')
		self.stop()
