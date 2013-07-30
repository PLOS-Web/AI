from django.core.management.base import BaseCommand
from articleflow.notification_setup import create_notification_types

def main(*args, **options):
    create_notification_types()

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args, **options)
