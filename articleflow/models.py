from django.db import models
from django.contrib.auth.models import User

class State(models.Model):
    """
    Defines the possible states that articles can be in
    """
    name = models.CharField(max_length=100)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

class ArticleState(models.Model):
    """
    Holds histories of states for each article
    @TODO set uneditable
    """
    article = models.ForeignKey('Article', related_name='article_states')
    state = models.ForeignKey('State')
    from_transition = models.ForeignKey('Transition', related_name='articlestates_created' , null=True, blank=True, default=None)
    from_transition_user = models.ForeignKey(User, related_name='articlestates_created',null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.article, self.state)
    
    def save(self, *args, **kwargs):
        ret = super(ArticleState, self).save(*args, **kwargs)
        art = self.article
        if art:
            art.current_articlestate = self
            art.save()
        return ret

class Journal(models.Model):
    full_name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200)
    last_modified = models.DateTimeField(auto_now=True)    

    def __unicode__(self):
        return self.full_name

class Article(models.Model):
    """
    Holds information about each article
    """
    doi = models.CharField(max_length=50, unique=True)
    pubdate = models.DateField()
    journal = models.ForeignKey('Journal')
    current_articlestate = models.ForeignKey('ArticleState', related_name='current_article', null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi
    
    # Return the possible transitions that this object can do based on its current state
    def possible_transitions(self):
        return self.current_articlestate.state.possible_transitions

    def execute_transition(self, transition, user):
        return transition.execute_transition(self, user)

class ArticleExtras(models.Model):
    """
    Holds extra, fuzzy info about articles for shortcutting searching and filtering
    """

    current_articlestate = models.ForeignKey('Article', related_name='article_extras')

    # Issue counts
    num_issues_xml = models.IntegerField(default=0)
    num_issues_pdf = models.IntegerField(default=0)
    num_issues_xmlpdf = models.IntegerField(default=0)
    num_issues_si = models.IntegerField(default=0)
    
    # Error counts
    num_errors = models.IntegerField(default=0)
    num_warnings = models.IntegerField(default=0)
            
class Transition(models.Model):
    """
    Defines the possible transitions between states
    @TODO add permissions
    """
    name = models.CharField(max_length=200)
    from_state = models.ForeignKey('State', related_name='possible_transitions')
    to_state = models.ForeignKey('State', related_name='possible_last_transitions')
    disallow_open_items = models.BooleanField(default=False)
    preference_weight = models.IntegerField()
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s: %s to %s' % (self.name, self.from_state, self.to_state)
    
    def execute_transition(self, art, user):
        """
        moves article to a new state.  Creates new ArticleState and a Transition
        to describe what happened
        """
        if (art.current_articlestate.state == self.from_state):
            # create new state
            s = art.article_states.create(state=self.to_state,
                                          from_transition=self,
                                          from_transition_user=user)
            
            return s
        else:
            return False


