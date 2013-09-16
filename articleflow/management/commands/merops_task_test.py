import sys

import articleflow.daemons.merops_tasks as merops_tasks

from django.core.management.base import BaseCommand, CommandError

def main(*args, **options):
    if len(args) != 1:
        sys.exit(1)
    try:
        func = getattr(merops_tasks, args[0])
    except AttributeError, e:
        print "merops_tasks does not have a function, %s" % args[0]
        sys.exit(1)
        
    func()
    

class Command(BaseCommand):
    args = "<function_name>"
    help = "call a function from merops_tasks by name"

    def handle(self, *args, **options):
        main(*args, **options)
