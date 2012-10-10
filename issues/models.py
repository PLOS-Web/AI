from django.db import models
from django.contrib.auth.models import User
from articleflow.models import Article

STATUS_CODES = (
    (1, 'Open'),
    (2, 'Closed'),
)

class Issue(models.Model):
    """
    Issue table.
    """
    category = models.ForeignKey('Category', related_name='issues')
    description = models.TextField()
    article = models.ForeignKey(Article, related_name='issues')
    status = models.IntegerField(default=1, choices=STATUS_CODES)
    submitter = models.ForeignKey(User, related_name='issues_submitted', null=True, blank=True, default=None)
    # @TODO change to actual FK
    error = models.IntegerField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return self.description

class Comment(models.Model):
    """
    Comments on issues
    """
    issue = models.ForeignKey('Issue', related_name='comments')
    comment = models.TextField()
    submitter = models.ForeignKey(User, related_name='comments_submitted', null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return self.comment

class Category(models.Model):
    """
    Table of available issue categories
    """
    name = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
