import sys

from django.core.management.base import BaseCommand, CommandError
import notification.models as n
from articleflow.models import Article

from django.contrib.auth.models import User

def main(*args, **options):
    help_msg = """Send a test notification to a specified user.\nUsage: python manage.py test_notification <username>"""
    if len(args) == 1:
        username = args[0]
    else:
        username = 'jlabarba'
        print "Using default recipient, %s" % username
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        sys.exit("User, %s, does not exist" % username)

    print "Sending test notification to %s ..." % username
    a = Article.objects.get(doi='pone.0012345')
    n.send_now([u], 'new_urgent_web_correction', {"article": a})
    
class Command(BaseCommand):
    args = "<username>"
    help = "Send a test notification to a specified user"
    #option_list = BaseCommand.option_list + (

    def handle(self, *args, **options):
        main(*args, **options)
