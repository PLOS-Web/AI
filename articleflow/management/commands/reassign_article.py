import sys
import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from ai import settings

from articleflow.models import Article

def main(*args, **options):
    usage_msg = "usage: reassign_article [DOI] [USERNAME]\nex: reassign_article pone.0012345 jlabarba"
    if len(args) not in [1, 2]:
        sys.exit(usage_msg)
    try:
        a = Article.objects.get(doi=args[0])
    except Article.DoesNotExist, e:
        sys.exit("I can't find an article with doi, %s" % args[0])
    if len(args) == 2:
        try:
            u = User.objects.get(username=args[1])
        except User.DoesNotExist, e:
            sys.exit("I can't find a user with username, %s" % args[1])

            c_s = a.current_articlestate
            c_s.assignee = u
            c_s.save()
    # Wipe assignment
    else:
        c_s = a.current_articlestate
        c_s.assignee = None
        c_s.save()     

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
