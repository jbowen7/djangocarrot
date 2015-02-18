# Carrot -- An alternative to Celery for Django

##Why this was made:
  1. Decouple task code from task manager code  
  2. Independent recording of task (name, app, status, dates, args, completed) in database  
  3. Simplicity for easy adaptation.  
  4. lighter than celery  
  5. nutritional benefits  
  
##Requirements:
  1. rabbitmq-server (default on localhost)  
  2. jsonfield  
  3. django1.7 (may run on earlier without the AppConfig code, not sure...)  
  
##Basic Usage:
  1. Define your workers  
  2. Start WorkerManager with the init script or another method: WorkerManager().start()  
  3. In your app "myapp" create a file called tasks.py  
  4. define a function called 'photo_upload' and add arbitrary code  
  5. In your app.views import QueuedTask and create it somewhere  
      `QueuedTask.object.create(name='picture_upload', app='myapp', user_id=request.user.id, data={file_id: 1})  `
  6. add or edit your workers in workers.py to add workers, or tasks that workers should execute  

##Example:
####workers.py -- edit workers (leave everything else)
```
WORKERS = {  
    'foo_processor': {  
       'app': 'foo',  
        'callback': process_task,  
        'tasks': ['say_hi_to_friend', 'sleep'],  
        'threads': 1  
    },  
    'foo_processor_important': {  
        'app':'foo',  
        'callback': process_task,  
        'tasks': ['call_mom'],  
        'threads': 2  
     }  
}  
```
####project/settings.py

`INSTALLED_APPS = ['carrot']`

#### migrate the model
```
manage.py makemigrations
manage.py migrate
```
####foo/tasks.py
```
def say_hi_to_friend(friend='Dog'):
  print 'Hi %s' % (friend,)

def sleep(seconds=86400):
  time.sleep(seconds)

def call_mom():
  try:
    mom()
  except NameError:
    raise
```
####manage.py shell
```
from carrot.utils import WorkerManager
WorkerManager().start()
```
####another manage.py shell
```
from carrot.models import QueuedTask
QueuedTask.objects.create(name='say_hi_to_friend', app='foo', data={'friend': 'daniel'})
QueuedTask.objects.create(name='call_mom', app='foo', data={})
```
 

##Notes:
This is simple app and it was created for my use case so it's not all inclusive of awesome features.  
It uses a convention over configuration approach to programming where when you create your QueuedTask  
the name= should be the name of the function found in myapp.tasks, app= name of your app (myapp), data= dictionary that gets passed to your callback function  
If you stick to the convention the default process_task callback should work for your workers.  
