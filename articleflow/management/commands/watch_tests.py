from django.core.management.base import BaseCommand, CommandError

from articleflow.merops_tasks import watch_docs_from_aries

def main():
    watch_docs_from_aries()

class Command(BaseCommand):
    def handle(self, *args, **options):
        main()
