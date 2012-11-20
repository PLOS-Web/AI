from django.db import models
from django.contrib.auth.models import User
from articleflow.models import Article

STATUS_CODES = (
    (1, 'Open'),
    (2, 'Closed'),
    (3, 'Wont fix'),
)

class Issue(models.Model):
    """
    Issue table.
    """
    category = models.ForeignKey('Category', related_name='issues')
    description = models.TextField()
    article = models.ForeignKey(Article, related_name='issues')
    #status = models.IntegerField(default=1, choices=STATUS_CODES)
    submitter = models.ForeignKey(User, related_name='issues_submitted', null=True, blank=True, default=None)
    # @TODO change to actual FK
    error = models.IntegerField(null=True, blank=True, default=None)
    current_status = models.ForeignKey('IssueStatus', related_name='current_status_of', null=True, blank=True, default=None)
    
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return self.description

    def save(self, *args, **kwargs):
        insert = not self.pk
        ret = super(Issue, self).save(*args, **kwargs)
        
        # Add a new 'open' status entry for new issues
        if insert: 
            status = IssueStatus(state=1, error=self)
            status.save()

        return ret

class IssueStatus(models.Model):
    status = models.IntegerField(choices=STATUS_CODES)
    
    issue = models.ForeignKey('Issue', related_name='statuses')

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_status_display()

    def __save__(self):
        ret = super(IssueStatus, self).save(*args, **kwargs)

        i = self.issue
        i.current_status = self
        i.save()

        return ret
    

class Category(models.Model):
    """
    Table of available issue categories
    """
    name = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
