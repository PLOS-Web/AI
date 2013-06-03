import requests
import simplejson
import datetime

from ai import settings
from django.test import LiveServerTestCase
from articleflow.models import Article, Journal, ArticleState, State
from errors.models import ErrorSet, Error

#host_base = "http://10.135.2.181:8000"
#host_base ="http://192.168.2.40:8000"

class APIArticleTestCase(LiveServerTestCase):

    fixtures = ['initial_data.json']

    def assert_article_exists(self, doi):
        try:
            return Article.objects.get(doi=doi)
        except Article.DoesNotExist:
            self.fail("article with doi %s doesn't exist" % doi)

    def assert_article_doesnt_exist(self, doi):
        try:
            Article.objects.get(doi=doi)
            self.fail("article with %s exist" % doi)
        except Article.DoesNotExist:
            pass

    def test_article_put_extra(self):
        """
        article insert should succeed
        """
        data = {
            'test': 'this is a test'
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        
        self.assert_article_exists('pone.9999999')
            
    def test_article_json_garbage(self):
        """
        article insert should fail
        """
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data='hahaha}')

        self.assert_article_doesnt_exist('pone.9999999')

    def test_article_file_sigs(self):
        """
        article insert should succeed with populated md5 and si_guid
        """
        data = {
            'si_guid': '4AQlP4lP0xGaDAMF6CwzAQ',
            'md5': '79054025255fb1a26e4bc422aef54eb4'
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))

        a = self.assert_article_exists('pone.9999999')
        
        self.assertEqual(a.md5, data['md5'])
        self.assertEqual(a.si_guid, data['si_guid'])


    def test_article_invalid_date_format(self):
        """
        article insert should fail
        """
        data = {
            'pubdate': '2013-12-31 00:00:00'
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))

        self.assert_article_doesnt_exist('pone.9999999')

    def test_article_update_pubdate(self):
        """
        article insert, then puddate update
        """
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps({}))
        self.assert_article_exists('pone.9999999')
            
        data = {
            'pubdate': '2013-12-31'
            }            
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        a = self.assert_article_exists('pone.9999999')
        print (a.verbose_unicode())
            
        self.assertEqual(a.pubdate, datetime.datetime.strptime(data['pubdate'], '%Y-%m-%d').date())

    def test_article_nonexistant_state(self):
        """
        article insert should fail
        """
        data = {
            'state': 'lala',
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))

        self.assert_article_doesnt_exist('pone.9999999')
        
    def test_article_update_nonexistant_state(self):
        """
        article insert, then no update
        """
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps({}))
        self.assert_article_exists('pone.9999999')
            
        data = {
            'state': 'lala',
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        
        a = self.assert_article_exists('pone.9999999')

        self.assertEqual(a.current_state.name,'New')
        
    def test_article_update_state_success(self):
        """
        article insert, then update
        """
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps({}))

        self.assert_article_exists('pone.9999999')

        data = {
            'state': 'Ingested',
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        a = self.assert_article_exists('pone.9999999')
            
        self.assertEqual(a.current_state.name,'Ingested')
        
    def test_article_put_empty(self):
        """
        article insert should succeed
        """
        data = {
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        self.assert_article_exists('pone.9999999')

    def test_article_put_fake_user(self):
        """
        article insert should fail due to fake user
        """

        data = {
            'state': 'Delivered',
            'state_change_user': 'fake_user',
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))

    def test_article_put_real_user(self):
        """
        article insert should succeed with effecting user, jlabarba.
        """
        data = {
            'state': 'New',
            'state_change_user': 'jlabarba',
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        a = self.assert_article_exists('pone.9999999')
        print "**** %s " % a.current_articlestate.verbose_unicode()
        self.assertEqual(a.current_articlestate.from_transition_user.username, data['state_change_user'])

    def test_article_typesetter(self):
        data = {
            'typesetter': 'Merops'
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        print (r.status_code, r.content)
        a = self.assert_article_exists('pone.9999999')
        self.assertEquals(a.typesetter.name, data['typesetter'])

    def test_article_fake_typesetter(self):
        data = {
            'typesetter': 'fake_typesetter'
            }
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps(data))
        self.assertEqual(r.status_code, 400)
        a = self.assert_article_doesnt_exist('pone.9999999')

    def test_article_get(self):
        r = requests.put(self.live_server_url + '/api/article/pone.9999999', data=simplejson.dumps({}))
        self.assert_article_exists('pone.9999999')
        
        r = requests.get(self.live_server_url + '/api/article/pone.9999999')
        self.assertEqual(r.status_code, 200)


class APIErrorSetTestCase(LiveServerTestCase):

    fixtures = ['initial_data.json']

    def assert_errorset_exists(self, doi):
        try:
            return ErrorSet.objects.get(article=Article.objects.get(doi=doi))
        except Article.DoesNotExist, e:
            self.fail("article with %s doesn't exist" % doi)
        except ErrorSet.DoesNotExist, e:
            self.fail("errorset for %s doesn't exist" % doi)
        
    def setUp(self):
        self.doi_1 = 'pone.9999999'
        a = Article(doi=self.doi_1, journal=Journal.objects.get(short_name='pone'))
        a.save()

    def test_errorset_put(self):
        data = {
            'source': 'ariesPull',
            'errors': 'error: stuff\nerror: other stuff\nwarning: a warning\ncorrection: a correction'
            }
        r = requests.put(self.live_server_url + '/api/article/%s/errorset/' % self.doi_1, data=simplejson.dumps(data)) 

        es = self.assert_errorset_exists(self.doi_1)
        errors = es.errors.all().order_by('level')
        
        self.assertEqual(errors[0].level, 1)
        self.assertEqual(errors[2].level, 2)
        self.assertEqual(errors[3].level, 3)
   
class APITransitionTestCase(LiveServerTestCase):

    fixtures = ['initial_data.json']

    def setUp(self):
        self.doi_1 = 'pone.9999999'
        a = Article(doi=self.doi_1, journal=Journal.objects.get(short_name='pone'))
        a.save()
        a_s = ArticleState(article=a, state=State.objects.get(name='Delivered'))
        a_s.save()

    def test_transition_post(self):
        """
        Post a transition
        """
        data = {
            'name': 'Pull',
            }
        r = requests.post(self.live_server_url + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))
        print r.status_code, r.content
        
        a = Article.objects.get(doi=self.doi_1)
        self.assertEquals(a.current_state.name, 'Pulled')

    def test_transition_fake_name(self):
        """
        Transition should fail due to fake name
        """
        data = {
            'name': 'not a transition',
            'transition_user': 'jlabarba',
            }
        r = requests.post(self.live_server_url + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))        
        
        a = Article.objects.get(doi=self.doi_1)
        self.assertEquals(a.current_state.name, 'Delivered')

    def test_transition_fake_username(self):
        """
        Transition should fail due to fake name
        """
        data = {
            'name': 'fake transition',
            'transition_user': 'jlabarba',
            }
        r = requests.post(self.live_server_url + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))        
        
        a = Article.objects.get(doi=self.doi_1)
        self.assertEquals(a.current_state.name, 'Delivered')

    def test_transition_fake_username(self):
        """
        Transition should fail due to fake name
        """
        data = {
            'name': 'Pull',
            'transition_user': 'fake user',
            }
        r = requests.post(self.live_server_url + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))        
        
        a = Article.objects.get(doi=self.doi_1)
        self.assertEquals(a.current_state.name, 'Delivered')

    def test_transition_post_user(self):
        """
        Transition should succeed with from_transition_user
        """
        data = {
            'name': 'Pull',
            'transition_user': 'jlabarba',
            }
        r = requests.post(self.live_server_url + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))        
        
        a = Article.objects.get(doi=self.doi_1)
        self.assertEquals(a.current_state.name, 'Pulled')
        self.assertEquals(a.current_articlestate.from_transition_user.username, data['transition_user'])

    def test_transition_get(self):
        r = requests.get(self.live_server_url + '/api/article/pone.9999999/transition/')
        print r.content
        self.assertEqual(r.status_code, 200)

