from subprocess import call
import os.path
import shutil
import datetime
import re
import zipfile


from django.db.models import Q
from django.utils.timezone import utc, localtime

from articleflow.models import Article, ArticleState, State, Typesetter, WatchState
from ai import settings
import articleflow.manuscript_extractor as man_e

from celery.task import task
from celery.utils.log import get_task_logger
celery_logger = get_task_logger(__name__) 

import logging
logger = logging.getLogger(__name__)
print __name__

RE_SHORT_DOI_PATTERN = "[a-z]*\.[0-9]*"

def make_articlestate_if_new(articlestate):
    if articlestate.article.current_state == articlestate.state:
        return False
    articlestate.save()
    return True

class PlosDoi(object):

    def __init__(self, doi_str):
        self._pub_prefix = "10.1371/journal."

        short_form_match = re.compile(RE_SHORT_DOI_PATTERN)
        #long_form_match = re.compile('^(?<=10\.1371/journal\.)%s$' % RE_SHORT_DOI_PATTERN)
        long_form_match = re.compile('(?<=10\.1371/journal\.)%s' % RE_SHORT_DOI_PATTERN)
        ambra_doi_match = re.compile('^(?<=info\:doi/10\.1371/journal\.)%s$' % RE_SHORT_DOI_PATTERN)

        if short_form_match.match(doi_str):
            self._short_doi = doi_str
            logger.debug("Parsing short form doi: %s" % doi_str)
        elif long_form_match.search(doi_str):
            self._short_doi = long_form_match.search(doi_str).group()
            logger.debug("Parsing long form doi: %s" % doi_str)
        elif ambra_doi_match.search(doi_str):
            self._short_doi = ambra_doi_match.search(doi_str).group()
            logger.debug("Parsing ambra-style doi: %s" % doi_str)
        else:
            raise ValueError("Couldn't parse doi %s" % doi_str)

        logger.debug("Constructed Doi object with shortform doi: %s" % self._short_doi)

    @property
    def short(self):
        return self._short_doi

    @property
    def long(self):
        return "%s%s" % (self._pub_prefix, self._short_doi)

def _get_mtime(file):
    return datetime.datetime.fromtimestamp(os.stat(file).st_mtime)

def _get_filenames_and_mtime_in_dir(path, filename_regex_prog=None):
    logger.debug("Checking for new files in %s matching %s" % (path, filename_regex_prog.pattern))
    files = [ (os.path.join(path, f), _get_mtime(os.path.join(path, f))) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    if filename_regex_prog:
        files = filter(lambda x: filename_regex_prog.match(os.path.basename(x[0])), files)
    return files


def scan_directory_for_changes(ws, trigger_func, directory, filename_regex_prog=None):
    """make one scan of a directory for all newly modified files.
    saves last mtime to database using a WatchState object.
    :param ws: :class:`WatchState` object
    :param trigger_func: a function to be executed on each new file
    :param directory: directory path to scan
    """
    try:
        files = _get_filenames_and_mtime_in_dir(directory, filename_regex_prog)
    except OSError, e:
        logger.error(e)
        raise
    files = filter(lambda x: ws.gt_last_mtime(x[1]),files)
    files = sorted(files, key=lambda f: f[1])
    try:
        for f, m_time in files:
            logger.info("Found new file: %s" % f)
            trigger_func(f)
            if ws.gt_last_mtime(m_time):
                logger.debug("Updating watchstate last m_time to %s" % m_time)
                ws.update_last_mtime(m_time)
    except Exception, e:
        logger.error(str(e))

def queue_doc_meropsing(article, doc=None):
    """Move a document into the queue for meropsing
    :param doc: filepath to document that oughta be moved.
    :param article: :class:`Article` object corresponding to the article being moved.
    """     
    # TODO move file into queue if specified
    if doc:
        filename, extension = os.path.splitext(doc)
        new_filename = os.path.join(settings.MEROPS_MEROPSED_WATCH, "%s%s" % (article.doi, extension))
        logger.info("%s: copying %s into meropsing queue, %s  " % (article.doi, doc, new_filename))
        shutil.copy(doc, new_filename)

    # update article status
    meropsed_queued_state = State.objects.get(unique_name="queued_for_meropsing")
    art_s = ArticleState(article=article, state=meropsed_queued_state)
    make_articlestate_if_new(art_s)

def queue_doc_finishxml(doc, article):
    """Move a document into the queue for finishxml
    :param doc: filepath to document that oughta be moved.
    :param article: :class:`Article` object corresponding to the article being moved.
    """     
    # TODO plop file in queue
    logger.debug("Moving %s into finish queue" % article.doi)

    # update article status
    finish_queued_state = State.objects.get(unique_name="queued_for_finish")
    art_s = ArticleState(article=article, state=finish_queued_state)
    make_articlestate_if_new(art_s)

def process_doc_from_aries(f):
    # add article to AI
    #   extract doi from go.xml
    si_guid = os.path.basename(f).split('.zip')[0]
    doi = PlosDoi(man_e.doi(f)).short
    logger.info("Identified new aries-merops delivery {guid: %s} as %s" % (si_guid,doi))
    celery_logger.info("watch_docs_from_aries identified new file for %s" % doi)

    art, new = Article.objects.get_or_create(doi=doi)
    art.typesetter = Typesetter.objects.get(name='Merops')
    art.si_guid = si_guid

    art.save()
    delivery_state = State.objects.get(unique_name='delivered_from_aries')
    art_s = ArticleState(article=art, state=delivery_state)
    make_articlestate_if_new(art_s)

    # extract manuscript, rename to doi.doc(x)
    try:
        manuscript_name = man_e.manuscript(f)
        z = zipfile.ZipFile(f)
        z.extract(manuscript_name, settings.MEROPS_MANUSCRIPT_EXTRACTION)
        logger.info("Extracting manuscript file, %s, to %s" % (manuscript_name, settings.MEROPS_MANUSCRIPT_EXTRACTION))
        z.close()
        man_f = os.path.join(settings.MEROPS_MANUSCRIPT_EXTRACTION, manuscript_name)
        queue_doc_meropsing(art, man_f)
    except man_e.ManuscriptExtractionException, e:
        logger.error(str(e))

@task
def watch_docs_from_aries():
    celery_logger.info("Initiating watch_docs_from_aries")
    ws, new = WatchState.objects.get_or_create(watcher="merops_aries_delivery")
    if new:
        ws.save()
    zip_prog = re.compile('.*\.zip$')
    scan_directory_for_changes(ws, process_doc_from_aries, settings.MEROPS_ARIES_DELIVERY, zip_prog)

@task
def watch_merops_output():
    def process_doc_from_merops(f):
        # Identify article
        filename = os.path.basename(f)
        doi_sre_match = re.match(RE_SHORT_DOI_PATTERN, filename)
        if not doi_sre_match:
            raise TypeError("Can't figure out doi from filename: %s" % filename)
        doi = doi_sre_match.group()
        logger.info("Found doi from filename: %s" % doi)
        celery_logger.info("watch_merops_output identified new file for %s" % doi)

        # Update status in AI
        art, new = Article.objects.get_or_create(doi=doi)
        if new:
            art.typesetter = Typesetter.objects.get(name='Merops')
            art.save()
        merops_output_state = State.objects.get(unique_name="meropsed")
        art_s = ArticleState(article=art, state=merops_output_state)
        make_articlestate_if_new(art_s)

    celery_logger.info("Initiating watch_merops_output")
    ws, new = WatchState.objects.get_or_create(watcher="merops_meropsed_out")
    if new:
        ws.save()
    meropsed_doc_prog = re.compile(RE_SHORT_DOI_PATTERN + '.*\.xml')
    scan_directory_for_changes(ws, process_doc_from_merops, settings.MEROPS_MEROPSED_OUTPUT, meropsed_doc_prog)

@task
def move_to_pm():
    meropsed_articles = Article.objects.filter(current_state__unique_name="meropsed")

    pm_state = State.objects.get(unique_name="prepare_manuscript")
    for a in meropsed_articles:
        art_s = ArticleState(article=a, state=pm_state)
        make_articlestate_if_new(art_s)

@task
def watch_finishxml_output():
    def process_doc_from_merops(f):
        # Identify article
        filename = os.path.basename(f)
        doi_sre_match = re.match(RE_SHORT_DOI_PATTERN, filename)
        if not doi_sre_match:
            raise TypeError("Can't figure out doi from filename: %s" % filename)
        doi = doi_sre_match.group()
        logger.info("Found doi from filename: %s" % doi)
        celery_logger.info("watch_finishxml_output identified new file for %s" % doi)

        # Update status in AI
        art, new = Article.objects.get_or_create(doi=doi)
        if new:
            art.typesetter = Typesetter.objects.get(name='Merops')
            art.save()
        finish_output_state = State.objects.get(unique_name="finish_out")
        art_s = ArticleState(article=art, state=finish_output_state)
        make_articlestate_if_new(art_s)
        #move immediately into ready to build article package
        ready_state = State.objects.get(unique_name="ready_to_build_article_package")
        art_s = ArticleState(article=art, state=ready_state)
        make_articlestate_if_new(art_s)

    celery_logger.info("Initiating watch_finishxml_output")
    ws, new = WatchState.objects.get_or_create(watcher="merops_finish_out")
    if new:
        ws.save()
    finished_xml_prog = re.compile(RE_SHORT_DOI_PATTERN + '.*\.xml$')
    scan_directory_for_changes(ws, process_doc_from_merops, settings.MEROPS_FINISH_XML_OUTPUT, finished_xml_prog)

@task
def watch_stuck_queue():
    celery_logger.info("Initiating watch_stuck_queue . . .")
    stale_threshold = datetime.timedelta(hours=1)
    
    now = datetime.datetime.utcnow().replace(tzinfo=utc)

    stale_articles = Article.objects.filter(\
        Q(current_articlestate__state__unique_name='queued_for_meropsing')|Q(current_articlestate__state__unique_name='queued_for_finish')).filter(created__lte=now - stale_threshold)

    print stale_articles.count()

    if stale_articles:
        a_string = ""
        #for a in stale_articles.all():
        #    a_string += "%s: %s since %s<br \>" % (a.doi, a.current_articlestate.state, localtime(a.current_articlestate.created))
        
        celery_logger.error("%s article(s) are currently stuck in a merops queued state" % stale_articles.count())
     
@task
def build_merops_packages():
    ariesPullMerops = os.path.abspath('/var/local/scripts/production/ariesPullMerops')
    ingest = os.path.abspath('/var/local/scripts/production/ingest')
    ingestion_queue = os.path.abspath('/var/spool/ambra/ingestion-queue/')

    articles_ready = Article.objects.filter(current_state__unique_name="ready_to_build_article_package").all()
    ingested_state = State.objects.get(unique_name='ingested')
    for a in articles_ready:
        logger.info("%s: attempting to ariesPullMerops ..." % a.doi)
        try:
            call([ariesPullMerops, a.doi], cwd=ingestion_queue)
            # if first revision, ingest
            ingest_arts = ArticleState.objects.filter(article=a, state=ingested_state).all()
            if not ingest_arts:
                logger.info("%s: first revision identified, attempting to ingest ..." % a.doi)
                call([ingest, a.doi], cwd=ingestion_queue)
        except OSError, ee:
            logger.exception(ee)
        except Exception, ee:
            logger.exception(ee)

@task
def test_task():
    print "*** AM I WORKING? ***"
    logger.info("TEST TASK")
    celery_logger.info("TEST TASK")
