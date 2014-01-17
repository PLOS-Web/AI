import sys

from django.core.management.base import BaseCommand, CommandError

from articleflow.utils import errors_pubdate_csv

def main(*args, **options):
    if len(args) != 2:
        print "Usage: errors_pubdate_csv <out_filename> <pubdate>"
        sys.exit(1)
    print errors_pubdate_csv(args[0], args[1])

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
