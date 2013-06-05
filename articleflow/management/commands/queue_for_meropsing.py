import sys
import os

from django.core.management.base import BaseCommand, CommandError

from ai import settings

from articleflow.daemons.merops_tasks import process_doc_from_aries
from articleflow.models import Article

def main(*args, **options):
    usage_msg = "usage: queue_for_meropsing doi|guid <doi>|<guid>\nex: queue_for_meropsing doi pone.0012345"
    if len(args) != 2:
        sys.exit(usage_msg)
    if args[0] == 'doi':
        try:
            a = Article.objects.get(doi=args[1])
        except Article.DoesNotExist, e:
            sys.exit("I can't find an article with doi, %s" % args[1])
        guid = a.si_guid
    elif args[0] == 'guid':
        guid = args[0]
    else:
        sys.exit(usage_msg)

    aries_zip = os.path.join(settings.MEROPS_ARIES_DELIVERY, guid + ".zip")
    #print aries_zip
    process_doc_from_aries(aries_zip)

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
