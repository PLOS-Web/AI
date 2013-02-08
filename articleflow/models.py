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
            art.current_state = self.state
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
    pubdate = models.DateField(null=True, blank=True, default=None)
    journal = models.ForeignKey('Journal')
    current_articlestate = models.ForeignKey('ArticleState', related_name='current_article', null=True, blank=True, default=None)
    current_state = models.ForeignKey('State', related_name="current_articles", null=True, blank=True, default=None)
    article_extras = models.ForeignKey('ArticleExtras', related_name="article_dont_use", null=True, blank=True, default=None)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi
    
    # Return the possible transitions that this object can do based on its current state
    def possible_transitions(self):
        return self.current_articlestate.state.possible_transitions

    def execute_transition(self, transition, user):
        return transition.execute_transition(self, user)

    def save(self, *args, **kwargs):
        insert = not self.pk
        ret = super(Article, self).save(*args, **kwargs)

        # Create a blank articleextras row
        if insert:
            # create new state
            s = ArticleState(article=self, state=State.objects.get(name="New"))
            s.save()
            
            if not self.article_extras:
                a_extras = ArticleExtras(article=self)
                a_extras.save()
                self.article_extras = a_extras
                self.save()

            if not self.current_articlestate:
                a_as = ArticleState(article=self)
                a_as.state, new = State.objects.get_or_create(name="New")
                a_as.save()

class ArticleExtras(models.Model):
    """
    Holds extra, fuzzy aggregates on articles for shortcutting searching and filtering
    """

    article = models.ForeignKey('Article', related_name='article_extras_dont_use')

    # Issue counts
    num_issues_total = models.IntegerField(default=0)
    num_issues_xml = models.IntegerField(default=0)
    num_issues_pdf = models.IntegerField(default=0)
    num_issues_xmlpdf = models.IntegerField(default=0)
    num_issues_si = models.IntegerField(default=0)
    
    # Error counts
    num_errors_total = models.IntegerField(default=0)
    num_errors = models.IntegerField(default=0)
    num_warnings = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        insert = not self.pk
        ret = super(ArticleExtras, self).save(*args, **kwargs)

        if insert:
            a = self.article
            a.article_extras = self
            a.save()

        return ret

    def __unicode__(self):
        doi = ""
        try:
            doi = self.article.doi
        except Article.DoesNotExist:
            pass

        return "Article_extras: (doi: %s)" % doi
        
            
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


