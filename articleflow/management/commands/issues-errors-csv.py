import sys

from django.core.management.base import BaseCommand, CommandError

from articleflow.utils import issues_errors_csv

def main(*args, **options):
    if len(args) != 1:
        print "Usage: issues_errors_csv <out_filename>"
        sys.exit(1)
    print issues_errors_csv(args[0])

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
