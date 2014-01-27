from django.views.generic.base import View
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


from notification.models import *
from notification.decorators import basic_auth_required, simple_basic_auth_callback

@login_required
def settings(request):
    settings_table = []
    for notice_type in NoticeType.objects.all():
        settings_row = []
        for medium_id, medium_display in NOTICE_MEDIA:
            form_label = "%s_%s" % (notice_type.label, medium_id)
            setting = get_notification_setting(request.user, notice_type, medium_id)
            if request.method == "POST":
                if request.POST.get(form_label) == "on":
                    setting.send = True
                else:
                    setting.send = False
                setting.save()
            settings_row.append((form_label, setting.send))
        settings_table.append({"notice_type": notice_type, "cells": settings_row})
    
    notice_settings = {
        "column_headers": [medium_display for medium_id, medium_display in NOTICE_MEDIA],
        "rows": settings_table,
    }

class Notices(View):
    template_name = 'notification/notices.html'
    
    def get_context_data(self, request, *args, **kwargs):
        notice_types = NoticeType.objects.all()
        notices = Notice.objects.notices_for(request.user, on_site=True)
        
        return {
            'notices': notices,
            'notice_types':notice_types
            }

    def get_sync(self, request, *args, **kwargs):
        ctx = self.get_context_data(request, *args, **kwargs)
        return render_to_response(self.template_name, ctx, context_instance=RequestContext(request))

    def get_ajax(self, request, *args, **kwargs):
        ctx = self.get_context_data(request, *args, **kwargs)
        return HttpResponse(simplejson.dumps(ctx), mimetype='application/json')

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            return self.get_ajax(request, args, kwargs)
        return self.get_sync(request, args, kwargs)


class NoticeCount(View):
    def get_context_data(self, request, *args, **kwargs):
        return {
            'notice_unseen_count': Notice.objects.unseen_count_for(request.user, on_site=True)
            }

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        ctx = self.get_context_data(request, *args, **kwargs)
        if request.is_ajax():
            return HttpResponse(simplejson.dumps(ctx), mimetype='application/json')
        else:
            return HttpResponse(ctx['notice_unseen_count'])


@login_required
def notices(request):
    notice_types = NoticeType.objects.all()
    notices = Notice.objects.notices_for(request.user, on_site=True)
    
    return render_to_response("notification/notices.html", {
        "notices": notices,
        "notice_types": notice_types,
    }, context_instance=RequestContext(request))

@login_required
def single(request, id):
    notice = get_object_or_404(Notice, id=id)
    if request.user == notice.user:
        return render_to_response("notification/single.html", {
            "notice": notice,
        }, context_instance=RequestContext(request))
    raise Http404

@login_required
def archive(request, noticeid=None, next_page=None):
    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            if request.user == notice.user or request.user.is_superuser:
                notice.archive()
            else:   # you can archive other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)
    return HttpResponseRedirect(next_page)

@login_required
def delete(request, noticeid=None, next_page=None):
    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            if request.user == notice.user or request.user.is_superuser:
                notice.delete()
            else:   # you can delete other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)
    return HttpResponseRedirect(next_page)

@login_required
def mark_all_seen(request):
    Notice.objects.notices_for(request.user, unseen=True).update(unseen=False)
    return HttpResponseRedirect(reverse("notification_notices"))
    
