from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from articleflow.daemons.em_sync import sync_live_pubdates

from ai import settings


def main(*args, **options):
    sync_live_pubdates()


class Command(BaseCommand):
    """
    option_list = BaseCommand.option_list + (
        make_option('-f',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Force merops requeue'),
        )
    """
    def handle(self, *args, **options):
        main(*args, **options)
