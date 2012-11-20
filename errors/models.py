from django.db import models
from articleflow.models import Article

ERROR_LEVEL = (
    (1, 'Error'),
    (2, 'Warning'),
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

class Error(models.Model):
    message = models.CharField(max_length=600)
    level = models.IntegerField(choices=ERROR_LEVEL)
    
    # FKs
    error_set = models.ForeignKey('ErrorSet', related_name='errors')
    #   Points to error if existed in previous error set
    old_error = models.ForeignKey('Error', related_name='new_error',
                                  null=True, blank=True, default=None)
    current_status = models.ForeignKey('ErrorStatus', related_name='current_status_of', null=True, blank=True, default=None)

    # Bookkeeping
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s: %s" % (self.get_level_display(), self.message)

    def save(self, *args, **kwargs):
        insert = not self.pk
        ret = super(Error, self).save(*args, **kwargs)
        
        # Add a new 'open' status entry for new issues
        if insert: 
            status = ErrorStatus(state=1, error=self)
            status.save()

        return ret
            
class ErrorStatus(models.Model):
    state = models.IntegerField(choices=STATUS_CODES)

    # FKs
    error = models.ForeignKey('Error', related_name='statuses')

    # Bookkeeping
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_state_display()

    def save(self, *args, **kwargs):
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
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s, %s" % (self.get_source_display(), self.created)
    
