from setuptools import setup, find_packages
setup(
  name = 'djangocarrot',
  packages = find_packages(),
  version = '1.1.1',
  description = 'Carrot -- A simple task Queue for Django.',
  author = 'John Bowen',
  author_email = 'jbowen7@gmail.com',
  url = 'https://github.com/jbowen7/djangocarrot',
  keywords = ['django', 'task', 'queue'],
  classifiers = [],
  install_requires = ['pika',],
)
