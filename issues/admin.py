from django.contrib import admin
from issues.models import *

admin.site.register(Issue)
admin.site.register(Category)
admin.site.register(IssueStatus)
