__author__ = 'jeduardo'

import atexit
import contextlib
import logging
import os
import tempfile

from flask import Flask, jsonify, make_response, request, send_file

from libreoffice import LibreOffice

# Application configuration
REQUEST_CHUNK_SIZE = 40960
LIBREOFFICE_BACKENDS_PER_HANDLER = 1

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
logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger(__name__)

# Instantiating application
app = Flask(__name__)
logger.info("Booting up odf2pdf converter")
backend = LibreOffice()
logger.info("odf2pdf converter ready to process requests")

@app.route('/api/v1/pdf', methods = ['POST'])
def convert_pdf():
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

    # Receiving the temporary file
    logger.debug("Received request for content %s of size %d. Suffix is %s" % (content_type, content_length, suffix))
    with tempfile.NamedTemporaryFile(suffix='.' + suffix, delete=False) as tmp:
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
        # Files need to be closed but not deleted (heh) to be converted.
        tmp.close()

        res = tmp.name.replace("." + suffix, ".pdf")
        logger.debug("Converting %s to %s" % (tmp.name, res))
        try:
            backend.convertFile(suffix, "pdf", tmp.name)
            logger.debug("Sending file %s back to caller" % res)
            return send_file(res)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)
        finally:
            with contextlib.suppress(FileNotFoundError):
                logger.debug("Removing temp file %s", tmp.name)
                os.remove(tmp.name)
                logger.debug("Removing temp PDF file %s", res)
                os.remove(res)

@atexit.register
def cleanup():
    logger.info("Shutting down odf2pdf converter")
    backend.shutdown()

if __name__ == '__main__':
    app.run(debug = False, port = 4000)