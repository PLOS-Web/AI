from django.contrib import admin
from articleflow.models import *

admin.site.register(State)
admin.site.register(ArticleState)
admin.site.register(Article)
admin.site.register(StateTransition)
admin.site.register(Transition)
