from django.db import models

class state(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class article_state(models.Model):
    article = models.ForeignKey('article', related_name='owning_article')
    state = models.ForeignKey('state')

class article(models.Model):
    doi = models.CharField(max_length=50)
    article_state = models.OneToOneField('article_state', related_name='current_state')

    def __unicode__(self):
        return self.doi

    
    

