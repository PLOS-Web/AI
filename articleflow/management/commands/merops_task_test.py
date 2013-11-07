import sys
from optparse import make_option

import articleflow.daemons.merops_tasks as merops_tasks
import articleflow.daemons.transition_tasks as transition_tasks
import articleflow.daemons.em_sync as em_sync

from django.core.management.base import BaseCommand, CommandError

def main(*args, **options):
    if len(args) != 1:
        sys.exit(1)
    
    if options['t']:
        task_set = transition_tasks
    elif options['e']:
        task_set = em_sync
    else:
        task_set = merops_tasks

    try:
        func = getattr(task_set, args[0])
    except AttributeError, e:
        print "task_set does not have a function, %s" % args[0]
        sys.exit(1)
        
    func()
    

class Command(BaseCommand):
    args = "<function_name>"
    option_list = BaseCommand.option_list + (
        make_option('-t',
                    action='store_true',
                    dest='t',
                    default=False,
                    help='Call function from transition tasks'),
        make_option('-e',
                    action='store_true',
                    dest='e',
                    default=False,
                    help='Call function from em sync'),
        )
    help = "call a 'tasks' function by name by name"
    

    def handle(self, *args, **options):
        main(*args, **options)
