from django.core.management.base import BaseCommand, CommandError
import notification.models as n
from articleflow.models import Article

from django.contrib.auth.models import User

def main(*args, **options):
    u = User.objects.get(username='jlabarba')
    a = Article.objects.get(doi='pone.0012345')
    n.send_now([u], 'new_urgent_web_correction', {"article": a})
    
class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
