Mongrel 2 WSGI Handler
----------------------

Forked from Berry's original WSGI handler work. Much thanks! (http://github.com/berry/).

Installation
============

python setup.py install :)

Django Instructions
===================

Add 'mongrel2_wsgi' to your INSTALLED_APPS and then you can run "python manage.py m2wsgi" and you're done. Currently hardcoded to push: tcp://127.0.0.1:9997 and pull: tcp://127.0.0.1:9996

Other WSGI Applications
=======================

from mongrel2 import handler
from mongrel2_wsgi import wsgi_server
wsgi_server(my_application_object, handler.Connection(uuid, push_url, pull_url))