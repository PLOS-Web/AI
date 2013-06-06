import sys
import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from ai import settings

from articleflow.models import Article, ArticleState, State

def main(*args, **options):
    usage_msg = "usage: set_article_state [DOI] [STATE unique_name]\nex: set_article_state pone.0012345 finish_out"
    if len(args) != 2:
        sys.exit(usage_msg)
    try:
        a = Article.objects.get(doi=args[0])
    except Article.DoesNotExist, e:
        sys.exit("I can't find an article with doi, %s" % args[0])
    try:
        s = State.objects.get(unique_name=args[1])
    except User.DoesNotExist, e:
        sys.exit("I can't find a state with that unique_name, %s" % args[1])

    c_s = ArticleState(article=a, state=s)
    c_s.save()

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
