__author__ = 'jeduardo'

import os
import sys
import logging
import tempfile

from flask import Flask, jsonify, make_response, request, send_file, after_this_request
from libreoffice import LibreOffice

# Application configuration
LIBREOFFICE_DEFAULT_HOST = 'localhost'
LIBREOFFICE_DEFAULT_PORT = 6519
REQUEST_CHUNK_SIZE = 4096

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
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Instantiating application
app = Flask(__name__)

# Instantiating Libre Office connection
office = LibreOffice(LIBREOFFICE_DEFAULT_HOST, LIBREOFFICE_DEFAULT_PORT)

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

        logger.debug("Converting %s to %s.pdf" % (tmp.name, tmp.name))
        if office.convertFile(suffix, "pdf", tmp.name):
            res = tmp.name.replace("." + suffix, ".pdf")

            logger.debug("Sending file %s back to caller" % res)
            return send_file(res)
        else:
            error = "Error converting file: %s" % office.lastError
            logger.error(error)
            return make_response(jsonify({'error': error}), 500)

if __name__ == '__main__':
    app.run(debug = False, port = 4000)