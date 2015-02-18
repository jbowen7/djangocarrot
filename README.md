# Carrot -- An alternative to Celery for Django

##Why this was made:
  1) Decouple task code from task manager code  
  2) Needed a record of the task, it's status, when it was created and completed, what args were used to call it, who called it, etc  
  3) Easier than getting celery to do what I wanted  
  
##Requirements:
  1) rabbitmq-server (default on localhost)  
  2) jsonfield  
  3) django1.7 (may run on earlier without the AppConfig code, not sure...)  
  
##Basic Usage:
  1) Define your workers 
  2) Start WorkerManager with the init script or another method: WorkerManager().start()
  3) In your app "myapp" create a file called tasks.py  
  4) define a function called 'photo_upload' and add arbitrary code  
  5) In your app.views import QueuedTask and create it somewhere
      QueuedTask.object.create(name='picture_upload', app='myapp', user_id=request.user.id, data={file_id: 1})  
  6) add or edit your workers in workers.py to add workers, or tasks that workers should execute  

##Advanced Usage:
  For now, refer to the source (TODO)  

##Notes:
This is simple app and it was created for my use case so it's not all inclusive of awesome features.  
It uses a convention over configuration approach to programming where when you create your QueuedTask  
the name= should be the name of the function found in myapp.tasks, app= name of your app (myapp), data= dictionary that gets passed to your callback function  
If you stick to the convention the default process_task callback should work for your workers.  
