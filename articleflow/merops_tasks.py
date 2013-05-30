import os.path
import datetime
import re

from articleflow.models import Article, ArticleState, State, Typesetter, WatchState
from ai import settings

import logging
logger = logging.getLogger(__name__)

def _get_mtime(file):
    return datetime.datetime.fromtimestamp(os.stat(file).st_mtime)

def _get_filenames_and_mtime_in_dir(path, filename_regex_prog=None):
    print "PATH %s" % path
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
        doi = 'pone.00000001'

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
    raise NotImplementedError

def queue_doc_finishxml():
    raise NotImplementedError

def watch_finishxml_output():
    raise NotImplementedError


