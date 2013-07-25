from django.core.management.base import BaseCommand, CommandError
import notification.models as n

from django.contrib.auth.models import User

def main(*args, **options):
    u = User.objects.get(username='jlabarba')
    n.send([u], 'hello_world')
    
class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
