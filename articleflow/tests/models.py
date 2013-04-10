from django.test import TestCase
from articleflow.models import *
from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)

class TransitionTestCase(TestCase):
    fixtures = ['initial_data.json', 'transitions_testdata.json']

    '''
    art1: pone.10
          Ready for QC (CW) 'zyg_test' -> 'Web Corrections'

    '''

    def test_transition(self):
        logger_func_name = 'test_transition'
        art1 = Article.objects.get(doi='pone.10')
        
        new_state = State.objects.get(name='Ready for QC (CW)')
        new_as = ArticleState(article=art1,
                              state=new_state)
        new_as.save()
        expected_assignee = User.objects.get(username='zyg_test')
        logger.info("%s: New articlestate: %s" % (logger_func_name, new_as))
        self.assertEqual(new_as.assignee, expected_assignee)
