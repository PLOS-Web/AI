import datetime
from django.utils.timezone import utc

from django.db import models
from articleflow.models import Article, ArticleExtras


ERROR_LEVEL = (
    (1, 'Error'),
    (2, 'Warning'),
    (3, 'Correction'),
)

STATUS_CODES = (
    (1, 'Open'),
    (2, 'Closed'),
    (3, 'Wont Fix'),
)

ERROR_SET_SOURCES = (
    (1, 'ariesPull'),
    (2, 'ingestPrep'),
    (3, 'test'),
)

def now():
    return datetime.datetime.utcnow().replace(tzinfo=utc)

class Error(models.Model):
    message = models.CharField(max_length=4096)
    level = models.IntegerField(choices=ERROR_LEVEL)
    
    # FKs
    error_set = models.ForeignKey('ErrorSet', related_name='errors')
    #   Points to error if existed in previous error set
    old_error = models.ForeignKey('Error', related_name='new_error',
                                  null=True, blank=True, default=None)
    current_status = models.ForeignKey('ErrorStatus', related_name='current_status_of', null=True, blank=True, default=None)

    # Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s: %s" % (self.get_level_display(), self.message)

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(Error, self).save(*args, **kwargs)
        
        # Add a new 'open' status entry for new issues
        if insert: 
            if self.level == 3:
                status = ErrorStatus(state=2, error=self)
            else:
                status = ErrorStatus(state=1, error=self)
            
            status.save()

            # Only do anything if this is an error for the latest errorset
            if self.error_set == self.error_set.article.error_sets.latest('created'):    
                a_extras, new = ArticleExtras.objects.get_or_create(article=self.error_set.article)
                
            #bad hardcoding for error counts in articleextras
                if self.level == 1:
                    a_extras.num_errors += 1
                elif self.level == 2:
                    a_extras.num_warnings += 1
                else:
                    print "Encountered error category unknown to articleextras"
                    
                a_extras.num_errors_total += 1                    

                a_extras.save()

        return ret

class Meta:
    order_with_respect_to = 'level'
            
class ErrorStatus(models.Model):
    state = models.IntegerField(choices=STATUS_CODES)

    # FKs
    error = models.ForeignKey('Error', related_name='statuses')

    # Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_state_display()

    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(ErrorStatus, self).save(*args, **kwargs)
        
        e = self.error
        e.current_status = self
        e.save()
        
        return ret
        

class ErrorSet(models.Model):
    source = models.IntegerField(choices=ERROR_SET_SOURCES)

    # FKs
    article = models.ForeignKey(Article, related_name='error_sets')

    # Bookkeeping
    created = models.DateTimeField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s: %s, %s" % (self.article.doi, self.get_source_display(), self.created)
    
    def save(self, *args, **kwargs):
        insert = not self.pk
	if insert and not self.created:
                self.created = now()
        ret = super(ErrorSet, self).save(*args, **kwargs)
        
        # Wipe out articleextra tallies on new errorset
        if insert: 
            a_extras, new = ArticleExtras.objects.get_or_create(article=self.article)
            a_extras.num_errors_total = 0
            a_extras.num_errors = 0
            a_extras.num_warnings = 0
            a_extras.save()

        return ret
            
        

        
