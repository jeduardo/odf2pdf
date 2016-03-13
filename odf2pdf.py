__author__ = 'jeduardo'

import os
import sys
import logging
import tempfile

from flask import Flask, jsonify, make_response, request, send_file, after_this_request
from libreoffice import LibreOffice
from threading import Lock

# Application configuration
REQUEST_CHUNK_SIZE = 4096
LIBREOFFICE_BACKENDS_PER_HANDLER = 10

VALID_MIME_TYPES = {
    'application/vnd.oasis.opendocument.text': 'odt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    # Leaving this all here for future support
    # 'application/vnd.oasis.opendocument.text-template': 'ott',
    # 'application/vnd.oasis.opendocument.text-web': 'oth',
    # 'application/vnd.oasis.opendocument.text-master': 'odm',
    # 'application/vnd.oasis.opendocument.graphics': 'odg',
    # 'application/vnd.oasis.opendocument.graphics-template':'otg',
    # 'application/vnd.oasis.opendocument.presentation': 'odp',
    # 'application/vnd.oasis.opendocument.presentation-template': 'otp',
    # 'application/vnd.oasis.opendocument.spreadsheet': 'ods',
    # 'application/vnd.oasis.opendocument.spreadsheet-template': 'ots',
    # 'application/vnd.oasis.opendocument.chart': 'odc',
    # 'application/vnd.oasis.opendocument.formula': 'odf',
    # 'application/vnd.oasis.opendocument.database': 'odb',
    # 'application/vnd.oasis.opendocument.image': 'odi',
    # 'application/vnd.openofficeorg.extension': 'oxt'
}

# Configuring application logger
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)
#handler = logging.StreamHandler(sys.stdout)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)
#  logger.addHandler(handler)

# Instantiating application
app = Flask(__name__)

class Backend:
    def __init__(self):
        # Instantiating Libre Office connection
        self.backends = []
        for i in range(0, LIBREOFFICE_BACKENDS_PER_HANDLER):
            logger.debug("Instantiating LibreOffice backend %d" % (i + 1))
            self.backends.append(LibreOffice())
        logger.info("%d LibreOffice backends instantiated" % LIBREOFFICE_BACKENDS_PER_HANDLER)

        for backend in self.backends:
            logger.debug(backend)
        self.current = 0
        self.lock = Lock()

    def next(self):
        try:
            self.lock.acquire()
            current = self.current
            if current >= len(self.backends):
                current = 0
            backend = self.backends[current]
            self.current = current + 1
            logger.debug("Returning backend %d (%s)" % (current, backend))
            return backend
        finally:
            self.lock.release()

backend = Backend()

@app.route('/api/v1/pdf', methods = ['POST'])
def convert():
    content_type = request.headers.get('Content-type')
    if content_type not in VALID_MIME_TYPES:
        error = "%s: format not supported" % content_type
        logger.debug(error)
        return make_response(jsonify({'error': error}), 415)
    else:
        suffix = VALID_MIME_TYPES[content_type]

    content_length = int(request.headers.get('Content-length'))
    if content_length == 0:
        error = "request data has zero length"
        return make_response(jsonify({'error': error}), 411)

    # All good, let's convert the file
    logger.debug("Received request for content %s of size %d. Suffix is %s" % (content_type, content_length, suffix))
    with tempfile.NamedTemporaryFile(suffix = '.' + suffix, delete = False) as tmp:
        # Saving request to file
        saved = 0
        while True:
            logger.debug("Saved %d of %d" % (saved, content_length))
            chunk = request.stream.read(REQUEST_CHUNK_SIZE)
            saved += len(chunk)
            if len(chunk) == 0:
                break
            tmp.write(chunk)
        logger.debug("Content written to %s" % tmp.name)
        # File has to be closed otherwise LibreOffice cannot convert it.
        # It also cannot be deleted otherwise LibreOffice cannot find it.
        tmp.close()

        res = tmp.name.replace("." + suffix, ".pdf")
        logger.debug("Converting %s to %s" % (tmp.name, res))
        service = backend.next()
        if service.convertFile(suffix, "pdf", tmp.name):
            logger.debug("Sending file %s back to caller" % res)
            return send_file(res)
        else:
            # TODO: this is definitely not safe or accurate
            error = "Error converting file: %s" % service.lastError
            logger.error(error)
            return make_response(jsonify({'error': error}), 500)

if __name__ == '__main__':
    app.run(debug = False, port = 4000)