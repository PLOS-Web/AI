import os.path
from articleflow.models import WatchState


def _get_filenames_and_mtime_in_dir(path):
    return [ (os.path.join(path, f), get_mtime(os.path.join(path, f))) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]


# TODO make default here a get or create
def scan_directory_for_changes(trigger_func, directory, w_s=WatchState(watcher="scan_directory_for_changes")):
    files = _get_filenames_and_mtime_in_dir(directory)
    files = filter(w_s.gt_last_mtime,files)
    files = sorted(files, key=lambda f: f[1])
    for f, m_time in files:
        if m_time > cutoff_cursor:
            trigger_func(f)
            if w_s.gt_last_mtime(m_time):
                w_s.update_last_mtime(m_time)

def watch_docs_from_aries(watch_directory):
    raise NotImplementedError

def queue_doc_meropsing():
    raise NotImplementedError

def watch_merops_output():
    raise NotImplementedError

def queue_doc_finishxml():
    raise NotImplementedError

def watch_finishxml_output():
    raise NotImplementedError


