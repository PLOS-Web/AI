from django.dispatch import receiver
from django.db.models import signals
import notification.models as notification
from articleflow.notification_setup import create_notification_types

@receiver(signals.post_syncdb, sender=notification)
def init_data(sender, **kwargs):
    create_notification_types()
    
