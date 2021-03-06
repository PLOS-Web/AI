import MySQLdb
from ai import settings

def make_full_doi(doi):
    return "info:doi/10.1371/journal.%s" % doi

class MYSQLConnection(object):
    def __init__(self, host, user, password, port=3306, database=''):
        self.cnxn = MySQLdb.connect(host=host,
                                    port=port,
                                    user=user,
                                    passwd=password,
                                    db=database)
        self.c = self.cnxn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.c.close()

    def __del__(self):
        self.c.close()
        
class AmbraConnection(MYSQLConnection):
    def doi_ingested(self, doi):
        self.c.execute(
            """
            SELECT a.state
            FROM article a
            WHERE a.doi = %(doi)s
            """, {'doi': make_full_doi(doi)})

        r = self.c.fetchall()

        if len(r) == 0:
            return False
        if len(r) > 1:
            raise LookupError("Multiple entries found for DOI: %s" % doi)


        return (r[0]['state'] in (0, 1) )

    def doi_published(self, doi):
        self.c.execute(
            """
            SELECT a.state
            FROM article a
            WHERE a.doi = %(doi)s
            """, {'doi': make_full_doi(doi)})

        r = self.c.fetchall()

        if len(r) == 0:
            return False
        if len(r) > 1:
            raise LookupError("Multiple entries found for DOI: %s" % doi)


        return (r[0]['state'] == 0)

class AmbraStageConnection(AmbraConnection):
    def __init__(self):
        super(AmbraStageConnection, self).__init__(\
            host=settings.AMBRA_STAGE_DATABASE['HOST'],
            port=settings.AMBRA_STAGE_DATABASE['PORT'],
            user=settings.AMBRA_STAGE_DATABASE['USER'],
            password=settings.AMBRA_STAGE_DATABASE['PASSWORD'],
            database=settings.AMBRA_STAGE_DATABASE['NAME'])

class AmbraProdConnection(AmbraConnection):
    def __init__(self):
        super(AmbraProdConnection, self).__init__(\
            host=settings.AMBRA_PROD_DATABASE['HOST'],
            port=settings.AMBRA_PROD_DATABASE['PORT'],
            user=settings.AMBRA_PROD_DATABASE['USER'],
            password=settings.AMBRA_PROD_DATABASE['PASSWORD'],
            database=settings.AMBRA_PROD_DATABASE['NAME'])

def main():
    with AmbraStageConnection() as asc:
        pubbed = asc.doi_published('pone.0059827')
        print pubbed
        
if __name__ == '__main__':
    main()
