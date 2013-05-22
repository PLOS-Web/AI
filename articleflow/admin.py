from django.contrib import admin
from articleflow.models import *

class ArticleAdmin(admin.ModelAdmin):
    readonly_fields = ('current_state', 'current_articlestate', 'article_extras')
    fieldsets = [
        (None            , {'fields': ['doi', 'pubdate', 'journal']}),
        ('State Info'    , {'fields': ['current_state', 'current_articlestate']}),
        ('File Info'     , {'fields': ['si_guid', 'md5']}),
        ('EM info'       , {'fields': ['em_pk', 'em_ms_number', 'em_max_revision']}),
        ('Record Info'   , {'fields': ['created']}),
        ]

admin.site.register(State)
admin.site.register(ArticleState)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Transition)
admin.site.register(Journal)
admin.site.register(ArticleExtras)
admin.site.register(AssignmentHistory)
admin.site.register(AssignmentRatio)
admin.site.register(Typesetter)

