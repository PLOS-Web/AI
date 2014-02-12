from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from articleflow.views import *
from errors.views import Errors

urlpatterns = patterns('articleflow.views',
                       url(r'^grid/search/$', ArticleGridSearch.as_view(), name='grid_search'),
                       url(r'^grid/$', ArticleGrid.as_view(), name='grid'),
                       url(r'^detail/(?P<doi>.*)/$', ArticleDetailMain.as_view(), name='detail_main'),
                       url(r'^detail/(?P<doi>.*)/transitions$', ArticleDetailTransition.as_view(), name='detail_transition'),
                       url(r'^detail/(?P<doi>.*)/transitions/upload$', ArticleDetailTransitionUpload.as_view(), name='detail_transition_upload'),
                       url(r'^detail/(?P<doi>.*)/lala', ArticleDetailTransitionPanel.as_view(), name='transitions_panel'),
                       url(r'^detail/(?P<doi>.*)/issues', ArticleDetailIssues.as_view(), name='detail_issues'),
                       url(r'^detail/(?P<doi>.*)/errors', Errors.as_view(), name='detail_errors'),
                       url(r'^detail/(?P<doi>.*)/history', ArticleDetailHistory.as_view(), name='detail_history'),
                       url(r'^help/', Help.as_view(), name='help'),
                       url(r'^api/', include('articleflow.api_urls')),
                       url(r'^detail/(?P<doi>.*)/assign-to-me', AssignToMe.as_view(), name='assign_to_me'),
                       url(r'^detail/(?P<doi>.*)/assign-article', AssignArticle.as_view(), name='assign_article'),
                       url(r'^assign_weights/(?P<state_pk>[0-9]*)/$', AssignRatios.as_view(), name='assign_weight_detail'),
                       url(r'^assign_weights/$', AssignRatiosMain.as_view(), name='assign_weight_main'),
                       url(r'^reports/', include('articleflow.reports_urls')),
                       #url(r'^sftp-serve-down/(?P<doi>.*)$', FTPMeropsdOrig.as_view(), name='sftp_serve_down'),
                       #url(r'^sftp_test_upload/$', FTPMeropsUpload.as_view(), name='sftp_test_upload'),                       
                       url(r'^detail/(?P<doi>.*)/merops_files/(?P<file_type>.*)$', ServeArticleDoc.as_view(), name='merops_files'),
                       url(r'^detail/(?P<doi>.*)/corrections_file$', HandleCorrectionsDoc.as_view(), name='corrections_file'),
                       url(r'^detail/(?P<doi>.*)/corrections_control$', CorrectionsControl.as_view(), name='corrections_control'),
                       )

