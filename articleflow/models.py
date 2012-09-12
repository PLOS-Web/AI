from django.db import models

class state(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class article(models.Model):
    doi = models.CharField(max_length=50)
    article_state = models.ForeignKey(article_state)

    def __unicode__(self):
        return self.doi
    
class article_state(models.Model):
    article = models.ForeignKey(article)
    state = models.ForeignKey(state)
    
    

