from django.db import connection
from django.core.management.base import BaseCommand

import os
import sys

from carrot.utils import WorkerManager


class Command(BaseCommand):


    def handle(self, pidfile="/var/run/carrot-workers.pid", *args, **options):
        self.daemonize(pidfile)
        connection.close()
        WorkerManager().start()


    def daemonize(self, pidfile, *args, **options):
        logfile = '/var/log/django/carrot-workers.log'
        #First we daemonize ourselves.
        stdin='/dev/null'
        stdout=logfile
        stderr=logfile  #'/dev/null'
        # Perform first fork.
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0) # Exit first parent.
        except OSError, e:
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
        except OSError, e:
            sys.stderr.write("fork #2 failed: (%d) %sn" % (e.errno, e.strerror))
            sys.exit(1)
            
        # The process is now daemonized, redirect standard file descriptors.
        for f in sys.stdout, sys.stderr: f.flush()
        si = file(stdin, 'r')
        so = file(stdout, 'a+')
        se = file(stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # disable buffering on stdout
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'a+', 0)

        # write pidfile -if not specified defaults to /var/run/mainlaunch-pd.pid
        pid = str(os.getpid())
        pidfile = open(pidfile, 'w')
        pidfile.write("%s\n" % pid)
        pidfile.close()
