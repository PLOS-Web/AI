import sys
import os
from subprocess import call

from django.core.management.base import BaseCommand, CommandError

from ai import settings
from ai import ambra_settings
from articleflow.models import Article, ArticleState, State

import logging
logger = logging.getLogger("commands")

def get_ingestible_articles():
    return Article.objects.filter(current_state__unique_name="pulled").all()  #RIGHT name?

def ingest_articles(arts):
    ingest = os.path.abspath('/var/local/scripts/production/mechIngest')
    ingestion_queue = os.path.abspath('/var/spool/ambra/ingestion-queue/')
    for a in arts:
        logger.info("Attempting to ingest %s..." % a.doi)
        call([ingest, "-s", "%s.zip" % a.doi], cwd=ingestion_queue)

def main():
    arts = get_ingestible_articles()
    logger.info("Found %s ingestible articles." % len(arts))
    ingest_articles(arts)

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args)
