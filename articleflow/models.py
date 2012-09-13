from django.db import models
from django.contrib.auth.models import User

class State(models.Model):
    '''
    Defines the possible states that articles can be in
    '''
    name = models.CharField(max_length=100)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

class ArticleState(models.Model):
    '''
    Holds histories of states for each article
    @TODO set uneditable
    '''
    article = models.ForeignKey('Article', related_name='article_states')
    state = models.ForeignKey('State')
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: $s' % (self.article, self.state)

class Article(models.Model):
    '''
    Holds information about each article
    '''
    doi = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi

    def current_articlestate(self):
        return self.article_states.latest('created')

class StateTransition(models.Model):
    '''
    Defines the possible transitions between states
    @TODO add permissions
    '''
    name = models.CharField(max_length=200)
    from_state = models.ForeignKey('State', related_name='possible_transitions')
    to_state = models.ForeignKey('State', related_name='possible_last_transitions')
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s: %s to $s' % (self.name, self.from_state, self.to_state)

class Transition(models.Model):
    '''
    Holds histories of transtitions for each article
    @TODO set uneditable
    '''
    article = models.ForeignKey('Article', related_name='transitions')
    statetransition = models.ForeignKey('StateTransition', related_name='transitions')
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True) 

    def __unicode__(self):
        return u'%s: %s' % (self.article.doi, self.statetransition.name)
    
    

