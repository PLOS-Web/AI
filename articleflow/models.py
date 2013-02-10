from django.db import models
from django.contrib.auth.models import User, Group

AUTO_ASSIGN = (
    (1, 'No'),
    (2, 'Yes'),
    (3, 'Custom')
)

class State(models.Model):
    """
    Defines the possible states that articles can be in
    """
    name = models.CharField(max_length=100)
    last_modified = models.DateTimeField(auto_now=True)
    worker_groups = models.ManyToManyField(Group, related_name="state_assignments")
    auto_assign = models.IntegerField(default=1, choices=AUTO_ASSIGN)

    def __unicode__(self):
        return self.name

    def possible_assignees(self):
        return User.objects.filter(groups__state_assignments=self)

class ArticleState(models.Model):
    """
    Holds histories of states for each article
    @TODO set uneditable
    """
    article = models.ForeignKey('Article', related_name='article_states')
    state = models.ForeignKey('State')
    assignee = models.ForeignKey(User,null=True, blank=True, default=None)
    from_transition = models.ForeignKey('Transition', related_name='articlestates_created' , null=True, blank=True, default=None)
    from_transition_user = models.ForeignKey(User, related_name='articlestates_created',null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.article, self.state)
    
    def assign_user(self, user):
        self.assignee = user
        ah = AssignmentHistory(user=user, article_state=self)
        self.save()
        ah.save()

    def save(self, *args, **kwargs):
        ret = super(ArticleState, self).save(*args, **kwargs)
        art = self.article
        if art:
            art.current_articlestate = self
            art.current_state = self.state
            art.save()
        if self.assignee:
            ah = AssignmentHistory(user=self.assignee, article_state=self)
            ah.save()
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
    current_state = models.ForeignKey('State', related_name="current_articles", null=True, blank=True, default=None)
    article_extras = models.ForeignKey('ArticleExtras', related_name="article_dont_use", null=True, blank=True, default=None)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi
    
    # Return the possible transitions that this object can do based on its current state
    def possible_transitions(self, user=None):
        if user:
            raw_transitions = self.current_state.possible_transitions.all()
            return raw_transitions.filter(allowed_groups__user=user)
        return self.current_state.possible_transitions

    def execute_transition(self, transition, user):
        return transition.execute_transition(self, user)

    def save(self, *args, **kwargs):
        insert = not self.pk
        ret = super(Article, self).save(*args, **kwargs)

        # Create a blank articleextras row
        if insert:
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

    # Bookkeeping
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

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
    allowed_groups = models.ManyToManyField(Group, related_name="allowed_transitions")
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

class AssignmentHistory(models.Model):
    user = models.ForeignKey(User, related_name='assignment_histories')
    article_state = models.ForeignKey('ArticleState', related_name='assignment_histories')
    
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

class AssignmentRatio(models.Model):
    user = models.ForeignKey(User, related_name='assignment_weights')
    state = models.ForeignKey('State', related_name='assignment_weights')
    weight = models.IntegerField()

    # bookkeeping
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "state")
