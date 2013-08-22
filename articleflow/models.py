import pytz
import datetime
import re
import collections

from django.utils.timezone import utc
from django.db import models
from django.contrib.auth.models import User, Group

from django.db.models import Sum, Max
###import autoassign

import notification.models as notification

import logging
logger = logging.getLogger(__name__)

PAC = pytz.timezone('US/Pacific')

def get_iterable(x):
    if isinstance(x, collections.Iterable):
        return x
    else:
        return (x,)

def now():
    return datetime.datetime.utcnow().replace(tzinfo=utc)

def toUTCc(d):
    if not d:
        return None

    logger.debug("Ensuring datetime is UTC: %s" % d)
    if d.tzinfo == pytz.utc:
        logger.debug("Datetime already UTC")
        return d
    else:
        d_utc = PAC.normalize(PAC.localize(d)).astimezone(pytz.utc)
        logger.debug("Datetime converted to: %s" % d_utc)
        return d_utc

AUTO_ASSIGN = (
    (1, 'No'),
    (2, 'Yes'),
    (3, 'Custom')
)

def get_journal_from_doi(doi):
    match = re.match('.*(?=\.)', doi)
    
    if not match:
        raise ValueError('Could not find a journal short_name in doi, %s' % doi)
    short_name = re.match('.*(?=\.)', doi).group(0)
    
    try:
        return Journal.objects.get(short_name=short_name)
    except Journal.DoesNotExist:
        raise ValueError("doi prefix, %s, does not match any known journal" % short_name)

class State(models.Model):
    """
    Defines the possible states that articles can be in
    """
    name = models.CharField(max_length=100)
    unique_name = models.CharField(max_length=100, unique=True, blank=True, null=True, default=None
                                 ,help_text="Unique name given to transition for programmatic referencing")
    last_modified = models.DateTimeField(auto_now=True)
    worker_groups = models.ManyToManyField(Group, related_name="state_assignments", null=True, blank=True, default=None)
    auto_assign = models.IntegerField(default=1, choices=AUTO_ASSIGN)
    reassign_previous = models.BooleanField(default=True)
    progress_index = models.IntegerField(default=0)
    typesetters = models.ManyToManyField('Typesetter', related_name="allowed_states", null=True, blank=True, default=None,
                                         help_text="typesetter processes to which this state belongs")

    #Bookkeeping 
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.name

    def possible_assignees(self):
        return User.objects.filter(groups__state_assignments=self)

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(State, self).save(*args, **kwargs)
        return ret

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
    created = models.DateTimeField(null=True, blank=True, default=None)
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
	if insert and not self.created:
                self.created = now()
        insert = not self.pk
        logger.debug("%s saving articlestate: %s" % (self.article.doi, self.verbose_unicode()))

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
                        logger.debug("%s: found previous same state: %s" % (art.doi, latest_same_articlestate.verbose_unicode()))
                        if latest_same_articlestate.assignee:
                            logger.info("%s: found previous same state assignee for. Reassigning to %s" % (self.article.doi ,latest_same_articlestate.assignee))
                            self.assign_user(latest_same_articlestate.assignee)
                    except ArticleState.DoesNotExist, e:
                        logger.info("%s: no previous same state found" % self.article.doi)
                # Use the autoassigner if applicable
                if not self.assignee and self.state.auto_assign > 1:
                    logger.info("%s: invoking autoassigner . . ." % self.article.doi)
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
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)    

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(Journal, self).save(*args, **kwargs)
        return ret

    def __unicode__(self):
        return self.full_name

class Typesetter(models.Model):
    """
    Describes typesetter
    """
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2048, null=True, blank=True, default=None)

    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)    

    def verbose_unicode(self):
        return "name: %s, description: %s, created: %s, last_modified: %s" % (self.name, self.description, self.created, self.last_modified)

    def __unicode__(self):
        return self.name

class Article(models.Model):
    """
    Holds information about each article
    """
    doi = models.CharField(max_length=50, unique=True)
    pubdate = models.DateField(null=True, blank=True, default=None)
    journal = models.ForeignKey('Journal', null=True, blank=True, default=None)
    si_guid = models.CharField(max_length=500, null=True, blank=True, default=None)
    md5 = models.CharField(max_length=500, null=True, blank=True, default=None)
    current_articlestate = models.ForeignKey('ArticleState', related_name='current_article', null=True, blank=True, default=None)
    current_state = models.ForeignKey('State', related_name="current_articles", null=True, blank=True, default=None)
    article_extras = models.ForeignKey('ArticleExtras', related_name="article_dont_use", null=True, blank=True, default=None)
    typesetter = models.ForeignKey('Typesetter', related_name='articles_typeset', null=True, blank=True, default=None)
    em_pk = models.IntegerField(null=True, blank=True, default=None)
    em_ms_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    em_max_revision = models.IntegerField(null=True, blank=True, default=None)
    
    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.doi
    
    def verbose_unicode(self):
        return "doi: %s, pubdate: %s, journal: %s, si_guid: %s, md5: %s, created: %s" % (self.doi, self.pubdate, self.journal, self.si_guid, self.md5, self.created)
    
    # Return the possible transitions that this object can do based on its current state

    def current_assignee(self):
        return self.current_articlestate.assignee

    def possible_transitions(self, user=None):
        if user:
            raw_transitions = self.current_state.possible_transitions.all()
            return raw_transitions.filter(allowed_groups__user=user).distinct()
        return self.current_state.possible_transitions.distinct()

    def execute_transition(self, transition, user, assignee=None):
        s = transition.execute_transition(self, user, assignee=assignee)
        if s:
            s.save()    
        return s
        

    def most_advanced_state(self, same_typesetter=True):
        states = self.states
        if same_typesetter:
            states.filter(typesetter=self.typesetter)
        if states:
            return states.latest('progress_index')
        else:
            return None

    def save(self, *args, **kwargs):
        insert = not self.pk
        logger.info("%s: saving article: %s" % (self.doi,self.verbose_unicode()))
	if insert and not self.created:
                self.created = now()
        if not self.journal:
            logger.debug("%s: automatically figuring out journal" % self.doi)
            self.journal = get_journal_from_doi(self.doi)
        ret = super(Article, self).save(*args, **kwargs)

        # Create a blank articleextras row
        if insert:
            # create new state
            logger.info("%s: inserting new article" % self.doi)
            logger.debug("%s: about to create a \"NEW\" ArticleState: %s" % (self.doi, self.verbose_unicode()))
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
            logger.info("%s: updating existing article model" % self.doi)

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
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
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
    unique_name = models.CharField(max_length=100, unique=True, blank=True, null=True, default=None
                                 ,help_text="Unique name given to transition for programmatic referencing")
    from_state = models.ForeignKey('State', related_name='possible_transitions')
    to_state = models.ForeignKey('State', related_name='possible_last_transitions')
    disallow_open_items = models.BooleanField(default=False)
    allowed_groups = models.ManyToManyField(Group, related_name="allowed_transitions")
    assign_transition_user = models.BooleanField(default=False)
    assign_previous_assignee = models.BooleanField(default=False)
    preference_weight = models.IntegerField()
    file_upload_destination = models.CharField(max_length=600, null=True, blank=True, default=None, help_text="If this transition requires an upload, enter the path to the desired destination directory.  Multiple destinations may be used by listing them separated by spaces.  If no upload is required, leave this field blank.")
    file_upload_description = models.CharField(max_length=600, null=True, blank=True, default=None, help_text="If this transition requires an upload, this is the help text to display")
    new_assignee_notification = models.ForeignKey(notification.NoticeType, related_name='transitions', null=True, blank=True, default=None, help_text="Notification type that should be sent to the new assignee when this transition happens.")

    #Bookkeeping 
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s: %s to %s' % (self.name, self.from_state, self.to_state)

    def verbose_unicode(self):
        return u'{pk: %s, name: %s,from_state: %s, to_state: %s, disallow_open_items: %s, assign_transition_user: %s, preference_weight: %s , created: %s, last_modified: %s}' % (self.pk, self.name, self.from_state, self.to_state, self.disallow_open_items, self.assign_transition_user, self.preference_weight, self.created, self.last_modified)
    
    def execute_transition(self, art, user, assignee=None):
        """
        moves article to a new state.  Creates new ArticleState and a Transition
        to describe what happened
        """
        if (art.current_articlestate.state == self.from_state):
            logger.debug("Creating articlestate for transition %s" % self.verbose_unicode())
            old_assignee = art.current_articlestate.assignee
            s = art.article_states.create(state=self.to_state,
                                          from_transition=self,
                                          from_transition_user=user)
            if assignee:
                s.assignee = assignee
            elif self.assign_previous_assignee and old_assignee:
                logger.debug("Assigning previous state's assignee ...")
                s.assignee = old_assignee
            elif self.assign_transition_user:
                logger.debug("Assign_transition_user = true, assigning %s to %s" % (user, s))
                s.assignee = user

            if self.new_assignee_notification and s.assignee:
                logger.debug("%s Sending notification, %s, to %s..." % (art.doi, self.new_assignee_notification, s.assignee))
                ctx = {
                    'article': art,
                    'assignee': s.assignee,
                    'from_transition_user': user,
                    }
                notification.send([s.assignee], self.new_assignee_notification.label, ctx)
            
            logger.debug("Execute transition is returing this state: %s" % s.verbose_unicode())
            return s
        else:
            logger.warning("%s: incorrectly attempted to perform transition, %s, while in state, %s (needed state, %s" % (art.doi, self, art.current_articlestate.state, self.from_state))
            return False

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(Transition, self).save(*args, **kwargs)
        return ret

class AssignmentHistory(models.Model):
    user = models.ForeignKey(User, related_name='assignment_histories')
    article_state = models.ForeignKey('ArticleState', related_name='assignment_histories')

    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'(%s, %s): %s %s' % (self.article_state.article.doi, self.article_state.state.name, self.user.username, self.created)

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(AssignmentHistory, self).save(*args, **kwargs)
        return ret

class WatchState(models.Model):
    watcher = models.CharField(max_length=100, unique=True, blank=True, null=True, default=None
                                 ,help_text="Unique name given to worker")
    last_mtime = models.DateTimeField(null=True, blank=True, default=None)

    def gt_last_mtime(self, dt):
        if dt is None:
            return False
        if not self.last_mtime:
            return True
        logger.debug("Comparing times: 'last_mtime': %s < 'dt': %s" % (self.last_mtime, toUTCc(dt)))
        return self.last_mtime < toUTCc(dt.replace(microsecond=0))

    def update_last_mtime(self, dt):
        self.last_mtime = toUTCc(dt)
        logger.debug("Updating last_mtime to %s" % self.last_mtime)
        self.save()

    def __unicode__(self):
        return self.watcher

    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

class AssignmentRatio(models.Model):
    user = models.ForeignKey(User, related_name='assignment_weights')
    state = models.ForeignKey('State', related_name='assignment_weights')
    weight = models.IntegerField(null=True, blank=True, default=None)

    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "state")

    def __unicode__(self):
        return u"state: %s, user: %s, weight: %s" % (self.state.name, self.user.username, self.weight)

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(AssignmentRatio, self).save(*args, **kwargs)
        return ret

class ExternalSync(models.Model):
    name = models.CharField(max_length=200, unique=True)
    source = models.CharField(max_length=200)

    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(ExternalSync, self).save(*args, **kwargs)
        return ret

    def start_sync(self):
        hist = SyncHistory(sync=self)
        hist.save()
        return hist

    @property
    def latest_sync(self):
        try:
            return self.histories.latest('created')
        except SyncHistory.DoesNotExist, ee:
            return None

    @property
    def latest_external_timestamp(self):
        try:
            return self.histories.latest('max_external_timestamp')
        except SyncHistory.DoesNotExist, ee:
            return None

    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['created']

class SyncHistory(models.Model):
    sync = models.ForeignKey('ExternalSync', related_name='histories')
    completion_time = models.DateTimeField(null=True, blank=True, default=None)
    max_external_timestamp = models.DateTimeField(null=True, blank=True, default=None)

    #Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def is_done(self):
        return (self.completion_time)

    def complete(self):
        self.completion_time = now()
        self.save()

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(SyncHistory, self).save(*args, **kwargs)
        return ret

    def __unicode__(self):
        return u"%s: %s" % (self.sync, self.created)

    class Meta:
        ordering = ['created']

class AutoAssign():
    @staticmethod
    def total_group_weight(state):
        return state.assignment_weights.aggregate(Sum('weight'))['weight__sum']

    @staticmethod
    def total_assignments(state, start_time):
        return AssignmentHistory.objects.filter(created__gte=start_time,article_state__state=state).count()

    @staticmethod
    def worker_assignments(state, user, start_time):
        return AssignmentHistory.objects.filter(user=user, created__gte=start_time, article_state__state=state).count()

    @staticmethod
    def pick_worker(article, state, start_time):
        logger.info("%s: picking worker . . ." % article.doi)
        total_assigns = AutoAssign.total_assignments(state, start_time)
        total_weight = AutoAssign.total_group_weight(state)

        possible_assignees = state.possible_assignees()
        
        # if this is returning to an old state, try to reassign to the last person who had it
        try:
            last_state = ArticleState.objects.filter(article=article).filter(state=state).order_by('created')[1]
            logger.debug("%s: last state was %s with assignee, %s" % (article.doi, last_state, last_state.assignee))
            if last_state.assignee in possible_assignees.all():
                logger.info("%s: picking previously assigned user, %s" % (article.doi, last_state.assignee))
                return last_state.assignee
        except IndexError:
            pass

        # if there are no weights defined, don't assign
        if not total_weight:
            logger.info("%s: No weights defined, picking nobody" % article.doi)
            return None

        # if nothing has been assigned, give to person with highest weight
        if total_assigns == 0:
            logger.debug("%s: nothing assigned yet in this state" % article.doi)
            max_weight = AssignmentRatio.objects.filter(state=state).aggregate(Max('weight'))['weight__max']
            max_weight_user = AssignmentRatio.objects.filter(weight=max_weight)[0].user
            logger.debug("%s: found max weight user, %s, with weight, %s" % (article.doi, max_weight_user, max_weight))
            return max_weight_user

    # otherwise figure out who has the biggest assignment deficit

        logger.debug("%s: analying worker deficits ..." % (article.doi))
        r_users = []
        max_deficit = (0, None)
        for u in possible_assignees.all():
            logger.debug("%s: analyzing %s ..." % (article.doi, u))
            work_ratio = AutoAssign.worker_assignments(state, u, start_time) / float(total_assigns)
            logger.debug("%s: %s's work_ratio: %s" % (article.doi, u, work_ratio))
            try:
                weight_ratio = AssignmentRatio.objects.get(user=u, state=state).weight / float(total_weight)
                if weight_ratio == 0:
                    logger.debug("%s: %s's weight ratio is zero, skipping" % (article.doi, u))
                    continue
            except AssignmentRatio.DoesNotExist:
                logger.debug("%s: %s has no weight assigned, skipping" % (article.doi, u))
                continue
            logger.debug("%s: %s's weight_ratio: %s" % (article.doi, u, weight_ratio))
            deficit = weight_ratio - work_ratio
            logger.debug("%s: %s's deficit: %s" % (article.doi, u, deficit))
        
            r_users += [(deficit, u)]
            if deficit > max_deficit[0] or not max_deficit[1]:
                max_deficit = (deficit, u)
        
        logger.info("%s: picking worker with biggest deficit.  user: %s, deficit: %s" % (article.doi, max_deficit[1], max_deficit[0]))
        return max_deficit[1]

def reassign_article(article, to_user, from_transition_user=None):
    """Reassign article to user."""
    arts = get_iterable(article)
    for a in arts:
        logger.info("%s: reassigning to %s" % (a.doi, to_user))
        c_arts = a.current_articlestate
        n_arts = ArticleState(article=a,
                              state=c_arts.state,
                              assignee=to_user,
                              from_transition_user=from_transition_user)

        n_arts.save()

        if not to_user:
            n_arts.assignee = None
            n_arts.save()
