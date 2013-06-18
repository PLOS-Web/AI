from django.test import TestCase

from articleflow.models import Article, AutoAssign, AssignmentRatio, ArticleState, State
from django.contrib.auth.models import User, Group

class AutoAssignTestCase(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.u_1 = User(username="u_1")
        self.u_1.save()
        self.u_2 = User(username="u_2")
        self.u_2.save()
        self.u_3 = User(username="u_3")
        self.u_3.save()
        self.aa_g1 = Group(name='g1')
        self.aa_g1.save()
        self.aa_g1.user_set.add(self.u_1)
        self.aa_g1.user_set.add(self.u_2)
        self.aa_g1.user_set.add(self.u_3)
        self.aa_state = State(name='test_aa',
                              unique_name='test_aa',
                              auto_assign=2,
                              reassign_previous=False,
                              progress_index=0)
        self.aa_state.save()
        self.aa_state.worker_groups.add(self.aa_g1)
        self.a_1 = Article(doi='pone.0012345')
        self.a_1.save()
        self.a_2 = Article(doi='pone.1012345')
        self.a_2.save()
        self.a_3 = Article(doi='pone.2012345')
        self.a_3.save()

    def test_null_assignratio(self):
        arts = ArticleState(article=self.a_1,
                            state=self.aa_state)
        arts.save()
        self.assertEqual(arts.assignee, None)
    
    def test_assignratio_single(self):
        a_s = AssignmentRatio(user=self.u_1,
                              state=self.aa_state,
                              weight=1)
        a_s.save()
        arts = ArticleState(article=self.a_1,
                            state=self.aa_state)
        arts.save()
        self.assertEqual(arts.assignee, self.u_1)

    def test_assignratio_multi_equal(self):
        a_s = AssignmentRatio(user=self.u_1,
                              state=self.aa_state,
                              weight=1)
        a_s.save()
        a_s = AssignmentRatio(user=self.u_2,
                              state=self.aa_state,
                              weight=1)
        a_s.save()
        a_s = AssignmentRatio(user=self.u_3,
                              state=self.aa_state,
                              weight=1)
        a_s.save()
        arts = ArticleState(article=self.a_1,
                            state=self.aa_state)
        arts.save()
        self.assertEqual(arts.assignee, self.u_1)

        arts = ArticleState(article=self.a_2,
                            state=self.aa_state)
        arts.save()
        self.assertEqual(arts.assignee, self.u_2)

        arts = ArticleState(article=self.a_3,
                            state=self.aa_state)
        arts.save()
        self.assertEqual(arts.assignee, self.u_3)
        
