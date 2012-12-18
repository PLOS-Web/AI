from django.contrib import admin
from errors.models import *

admin.site.register(Error)
admin.site.register(ErrorStatus)
admin.site.register(ErrorSet)
