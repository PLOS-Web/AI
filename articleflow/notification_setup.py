import notification.models as notification

def create_notification_types(verbosity=2):
    print "Initializing notifications ..."

    notification.NoticeType.create(\
        label="new_urgent_web_correction",
        display="New Urgent Web Corrections",
        description="New article needing urgent web corrections",
        default=2,
        verbosity=verbosity)

    notification.NoticeType.create(\
        label="sent_back_to_production",
        display="Sent back to production",
        description="An article was sent back to production",
        default=2,
        verbosity=verbosity)



