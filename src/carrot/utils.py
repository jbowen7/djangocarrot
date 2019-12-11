from carrot.models import Worker, Task
from django.utils import timezone
from django.db import connection as dbconnection
from multiprocessing import Process, active_children

import pika

import time
import traceback
import os
import signal
import sys


class WorkerService(object):
	def __init__(self, worker):
		assert isinstance(worker, Worker)
		self.worker = worker
		self.exchange = worker.exchange
		self.queue = worker.queue
		self.routing_key = worker.routing_key

	def start(self):
		# Register a Signal Terminate Handler so this can die gracefully when running as a daemon
		signal.signal(signal.SIGTERM, self.__sigterm_handler)

		self.rabbit = RabbitHelper()
		self.rabbit.create_exchange(self.exchange)
		self.rabbit.create_queue(self.queue)
		self.rabbit.bind_queue(self.exchange, self.queue, self.routing_key)
		try:
			self.rabbit.start_consuming(self.queue, self.__message_callback)
		except KeyboardInterrupt:
			self.stop()

	def stop(self):
		self.rabbit.close()
		active_children()  # joins Processes
		dbconnection.close()  # prevents internactive shell from Mysql has gone away error
		sys.exit(0)
		return

	def __sigterm_handler(self, signal, frame):
		print('Worker(%s) Caught SIGTERM. Shutting down' % self.worker.name)
		return self.stop()

	def __message_callback(self, ch, method, properties, body):
		# Max concurrency for a worker is defined by worker.concurrency
		while len(active_children()) >= self.worker.concurrency:
			print('Worker(%s) at max concurrency: %s' % (self.worker.name, self.worker.concurrency))
			time.sleep(1)

		# process task
		task_id = int(body)
		print('Starting work for task: %s ' % task_id)
		Process(target=self.process_task, args=(task_id,)).start()

		# Acknowledge the message
		ch.basic_ack(delivery_tag=method.delivery_tag)

	def process_task(self, task_id):
		try:
			# Close db connection after fork else bad things happen
			dbconnection.close()

			# Get task
			print('Process %s: started for Task: %s' % (os.getpid(), task_id))
			task = Task.objects.get(id=task_id)
			task.status = 'processing'
			task.date_processed = timezone.now()
			task.save()

			# Run
			retval = task.execute()
			task.status = retval

		except KeyboardInterrupt:
			print("Caught Keyboard Interrupt: Quiting gracefully...")
			task.status = "KeyboardInterrupt"
		except Task.DoesNotExist:
			print("Task does not exist for id: %s, nothing to do")
			task = None
		except Exception as e:
			print('Error caught: %s' % str(e))
			print(traceback.format_exc())
			task.status = 'Error: %s' % str(e)
		finally:
			print('Process %s finished for Task: %s ' % (os.getpid(), task_id))
			if task:
				task.date_completed = timezone.now()
				task.completed = True
				task.save()


class RabbitHelper(object):
	def send_message(self, exchange, routing_key, message):
		self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)

	def start_consuming(self, queue_name, callback, no_ack=False):
		self.channel.basic_consume(callback, queue=queue_name, no_ack=no_ack)
		self.channel.start_consuming()

	def create_exchange(self, exchange, type='direct', durable=True):
		self.channel.exchange_declare(exchange=exchange, type=type, durable=durable)

	def create_queue(self, queue_name, durable=True):
		self.channel.queue_declare(queue=queue_name, durable=durable)

	def bind_queue(self, exchange, queue_name, routing_key):
		self.channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

	def close(self):
		self.connection.close()

	def __init__(self, host='localhost'):
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
		self.channel = self.connection.channel()


def test(seconds):
	print('this is a carrot task test')
	print('sleeping for %s seconds' % seconds)
	time.sleep(seconds)
	print('finished sleeping')
