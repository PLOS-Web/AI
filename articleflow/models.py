import datetime
from django.utils.timezone import utc

from django.db import models
from django.contrib.auth.models import User, Group

from django.db.models import Sum, Max
###import autoassign

import logging
logger = logging.getLogger(__name__)

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
    worker_groups = models.ManyToManyField(Group, related_name="state_assignments", null=True, blank=True, default=None)
    auto_assign = models.IntegerField(default=1, choices=AUTO_ASSIGN)
    reassign_previous = models.BooleanField(default=True)
    progress_index = models.IntegerField(default=0)

    #Bookkeeping 
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.name

    def possible_assignees(self):
        return User.objects.filter(groups__state_assignments=self)

    class Meta:
        ordering = ['progress_index']


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

    #Bookkeeping 
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.article, self.state)
    
    def verbose_unicode(self):
        return "{pk: %s, article: %s, assignee: %s, state: %s, from_transition: %s, from_transition_user: %s, created: %s}" % (self.pk, self.article, self.assignee, self.state, self.from_transition, self.from_transition_user, self.created)
    
    def assign_user(self, user):
        self.assignee = user
        ah = AssignmentHistory(user=user, article_state=self)
        self.save()
        ah.save()

    def save(self, *args, **kwargs):
        insert = not self.pk
        logger.debug("SAVING ARTICLESTATE: %s" % self.verbose_unicode())

        ret = super(ArticleState, self).save(*args, **kwargs)
        art = self.article

        if insert:
            if self.assignee:
                self.assign_user(self.assignee)
            else:
                # Check to see if a previous assignee should be assigned
                if self.state.reassign_previous:
                    try:
                        latest_same_articlestate = ArticleState.objects.filter(article=self.article,state=self.state,created__lt=self.created).latest('created')
                        logger.debug("Found previous same state for %s: %s" % (art.doi, latest_same_articlestate.verbose_unicode()))
                        if latest_same_articlestate.assignee:
                            logger.info("Found previous same state assignee for %s. Reassigning %s" % (self.article.doi ,latest_same_articlestate.assignee))
                            self.assign_user(latest_same_articlestate.assignee)
                    except ArticleState.DoesNotExist, e:
                        logger.info("No previous same state for %s found" % self.article.doi)
                # Use the autoassigner if applicable
                if not self.assignee and self.state.auto_assign > 1:
                    print "Finding worker ..."
                    a_user = AutoAssign.pick_worker(self.article, self.state, datetime.date.today())
                    if a_user:
                        self.assign_user(a_user)

        if art:
            art.current_articlestate = self
            art.current_state = self.state
            art.save()

        return ret

class Journal(models.Model):
    full_name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200) #the common acronym/shortening of the journal's name
    em_db_name = models.CharField(max_length=200) #the name of the journal's db in the EM MSSQL DB
    em_url_prefix = models.CharField(max_length=200) #the journal name modifier for EM's url scheme
    em_ambra_stage_prefix = models.CharField(max_length=200) #the journal name modifier for stage Ambra's URL scheme
    
    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
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
    si_guid = models.CharField(max_length=500, null=True, blank=True, default=None)
    md5 = models.CharField(max_length=500, null=True, blank=True, default=None)
    current_articlestate = models.ForeignKey('ArticleState', related_name='current_article', null=True, blank=True, default=None)
    current_state = models.ForeignKey('State', related_name="current_articles", null=True, blank=True, default=None)
    article_extras = models.ForeignKey('ArticleExtras', related_name="article_dont_use", null=True, blank=True, default=None)
    em_pk = models.IntegerField(null=True, blank=True, default=None)
    em_ms_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    em_max_revision = models.IntegerField(null=True, blank=True, default=None)
    
    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi
    
    def verbose_unicode(self):
        return "doi: %s, pubdate: %s, journal: %s, si_guid: %s, md5: %s, created: %s" % (self.doi, self.pubdate, self.journal.short_name, self.si_guid, self.md5, self.created)
    
    # Return the possible transitions that this object can do based on its current state
    def possible_transitions(self, user=None):
        if user:
            raw_transitions = self.current_state.possible_transitions.all()
            return raw_transitions.filter(allowed_groups__user=user).distinct()
        return self.current_state.possible_transitions.distinct()

    def execute_transition(self, transition, user):
        return transition.execute_transition(self, user)

    def save(self, *args, **kwargs):
        insert = not self.pk
        logger.info("SAVING ARTICLE: %s" % self.verbose_unicode())
        ret = super(Article, self).save(*args, **kwargs)

        # Create a blank articleextras row
        if insert:
            # create new state
            logger.info("INSERTING NEW ARTICLE: %s" % self.doi)
            logger.debug("ABOUT TO CREATE A \"NEW\" ArticleState: %s" % self.verbose_unicode())
            s = ArticleState(article=self, state=State.objects.get(name="New"), created=self.created)
            s.save()
            
            if not self.article_extras:
                a_extras = ArticleExtras(article=self)
                a_extras.save()
                self.article_extras = a_extras
                self.save()

            if not self.current_articlestate:
                logger.error("WHY AM I RUNNING")
                a_as = ArticleState(article=self)
                a_as.state, new = State.objects.get_or_create(name="New")
                a_as.save()
        else:
            logger.info("UPDATING EXISTING ARTICLE: %s" % self.doi)

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
    num_issues_legacy = models.IntegerField(default=0)
    
    # Error counts
    num_errors_total = models.IntegerField(default=0)
    num_errors = models.IntegerField(default=0)
    num_warnings = models.IntegerField(default=0)

    # Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
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

    #Bookkeeping 
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
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

    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'(%s, %s): %s %s' % (self.article_state.article.doi, self.article_state.state.name, self.user.username, self.created)

class AssignmentRatio(models.Model):
    user = models.ForeignKey(User, related_name='assignment_weights')
    state = models.ForeignKey('State', related_name='assignment_weights')
    weight = models.IntegerField(null=True, blank=True, default=None)

    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "state")

    def __unicode__(self):
        return u"state: %s, user: %s, weight: %s" % (self.state.name, self.user.username, self.weight)

class AutoAssign():
    @staticmethod
    def total_group_weight(state):
        return state.assignment_weights.aggregate(Sum('weight'))['weight__sum']

    @staticmethod
    def total_assignments(state, start_time):
        return AssignmentHistory.objects.filter(created__gte=start_time).count()

    @staticmethod
    def worker_assignments(state, user, start_time):
        return AssignmentHistory.objects.filter(user=user).filter(created__gte=start_time).count()

    @staticmethod
    def pick_worker(article, state, start_time):
        print "Pick Worker start"
        total_assigns = AutoAssign.total_assignments(state, start_time)
        total_weight = AutoAssign.total_group_weight(state)

        possible_assignees = state.possible_assignees()
        
        # if this is returning to an old state, try to reassign to the last person who had it
        try:
            last_state = ArticleState.objects.filter(article=article).filter(state=state).order_by('created')[1]
            print "last_state: %s" % last_state
            print "last_state_assignee: %s" % last_state.assignee
            if last_state.assignee in possible_assignees.all():
                print "Old assignee found"
                return last_state.assignee
        except IndexError:
            pass

        # if there are no weights defined, don't assign
        if not total_weight:
            print "No weights defined"
            return None

        # if nothing has been assigned, give to person with highest weight
        if total_assigns == 0:
            print "Nothing assigned yet, giving max weighted user"
            max_weight = AssignmentRatio.objects.filter(state=state).aggregate(Max('weight'))['weight__max']
            print "Max_weight: %s" % max_weight
            return AssignmentRatio.objects.filter(weight=max_weight)[0].user

    # otherwise figure out who has the biggest assignment deficit

        print "Analying deficits"
        r_users = []
        max_deficit = (0, None)
        for u in possible_assignees.all():
            print "Analyzing %s ..." % u
            work_ratio = AutoAssign.worker_assignments(state, u, start_time) / float(total_assigns)
            print "work_ratio: %s" % work_ratio
            try:
                weight_ratio = AssignmentRatio.objects.get(user=u, state=state).weight / float(total_weight)
                if weight_ratio == 0:
                    print "Weight ratio is zero, skipping"
                    continue
            except AssignmentRatio.DoesNotExist:
                print "No weight assigned, skipping"
                continue
            print "weight_ratio: %s" % weight_ratio
            deficit = weight_ratio - work_ratio
            print "deficit: %s" % deficit
        
            r_users += [(deficit, u)]
            if deficit > max_deficit[0] or not max_deficit[1]:
                max_deficit = (deficit, u)

        return max_deficit[1]
