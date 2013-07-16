from django.dispatch import receiver
from django.db.models import signals
import notification.models as notification

@receiver(signals.post_syncdb, sender=notification)
def init_data(sender, **kwargs):
    print "Initializing notifications ..."
    notification.NoticeType.create("hello_world", "Hello World!", "It's me, Django-notifications")
