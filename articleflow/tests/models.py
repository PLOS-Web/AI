from django.test import TestCase
from articleflow.models import *

class TransitionTestCase(TestCase):
    fixtures = ['initial_data.json', 'transitions_testdata.json']

    def test_current_articlestate(self):
        a = Article.objects.get(pk=1)
        c_as = a.current_articlestate
        manual_c_as = ArticleState.objects.get(pk=6)
        self.assertEqual(c_as,manual_c_as)

    def test_possible_transitions(self):
        a = Article.objects.get(pk=1)
        pts = a.possible_transitions()
        # should only be one possible transition here
        t = pts.get()
        manual_t = Transition.objects.get(pk=1)
        self.assertEqual(t, manual_t)

    def test_transition(self):
        a = Article.objects.get(pk=1)

        # Make sure the article is in the correct state before starting
        s0 = a.current_articlestate.state
        manual_s0 = ArticleState.objects.get(pk=6).state
        self.assertEqual(s0,manual_s0)

        # execute transition
        pts = a.possible_transitions()
        # should only be one
        t = pts.get()
        # make fake user object
        user = User.objects.get(pk=1)
        a.execute_transition(t,user)
        
        # Correct finishing state?
        s_f = a.current_articlestate.state
        manual_s_f = State.objects.get(pk=4)
        self.assertEqual(s_f, manual_s_f)

        # Made a transition
        t = a.articletransitions.get()
        self.assertTrue(t)
