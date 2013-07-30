from django.contrib.sites.models import Site

from django.conf import settings

def site_domain(request):
    print "lalala"
    return {
        'site_domain': Site.objects.get(pk=settings.SITE_ID).domain,
        }
