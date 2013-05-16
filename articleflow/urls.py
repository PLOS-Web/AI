from django.conf.urls import patterns, include, url
from articleflow.views import *
from errors.views import Errors

urlpatterns = patterns('articleflow.views',
                       url(r'^grid/$', ArticleGrid.as_view(), name='grid'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/$', ArticleDetailMain.as_view(), name='detail_main'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/transitions', ArticleDetailTransition.as_view(), name='detail_transition'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/issues', ArticleDetailIssues.as_view(), name='detail_issues'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/errors', Errors.as_view(), name='detail_errors'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/history', ArticleDetailHistory.as_view(), name='detail_history'),
                       url(r'^help/', Help.as_view(), name='help'),
                       url(r'^api/', include('articleflow.api_urls')),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/assign-to-me', AssignToMe.as_view(), name='assign_to_me'),
                       url(r'^assign_weights/(?P<state_pk>[0-9]*)/$', AssignRatios.as_view(), name='assign_weight_detail'),
                       url(r'^assign_weights/$', AssignRatiosMain.as_view(), name='assign_weight_main'),
                       url(r'^reports/', include('articleflow.reports_urls')),
                       url(r'^sftp-serve-down/(?P<doi>[a-z|\.|0-9]{0,50})$', FTPMeropsdOrig.as_view(), name='sftp_serve_down'),
                       url(r'^sftp_test_upload/$', FTPMeropsUpload.as_view(), name='sftp_test_upload'),                       
                       )

