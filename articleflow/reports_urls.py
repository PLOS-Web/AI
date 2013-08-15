from django.conf.urls import patterns, include, url
from articleflow.views import *

urlpatterns = patterns('articleflow.views',
                       url(r'^$', ReportsMain.as_view(), name='reports_main'),
                       url(r'^pc_qc_counts/$', ReportsPCQCCounts.as_view(), name='reports_pc_qc_counts'),
                       url(r'^qa_automation_performance/$', ReportMeropsCounts.as_view(), name='reports_merops_counts'),
                       )
