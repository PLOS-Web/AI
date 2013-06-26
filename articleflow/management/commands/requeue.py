import sys
import shutil
import glob
import os.path

from django.core.management.base import BaseCommand, CommandError
from articleflow.daemons.merops_tasks import process_doc_from_aries
from articleflow.models import Article

from ai import settings


def requeue(doi, source, dest):
    request_pathname = os.path.join(source, doi + "*")
    f = glob.glob(request_pathname)
    if len(f) != 1:
        if len(f) > 1:
            raise OSError("Too many candidate files found for %s: %s" % (doi, f))
        else:
            raise OSError("No file found matching %s" % request_pathname)

    shutil.copy(f[0], dest)

def requeue_merops(doi):
    try:
        return requeue(doi, settings.MEROPS_MEROPSED_WATCH_BU, settings.MEROPS_MEROPSED_WATCH)
    except OSError, ee:
        try:
            a = Article.objects.get(doi=doi)
            guid = a.si_guid
        except Article.DoesNotExist, e:
            raise ValueError("I can't find an article with doi, %s" % doi)
        aries_zip = os.path.join(settings.MEROPS_ARIES_DELIVERY, guid + ".zip")
        process_doc_from_aries(aries_zip)

def requeue_finishxml(doi):
    return requeue(doi, settings.MEROPS_FINISH_XML_WATCH_BU, settings.MEROPS_FINISH_XML_WATCH)

def main(*args, **options):
    usage_msg = "usage: requeue [merops|finishxml] [doi]"
    if len(args) != 2:
        print(usage_msg)
        sys.exit(1)
        
    if args[0] == 'merops':
        requeue_merops(args[1])
    elif args[0] == 'finishxml':
        requeue_finishxml(args[1])
    else:
        print("I don't recognize the process, %s" % args[0])
        print(usage_msg)
        sys.exit(1)

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
