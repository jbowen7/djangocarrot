from django.db import connection
from django.core.management.base import BaseCommand

import os
import sys
import signal

from carrot.utils import RabbitHelper
from carrot.models import Worker
from carrot.models import Task



class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument("--task-id", '-t', dest="task_id")


	def handle(self, *args, **options):
		task_id = options.get('task_id', None)
		if not task_id:
			print("Usage: manage.py requeue_task --task-id n")
			return
		if task_id.isdigit() is False:
			print("--task-id argument must be and integer")
			return

		task = Task.objects.filter(id=task_id).first()
		if not task:
			print("No task found with id of %s. Exiting..." % task_id)
			return
		if task.completed:
			print("Task is already completed. Exiting...")

		return RabbitHelper().send_message(task.exchange, task.routing_key, task_id)
