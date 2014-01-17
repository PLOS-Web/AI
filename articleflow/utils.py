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
        
def errors_pubdate_csv(out_filename, pubdate):
    #arts = Article.objects.filter(Q(current_state__unique_name='needs_web_corrections_cw')|Q(current_state__unique_name='needs_web_corrections_merops'))
    arts = Article.objects.filter(pubdate=pubdate)
    
    csv_rows = []
    key = ["DOI",
           "Errorset #",
           "Errorset source",
           "Pubdate",
           "Error Type",
           "Error Message",
           "Typesetter"]
    csv_rows += [key] 
    for art in arts.order_by('doi').all():
        errorsets = ErrorSet.objects.filter(article=art).order_by('created')
        for i, errorset in enumerate(errorsets):
            for e in errorset.errors.order_by('level', 'message').all():
                csv_cols = [art.doi,
                            i + 1,
                            errorset.get_source_display(),
                            str(art.pubdate),
                            e.get_level_display(),
                            e.message,
                            art.typesetter.name]
                csv_rows += [csv_cols]
    
    f = open(out_filename, 'wb')
    writer = csv.writer(f)
    writer.writerows(csv_rows)
    f.close()
