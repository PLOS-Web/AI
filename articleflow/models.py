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
        return u'%s: %s' % (self.article, self.state)

class Article(models.Model):
    '''
    Holds information about each article
    '''
    doi = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi
    
    # Return most recent associated state
    def current_articlestate(self):
        return self.article_states.latest('created')
    
    # Return the possible transitions that this object can do based on its current state
    def possible_transitions(self):
        return self.current_articlestate().state.possible_transitions

    def execute_transition(self, statetrans, instigator):
        statetrans.execute_transition(self, instigator)
            
class Transition(models.Model):
    '''
    Defines the possible transitions between states
    @TODO add permissions
    '''
    name = models.CharField(max_length=200)
    from_state = models.ForeignKey('State', related_name='possible_transitions')
    to_state = models.ForeignKey('State', related_name='possible_last_transitions')
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s: %s to %s' % (self.name, self.from_state, self.to_state)
    
    def execute_transition(self, art, instigator):
        '''
        moves article to a new state.  Creates new ArticleState and a Transition
        to describe what happened
        '''
        if (art.current_articlestate().state == self.from_state):
            # find current state
            c_as = art.current_articlestate()
            # create new state
            s = art.article_states.create(state=self.to_state)
            # create transition entry
            t = ArticleTransition(article = art,
                                  transition=self,
                                  user=instigator,
                                  from_articlestate = c_as,
                                  to_articlestate = s)
            t.save()
            return t
        else:
            return 1
            
class ArticleTransition(models.Model):
    '''
    Holds histories of transtitions for each article
    @TODO set uneditable
    '''
    article = models.ForeignKey('Article', related_name='articletransitions')
    transition = models.ForeignKey('Transition', related_name='articletransitions')
    user = models.ForeignKey(User)
    from_articlestate = models.ForeignKey('ArticleState', related_name='transitioned_to')
    to_articlestate = models.ForeignKey('ArticleState', related_name='transitioned_from')

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.article.doi, self.statetransition.name)

