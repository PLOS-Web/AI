import notification.models as notification

def create_notification_types(verbosity=2):
    print "Initializing notifications ..."

    notification.NoticeType.create(\
        label="new_urgent_qc",
        display="New Urgent QC",
        description="New article needing urgent QC",
        default=2,
        verbosity=verbosity)

