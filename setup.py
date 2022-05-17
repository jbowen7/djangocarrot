#!/usr/bin/env python3

import os
from setuptools import setup, find_packages

BASE_DIR = os.path.dirname(__file__)
VERSION = '2.4.0'

setup(
  name = 'djangocarrot',
  version = VERSION,
  description = 'Carrot -- A simple task Queue for Django.',
  author = 'John Bowen',
  author_email = 'jbowen7@gmail.com',
  url = 'https://github.com/jbowen7/djangocarrot',
  keywords = ['django', 'task', 'queue'],
  install_requires = ['pika',],
  package_dir={'': 'src'},
  packages=find_packages(where='src', exclude=[]),
)
