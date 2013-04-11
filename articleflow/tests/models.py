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
    art2: pone.11
          Ready for QC (CW) None -> 'At CW'
    art3: pone.20
          Needs Web Corrections (CW)

    '''

    def test_reassignment_transition(self):
        logger_func_name = 'test_transition'
        art1 = Article.objects.get(doi='pone.10')
        
        new_state = State.objects.get(name='Ready for QC (CW)')
        new_as = ArticleState(article=art1,
                              state=new_state)
        new_as.save()
        expected_assignee = User.objects.get(username='zyg_test')
        logger.info("%s: New articlestate: %s" % (logger_func_name, new_as))
        self.assertEqual(new_as.assignee, expected_assignee)

        art2 = Article.objects.get(doi='pone.11')
        new_as = ArticleState(article=art2,
                              state=new_state)
        new_as.save()
        self.assertEqual(new_as.assignee, None)

    def test_assign_creator_transition(self):
        art3 = Article.objects.get(doi='pone.20')
        p_trans = art3.possible_transitions()
        logger.debug("LALALALALAL: Possible transitions:")
        for pt in p_trans:
            logger.debug("Possible Transition: %s" % pt.verbose_unicode())
        trans = Transition.objects.get(pk=71)
        user = User.objects.get(username='web_test')
    
        art3.execute_transition(trans, user)
        art3 = Article.objects.get(doi='pone.20')
        self.assertEqual(art3.current_articlestate.assignee, user)
