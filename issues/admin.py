from django.contrib import admin
from issues.models import *

admin.site.register(Issue)
admin.site.register(Comment)
admin.site.register(Category)
