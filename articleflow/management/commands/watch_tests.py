from django.core.management.base import BaseCommand, CommandError

from articleflow.merops_tasks import watch_docs_from_aries, watch_merops_output, move_to_pm, watch_finishxml_output

def main():
    watch_docs_from_aries()
    watch_merops_output()
    move_to_pm()
    watch_finishxml_output()

class Command(BaseCommand):
    def handle(self, *args, **options):
        main()
