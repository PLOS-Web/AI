import os.path
import datetime
import re

from articleflow.models import Article, ArticleState, State, Typesetter, WatchState
from ai import settings
import manuscript_extractor as man_e

import logging
logger = logging.getLogger(__name__)

RE_SHORT_DOI_PATTERN = "[a-z]*\.[0-9]*"

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
    logger.info("Checking for new files in %s matching %s" % (path, filename_regex_prog.pattern))
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
    for f, m_time in files:
        logger.info("Found new file: %s" % f)
        trigger_func(f)
        if ws.gt_last_mtime(m_time):
            ws.update_last_mtime(m_time)

def watch_docs_from_aries():
    def process_doc_from_aries(f):
        # add article to AI
        #   extract doi from go.xml
        si_guid = 'blahblah filler'
        doi = PlosDoi(man_e.doi(f)).short
        logger.debug("Identified new aries-merops delivery as %s" % doi)
        #doi = 'pone.00000001'

        art, new = Article.objects.get_or_create(doi=doi)
        art.typesetter = Typesetter.objects.get(name='Merops')
        art.si_guid = si_guid

        art.save()
        delivery_state = State.objects.get(unique_name='delivered_from_aries')
        art_s = ArticleState(article=art, state=delivery_state)
        art_s.save()
        # extract manuscript, rename to doi.doc
        # move manuscript to hopper
        queue_doc_meropsing('TODO', art)
                
    ws, new = WatchState.objects.get_or_create(watcher="merops_aries_delivery")
    if new:
        ws.save()
    zip_prog = re.compile('.*\.zip$')
    scan_directory_for_changes(ws, process_doc_from_aries, settings.MEROPS_ARIES_DELIVERY, zip_prog)

def queue_doc_meropsing(doc, article):
    """Move a document into the queue for meropsing
    :param doc: filepath to document that oughta be moved.
    :param article: :class:`Article` object corresponding to the article being moved.
    """     
    # TODO plop file in queue
    logger.debug("Moving %s into meropsing queue" % article.doi)

    # update article status
    meropsed_queued_state = State.objects.get(unique_name="queued_for_meropsing")
    art_s = ArticleState(article=article, state=meropsed_queued_state)
    art_s.save()

def watch_merops_output():
    def process_doc_from_merops(f):
        # Identify article
        filename = os.path.basename(f)
        logger.debug("Filename: %s" % filename)
        doi_sre_match = re.match(RE_SHORT_DOI_PATTERN, filename)
        if not doi_sre_match:
            raise TypeError("Can't figure out doi from filename: %s" % filename)
        doi = doi_sre_match.group()
        logger.debug("Found doi from filename: %s" % doi)

        # Update status in AI
        art, new = Article.objects.get_or_create(doi=doi)
        if new:
            art.typesetter = Typesetter.objects.get(name='Merops')
            art.save()
        merops_output_state = State.objects.get(unique_name="meropsed")
        art_s = ArticleState(article=art, state=merops_output_state)
        art_s.save()

    ws, new = WatchState.objects.get_or_create(watcher="merops_meropsed_out")
    if new:
        ws.save()
    meropsed_doc_prog = re.compile(RE_SHORT_DOI_PATTERN + '\.doc$')
    scan_directory_for_changes(ws, process_doc_from_merops, settings.MEROPS_MEROPSED_OUTPUT, meropsed_doc_prog)

def move_to_pm():
    meropsed_articles = Article.objects.filter(current_state__unique_name="meropsed")

    pm_state = State.objects.get(unique_name="prepare_manuscript")
    for a in meropsed_articles:
        art_s = ArticleState(article=a, state=pm_state)
        art_s.save()

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
    art_s.save()

def watch_finishxml_output():
    def process_doc_from_merops(f):
        # Identify article
        filename = os.path.basename(f)
        logger.debug("Filename: %s" % filename)
        doi_sre_match = re.match(RE_SHORT_DOI_PATTERN, filename)
        if not doi_sre_match:
            raise TypeError("Can't figure out doi from filename: %s" % filename)
        doi = doi_sre_match.group()
        logger.debug("Found doi from filename: %s" % doi)

        # Update status in AI
        art, new = Article.objects.get_or_create(doi=doi)
        if new:
            art.typesetter = Typesetter.objects.get(name='Merops')
            art.save()
        finish_output_state = State.objects.get(unique_name="finish_out")
        art_s = ArticleState(article=art, state=finish_output_state)
        art_s.save()

    ws, new = WatchState.objects.get_or_create(watcher="merops_finish_out")
    if new:
        ws.save()
    finished_xml_prog = re.compile(RE_SHORT_DOI_PATTERN + '\.xml$')
    scan_directory_for_changes(ws, process_doc_from_merops, settings.MEROPS_FINISH_XML_OUTPUT, finished_xml_prog)
