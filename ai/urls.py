from django.conf.urls import patterns, include, url
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {
            "template": "homepage.html",
            }, name="home"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('articleflow.urls')),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="auth_login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name="auth_logout"),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^issues/', include('issues.urls')),
)
