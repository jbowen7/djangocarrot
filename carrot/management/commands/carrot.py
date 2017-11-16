from django.db import connection
from django.core.management.base import BaseCommand

import os
import sys
import signal

from carrot.utils import WorkerService
from carrot.models import Worker

from multiprocessing import Process


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument("--pid", '-p', dest="pidfile", default="/var/run/carrot.pid")
		parser.add_argument("--log", '-l', dest="logfile", default="/var/log/carrot.log")


	def handle(self, *args, **options):
		# Get cmd line args
		pidfile = options['pidfile']
		logfile = options['logfile']
		verbosity = options['verbosity']

		# Daemonzie first then handle stuff
		self.daemonize(pidfile, logfile)
		connection.close()

		signal.signal(signal.SIGTERM, self.signal_term_handler)
		self.processes = []

		print('Carrot Starting...')
		for worker in Worker.objects.filter(enabled=True):
			w = WorkerService(worker)
			p = Process(target=w.start)
			p.start()
			self.processes.append(p)
			print('Started worker (%s) PID: %s' % (worker.name, p.pid))

	def signal_term_handler(self, signal, frame):
		print('Carrot Shutting down..')
		for p in self.processes:
			print('killing worker (%s)' % p.pid)
			p.terminate()


	def daemonize(self, pidfile, logfile, *args, **options):
		#First we daemonize ourselves.
		stdin='/dev/null'
		stdout=logfile
		stderr=logfile  #'/dev/null'
		# Perform first fork.
		try:
			pid = os.fork()
			if pid > 0:
				sys.exit(0) # Exit first parent.
		except OSError as e:
			sys.stderr.write("fork #1 failed: (%d) %sn" % (e.errno, e.strerror))
			sys.exit(1)
		# Decouple from parent environment.
		os.chdir("/")
		os.umask(0)
		os.setsid()
		# Perform second fork.
		try:
			pid = os.fork()
			if pid > 0:
				sys.exit(0) # Exit second parent.
		except OSError as e:
			sys.stderr.write("fork #2 failed: (%d) %sn" % (e.errno, e.strerror))
			sys.exit(1)

		# The process is now daemonized, redirect standard file descriptors.
		for f in sys.stdout, sys.stderr: f.flush()
		si = open(stdin, 'r')
		so = open(stdout, 'a+')
		se = open(stderr, 'a+')
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())

		pid = str(os.getpid())
		pidfile = open(pidfile, 'w')
		pidfile.write("%s\n" % pid)
		pidfile.close()
