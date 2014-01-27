from django.conf.urls.defaults import *

from notification.views import Notices, NoticeCount, mark_all_seen, single

urlpatterns = patterns('',
    url(r'^$', Notices.as_view(), name="notification_notices"),
    url(r'^notice_unseen_count/$', NoticeCount.as_view(), name="notice_unseen_count"),
    url(r'^(\d+)/$', single, name="notification_notice"),
    url(r'^mark_all_seen/$', mark_all_seen, name="notification_mark_all_seen"),
)
