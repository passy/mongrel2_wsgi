from optparse import make_option
from uuid import uuid4
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler

from mongrel2_wsgi import server
from mongrel2 import handler

class Command(BaseCommand):
    help = "Runs a Django WSGI server."

    def handle(self, *args, **options):
        #self.stdout.write("Starting 0MQ server.")
        print "Starting 0MQ server."
        conn = handler.Connection(
            str(uuid4()), 
            "tcp://127.0.0.1:9997",  # TODO: Take these as command line args.
            "tcp://127.0.0.1:9996")
        
        django_application = WSGIHandler()
        server.wsgi_server(django_application, conn)