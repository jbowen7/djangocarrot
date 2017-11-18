# Carrot -- A simple task queue for Django

## Why this was made:
  1. It's very easy to use.
  2. It decouples the task code from the task manager code.
  
## Quick Setup:
  1. Install rabbitmq-server (default on localhost)  
  ```
  yum install rabbitmq-server
  service rabbitmq-server start
  ```

  2. Install carrot
  ```
  pip install djangocarrot
  manage.py makemigrations carrot
  manage.py migrate carrot
  ```

  3. Add carrot to installed apps (settings.py)
  `INSTALLED_APPS = ['carrot']`

  
## Basic Usage:
```python
from carrot.models import Task  

Task.objects.create(kallable="myapp.mymodule.mykallable")
```

Task arguments:
* kallable (required): location to callable, e.g. animals.Dog.bark
* args (optional): list of positional arguments to pass to the callable 
* kwargs (optional): map of key/value pairs to pass to the callable
* worker (optional): request a specific worker to execute task

## Consume tasks
The tasks need to be consumed. This can easily be accomplished with the WorkerService
```python
from carrot.utils import WorkerService
WorkerService().start()
```
The worker service can also be daemonized with a management command
`manage.py carrot-workers`


## Workers (Advanced Usage)
A default worker is already available to use for tasks and this step is not necessary. However, new workers may be created to handle specific
tasks. For example, let's say you need a worker which only processes one task at a time so as not to overwhelm 
some system resource.
```python
from carrot.models import Worker, Task

worker = Worker(name='fileprocesser')
worker.description = 'Used for processing large files one at a time'
worker.concurrency = 1
worker.save()

Task.objects.create(kallable='example.processFile', args=['/tmp/huge1.wav'], kwargs={'bitrate': 1411}, worker=worker)
Task.objects.create(kallable='example.processFile', args=['/tmp/huge2.wav'], kwargs={'bitrate': 1411}, worker=worker)
Task.objects.create(kallable='example.processFile', args=['/tmp/huge3.wav'], kwargs={'bitrate': 1411}, worker=worker)

```

Worker arguments:
* name (required): an arbitrary name to identify the worker
* description (optional): a description of worker and it's duties
* concurrency (optional) (default -> 4): how many tasks this worker can process concurrently
* enabled (optional) (default: True): whether or not this worker should be processing tasks



