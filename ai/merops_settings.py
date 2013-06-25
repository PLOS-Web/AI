import os.path

MEROPS_ARIES_DELIVERY = os.path.abspath("/var/spool/delivery/merops/aries-delivery")

MEROPS_MEROPSED_WATCH = os.path.abspath("/var/spool/delivery/merops/merops/watch/")
MEROPS_MEROPSED_WATCH_BU = os.path.abspath("/var/spool/delivery/merops/merops/watch-bu/")
MEROPS_MEROPSED_OUTPUT = os.path.abspath("/var/spool/delivery/merops/merops/out/")
MEROPS_FINISH_XML_WATCH = os.path.abspath("/var/spool/delivery/merops/finish/watch/")
MEROPS_FINISH_XML_WATCH_BU = os.path.abspath("/var/spool/delivery/merops/finish/watch-bu/")
MEROPS_FINISH_XML_OUTPUT = os.path.abspath("/var/spool/delivery/merops/finish/out/"
)

MEROPS_MANUSCRIPT_EXTRACTION = os.path.abspath("/tmp/merops/manuscript-extraction/")

MEROPS_FILE_SCHEMA = {
    'meropsed.doc': {
        'dir_path': MEROPS_MEROPSED_OUTPUT,
        'filename_modifier': '',
        'file_extension': 'doc*',
        },
    'meropsed-original.doc': {
        'dir_path': MEROPS_MEROPSED_OUTPUT,
        'filename_modifier': '-Original',
        'file_extension': 'doc*',
        },
    'meropsed.xml': {
        'dir_path': MEROPS_MEROPSED_OUTPUT,
        'filename_modifier': '',
        'file_extension': 'xml',
        },
    'finishxml.doc': {
        'dir_path': MEROPS_FINISH_XML_OUTPUT,
        'filename_modifier': '-FinishXMLCheck',
        'file_extension': 'doc*',
        },
    'finishxml-original.doc': {
        'dir_path': MEROPS_FINISH_XML_OUTPUT,
        'filename_modifier': '-FinishXMLCheck-Original',
        'file_extension': 'doc*',
        },
    'finishxml.xml': {
        'dir_path': MEROPS_FINISH_XML_OUTPUT,
        'filename_modifier': '',
        'file_extension': 'xml',
        },
    }
