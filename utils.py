import pika
from multiprocessing import Process
import workers
import time
from django.db import connection as dbconnection

class WorkerManager(object):

	def start(self):
		self.rabbit.create_exchange(self.exchange)
		self.rabbit.create_queue(self.queue)
		self.rabbit.bind_queue(self.exchange, self.queue, self.routing_key)
		self.rabbit.start_consuming(self.queue, self.__start_worker)

	def __start_worker(self, ch, method, properties, body):
		body = eval(body)
		app = body['app']
		task_name = body['task_name']
		task_id = body['task_id']
		worker = self.__get_worker(app, task_name)
		if self.__worker_has_available_thread(worker):
			print 'Starting worker: %s for task: %s' % (worker, task_name)
			# For sanity, close dbconnection
			dbconnection.close()
			job = Process(target=self.workers[worker]['callback'], args=(task_id,))
			job.start()
			self.worker_running_threads[worker].append(job)
		else:
			print 'No threads available for worker: %s' % (worker,)
			Process(target=self.__requeue_task, args=(str(body),)).start()
		return

	def __get_worker(self, app, task_name):
		worker = None
		for worker_name, worker_settings in self.workers.iteritems():
			if worker_settings['app'] == app:
				if task_name in worker_settings['tasks']:
					worker = worker_name
					break
		return worker

	def __worker_has_available_thread(self, worker):
		jobs = self.worker_running_threads[worker]
		for job in jobs:
			if not job.is_alive():
				self.worker_running_threads[worker].remove(job)
		if len(self.worker_running_threads[worker]) < self.worker_max_threads[worker]:
			return True
		else:
			return False

	def __requeue_task(self, body):
		# Don't requeue right away it will just be immediately consumed
		time.sleep(10)
		self.rabbit.send_message(self.exchange, self.routing_key, body)
		return


	def __init__(self, worker_dict=workers.WORKERS, exchange='carrot', queue='worker-manager', routing_key='worker-manager'):
		self.rabbit = RabbitHelper()
		self.exchange = exchange
		self.queue = queue
		self.routing_key = routing_key
		self.workers = worker_dict
		self.worker_running_threads = {}
		self.worker_max_threads = {}
		self.jobs = {}
		for key, value in self.workers.iteritems():
			self.worker_running_threads[key] = []
			self.worker_max_threads[key] = value['threads']


class RabbitHelper(object):
	def send_message(self, exchange, routing_key, message):
		self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)

	def start_consuming(self, queue_name, callback, no_ack=True):
		self.channel.basic_consume(callback, queue=queue_name, no_ack=no_ack)
		self.channel.start_consuming()

	def create_exchange(self, exchange, type='direct', durable=True):
		self.channel.exchange_declare(exchange=exchange, type=type, durable=durable)

	def create_queue(self, queue_name, durable=True):
		self.channel.queue_declare(queue=queue_name, durable=durable)

	def bind_queue(self, exchange, queue_name, routing_key):
		self.channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

	def __init__(self, host='localhost'):
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
		self.channel = self.connection.channel()

	def __del__(self):
		self.connection.close()
