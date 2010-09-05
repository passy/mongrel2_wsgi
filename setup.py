#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='Mongrel2 WSGI',
      version='1.0',
      description='Mongrel2 (0MQ) server that runs WSGI applications.',
      maintainer='Timothy Fitz',
      maintainer_email='TimothyFitz@gmail.com',
      url='http://github.com/timothyfitz/mongrel2_wsgi',
      packages=['mongrel2_wsgi'],
     )