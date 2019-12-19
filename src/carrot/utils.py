import importlib


def import_callable(path):
	"""
	:param path: the dot-notated absolute path to a callable
	:returns: callable, e.g. function, class
	"""
	assert isinstance(path, str)
	split_path = path.split('.')
	module_path = ".".join(split_path[:-1])
	callable_name = split_path[-1]
	module = importlib.import_module(module_path)
	return getattr(module, callable_name)
