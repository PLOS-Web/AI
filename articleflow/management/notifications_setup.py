from django.dispatch import receiver
from django.db.models import signals
import notification.models as notification

@receiver(signals.post_syncdb, sender=notification)
def init_data(sender, **kwargs):
    print "Initializing notifications ..."
    n = notification.NoticeType(\
        label="hello_world",
        display="Hello World!",
        description="It's me, Django-notifications",
        default=2)
    n.save()
