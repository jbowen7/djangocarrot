import importlib
from django.utils import timezone

from carrot.models import QueuedTask 
import settings

"""
Define your workers and callbacks here. Workers are expeced to have an app, (list)tasks and threads 
See the examples below
This app, as is, will work out of the box if you stick to certain conventions
	1) app: should be the name of an app in which tasks.py can be found
	2) tasks: should be the name of the function found in the app (exchange) tasks.py file
By sticking to these conventions the process_task callback can be used for any task.
"""

## Define Worker callbacks
def process_task(task_id):
	task = QueuedTask.objects.get(id=task_id)
	task.status = 'processing'
	task.save()

	# Get the strings to find the function
	app_name = task.app
	function_name = task.name
	module = importlib.import_module("%s.%s" % (app_name, settings.DEFAULT_TASK_MODULE))

	# Reload the module incase there were changes to the function after workers started
	if not module:
		print 'Module is not found: %s' % module
	else:
		reload(module)
	function_to_call = getattr(module, function_name)
	if not callable(function_to_call):
		print 'Function is not callable: %s' % function_to_call
		task.status = 'error'
	else:
		data = task.data
		try:
			print 'Processing task: %s -- app: %s' % (task.name, task.app)
			retval = function_to_call(**data)
			if isinstance(retval, bool):
				task.status = "retval: %s" % (retval,)
			else:
				task.status = 'done'
			task.completed = True
			task.date_completed = timezone.now()
		except Exception as e:
			print 'Error caught: %s' % str(e)
			task.status = 'Error: %s' % str(e)
	
	task.save()
	return	



## Define workers here 
## As a convention routing keys will be the names of the methods they call
WORKERS = {
	'file_processor': {
		'app': 'filemanager',
		'callback': process_task, 
		'tasks': ['photo_upload', 'song_upload', 'deactivate_file'],
		'threads': 2
	},
	'account_manager': {
		'app':'accounts',
		'callback': process_task, 
		'tasks': ['deactivate_account'],
		'threads': 2
		
	}
}


