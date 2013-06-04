from django.core.management.base import BaseCommand, CommandError

from articleflow.views import find_highest_file_version_number

def main():
    find_highest_file_version_number('/var/spool/delivery/merops/merops/out', 'pone.0012345')
    find_highest_file_version_number('/var/spool/delivery/merops/merops/out', 'pone.0012340')

class Command(BaseCommand):
    def handle(self, *args, **options):
        main()
