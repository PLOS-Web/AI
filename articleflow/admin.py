from django.contrib import admin
from articleflow.models import *

admin.site.register(State)
admin.site.register(ArticleState)
admin.site.register(Article)
admin.site.register(Transition)
admin.site.register(Journal)
admin.site.register(ArticleExtras)

