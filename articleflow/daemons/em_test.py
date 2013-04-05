from celery import task
import pyodbc

from ai import settings

@task()
def em_test(lastname):
    em_pone = settings.EM_REPORTING_DATABASE
    em_pone.update({'NAME': 'pone'})

    cnx_settings = 'DRIVER={freeTDS};SERVER=%(HOST)s;PORT=%(PORT)d;DATABASE=%(NAME)s;UID=%(USER)s;PWD=%(PASSWORD)s;TDS_VERSION=8.0' % em_pone

    cnxn = pyodbc.connect(cnx_settings)
    cursor = cnxn.cursor()
    
    cursor.execute("select top(1) lastname, firstname from people where lastname like '%s'" % lastname)
    rows = cursor.fetchall()
    return rows
    #for row in rows:
    #    print row.lastname

