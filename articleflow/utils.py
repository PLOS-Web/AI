import csv

from articleflow.models import Article
from errors.models import ErrorSet

from django.db.models import Q

def issues_errors_csv(out_filename):
    #arts = Article.objects.filter(Q(current_state__unique_name='needs_web_corrections_cw')|Q(current_state__unique_name='needs_web_corrections_merops'))
    arts = Article.objects.filter(Q(current_state__unique_name='needs_web_corrections_cw'))
    
    csv_rows = []
    for art in arts.all():
        issues = art.issues
        for i in issues.all():
            csv_cols = [art.doi, i.category.name, i.description]
            csv_rows += [csv_cols]
        errorsets = ErrorSet.objects.filter(article=art)
        if errorsets:
            latest_errorset = errorsets.latest('created')
            for e in latest_errorset.errors.all():
                csv_cols = [art.doi, 'Error', e.message]
                csv_rows += [csv_cols]
    
    f = open(out_filename, 'wb')
    writer = csv.writer(f)
    writer.writerows(csv_rows)
    f.close()
    
    return csv_rows
        
