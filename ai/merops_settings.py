import os.path

MEROPS_ARIES_DELIVERY = os.path.abspath("/var/spool/delivery/merops/aries-delivery")

MEROPS_MEROPSED_WATCH = os.path.abspath("/var/spool/delivery/merops/merops/watch/")
MEROPS_MEROPSED_OUTPUT = os.path.abspath("/var/spool/delivery/merops/merops/out/")
MEROPS_FINISH_XML_WATCH = os.path.abspath("/var/spool/delivery/merops/finish/watch/")
MEROPS_FINISH_XML_OUTPUT = os.path.abspath("/var/spool/delivery/merops/finish/out/"
)

MEROPS_MANUSCRIPT_EXTRACTION = os.path.abspath("/tmp/merops/manuscript-extraction/")

MEROPS_FILE_SCHEMA = {
    'meropsed.doc': {
        'dir_path': MEROPS_MEROPSED_OUTPUT,
        'filename_modifier': '',
        'file_extension': 'doc',
        },
    'meropsed-original.doc': {
        'dir_path': MEROPS_MEROPSED_OUTPUT,
        'filename_modifier': '-original',
        'file_extension': 'doc',
        },
    'meropsed-original.xml': {
        'dir_path': MEROPS_MEROPSED_OUTPUT,
        'filename_modifier': '',
        'file_extension': 'xml',
        },
    'finishxml.doc': {
        'dir_path': MEROPS_FINISH_XML_OUTPUT,
        'filename_modifier': '-finishxmlcheck-original',
        'file_extension': 'doc',
        },
    'finishxml-original.doc': {
        'dir_path': MEROPS_FINISH_XML_OUTPUT,
        'filename_modifier': '-finishxmlcheck-original',
        'file_extension': 'doc',
        },
    'finishxml.xml': {
        'dir_path': MEROPS_FINISH_XML_OUTPUT,
        'filename_modifier': '',
        'file_extension': 'xml',
        },
    }
