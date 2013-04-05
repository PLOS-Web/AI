import datetime
from django.utils.timezone import utc
now = datetime.datetime.utcnow().replace(tzinfo=utc)


from django.db import models
from django.contrib.auth.models import User
from articleflow.models import Article, ArticleExtras

STATUS_CODES = (
    (1, 'Open'),
    (2, 'Closed'),
    (3, 'Wont fix'),
)

CATEGORY_COLORS = (
    (1, 'blue'),
    (2, 'red'),
    (3, 'violet'),
    (4, 'orange'),
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
    error = models.IntegerField(null=True, blank=True, default=None)
    current_status = models.ForeignKey('IssueStatus', related_name='current_status_of', null=True, blank=True, default=None)

    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
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
            status = IssueStatus(status=1, issue=self)
            status.save()

            self.current_status = status
            ret = super(Issue, self).save(*args, **kwargs)
            
            a_extras, new = ArticleExtras.objects.get_or_create(article=self.article)
            print "A_EXTRAS"
            print a_extras
            
            #bad hardcoding for issue counts in articleextras
            print self.category.name
            if self.category.name == "XML":
                a_extras.num_issues_xml += 1
            elif self.category.name == "PDF":
                a_extras.num_issues_pdf += 1
            elif self.category.name == "XML+PDF":
                a_extras.num_issues_xmlpdf += 1
            elif self.category.name == "SI":
                a_extras.num_issues_si += 1
            elif self.category.name == "Legacy":
                a_extras.num_issues_legacy += 1
            else:
                print "Encountered category unknown to articleextras"

            a_extras.num_issues_total += 1

            a_extras.save()

        return ret


class IssueStatus(models.Model):
    status = models.IntegerField(choices=STATUS_CODES)
    
    issue = models.ForeignKey('Issue', related_name='statuses')

    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_status_display()

    def save(self, *args, **kwargs):
        print "Save IssueStatus"
        ret = super(IssueStatus, self).save(*args, **kwargs)

        i = self.issue
        i.current_status = self
        print "New issue.current_status: %s" % i.current_status.pk
        i.save()

        return ret
    

class Category(models.Model):
    """
    Table of available issue categories
    """
    name = models.CharField(max_length=50, unique=True)

    #Bookkeeping
    created = models.DateTimeField(default=datetime.datetime.utcnow().replace(tzinfo=utc))
    last_modified = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
