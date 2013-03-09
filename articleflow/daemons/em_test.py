from celery import task
import pyodbc

from django.settings import EM_DATABASE

@task()
def em_test(lastname):
    cnx_settings = 'DRIVER={SQL Server};SERVER=%(HOST)s;DATABASE=%(NAME)s;UID=%(user)s;PWD=%(PASSWORD)s' % EM_DATABASE

    cnxn = pyodbc.connect(cnx_settings)
    cursor = cnxn.cursor()
    cursor.execute("select top(1) lastname from people where lastname like '%s'" % lastname)
    rows = cursor.fetchall()
    return rows
    #for row in rows:
    #    print row.lastname

