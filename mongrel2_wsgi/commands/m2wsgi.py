from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from mongrel2_wsgi import server

class Command(BaseCommand):
    help = "Runs a Django WSGI server."

    def handle(self, *args, **options):
        django_application = WSGIHandler()
        server.wsgi_server(django_application)