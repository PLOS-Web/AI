import MySQLdb

s_host = "sfo-db01.int.plos.org"
s_user = "article_tracker"
s_passwd = "pqeCKYxL"
s_db = "article_tracker"

class Migrate():
    
    def __init__(self):
        self.at_db = MySQLdb.connect(host= s_host,
                                     user=s_user,
                                     passwd=s_passwd,
                                     db=s_db)
        self.at_c = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

    def get_pull_dois(self):
        self.at_c.execute(
            """
            SELECT
              ap.doi as 'doi'
            FROM article_pulls as ap
            LIMIT 10;
            """)
        print self.at_c.fetchall()
    
if __name__ == '__main__':
    m = Migrate()
    m.get_pull_dois()

    
