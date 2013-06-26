import sys

from django.core.management.base import BaseCommand, CommandError

from ai import settings
from articleflow.management.commands.requeue import requeue_merops, requeue_finishxml
from articleflow.models import Article

import logging
logger = logging.getLogger("commands")

def brequeue(articles, queue_func):
    if not articles:
        logger.info("Found no articles that are queued.  Exiting.")
        return 0
    logger.info("Identified %s article(s) that are queued.  Requeueing ..." % len(articles))
    for a in articles:
        try:
            logger.info("Requeueing %s" % a.doi)
            queue_func(a.doi)
        except OSError, ee:
            logger.exception(ee)
    return 0
            
def main(*args, **options):
    usage_msg = "usage: brequeue [merops|finishxml|both]"
    if len(args) != 1:
        print(usage_msg)
        sys.exit(1)
    if args[0] == 'merops':
        articles = Article.objects.filter(current_state__unique_name="queued_for_meropsing").all()
        brequeue(articles, requeue_merops)
    if args[0] == 'finishxml':
        articles = Article.objects.filter(current_state__unique_name="queued_for_finish").all()
        brequeue(articles, requeue_finishxml)
    if args[0] == 'both':
        articles = Article.objects.filter(current_state__unique_name="queued_for_meropsing").all()
        brequeue(articles, requeue_merops)
        articles = Article.objects.filter(current_state__unique_name="queued_for_finish").all()
        brequeue(articles, requeue_finishxml)
    else:
        print(usage_msg)
        sys.exit(1)

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
