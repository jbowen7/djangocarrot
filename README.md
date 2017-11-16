# Carrot -- An alternative to Celery for Django

## Why this was made:
  1. It decouples task code from process that executes the task. 
  2. Independent recording of task (kallable, args, kwargs, worker, status, dates) in database  
  3. It's very easy to use.
  
## Setup:
  1. Install rabbitmq-server (default on localhost)  
  ```
  yum install rabbitmq-server
  service rabbitmq-server start
  ```

  2. Add carrot to installed apps
  # settings.py
  `INSTALLED_APPS = ['carrot']`

  3. Migrate models 
  ```
  manage.py makemigrations carrot
  manage.py migrate 
  ```
  
## Basic Usage:
```
from carrot.models import Task  

Task.objects.create(kallable="myapp.mymodule.mykallable")
```

Task arguments:
kallable (required): location to callable, e.g. animals.Dog.bark
args (optional): list of positional arguments to pass to the callable 
kwargs (optional): map of key/value pairs to pass to the callable
worker (optional): request a specific worker to execute task


## Workers
A default worker is already available to use for tasks, however if it is necessary to create new workers to handle specific
tasks. For example let's say you needed to have one worker which only processed one task at a time so as not to overwhelm 
some system resource.
```
from carrot.models import Worker, Task

worker = Worker(name='fileprocesser')
worker.description = 'Used for processing large files one at a time'
worker.concurrency = 1
worker.save()

Task.objects.create(kallable='example.processFile', args=['/tmp/huge1.wav'], kwargs={'bitrate': 1411})
Task.objects.create(kallable='example.processFile', args=['/tmp/huge2.wav'], kwargs={'bitrate': 1411})
Task.objects.create(kallable='example.processFile', args=['/tmp/huge3.wav'], kwargs={'bitrate': 1411})

```


## Consume tasks
The tasks need to be consumed. This can easily be accomplished with the WorkerService
```
from carrot.utils import WorkerService
WorkerService().start()
```

## Daemonize
A management command is included, which will daemonize the WorkerService process
`manage.py carrot-workers`

