import atexit
import contextlib
import logging
import os
import tempfile

from datetime import datetime
from flask import Flask, jsonify, make_response, request, send_file
from libreoffice import LibreOffice
from nocache import nocache
from requestid import requestid

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

# Application configuration
REQUEST_CHUNK_SIZE = int(os.environ.get('ODF2PDF_REQUEST_CHUNK_SIZE', 40960))
LOG_LEVEL = os.environ.get('ODF2PDF_LOG_LEVEL', 'INFO')


# Filter to add request ID to logger
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if request:
            id = request.headers.get('X-Request-Id')
            if id:
                record.id = id
            else:
                record.id = 'NOID'
        else:
            record.id = 'INIT'
            return True


# Instantiating application
app = Flask(__name__)
# Configuring logger
logging.basicConfig(level=logging._nameToLevel[LOG_LEVEL],
                    format='%(name)s %(levelname)s %(id)s %(message)s')
for handler in logging.root.handlers:
    handler.addFilter(RequestIdFilter())
logger = logging.getLogger(__name__)
# Bootstrapping
logger.info("Booting up odf2pdf converter")
logger.info("Request chunk size is %d bytes" % REQUEST_CHUNK_SIZE)
logger.info("Default log level is %s" % LOG_LEVEL)
logger.debug("Debug mode is enabled")
backend = LibreOffice()
logger.info("odf2pdf converter ready to process requests")


@app.route('/api/v1/pdf', methods = ['POST'])
@nocache
@requestid
def convert_pdf():
    start_time = datetime.now()
    content_type = request.headers.get('Content-type')
    if content_type not in VALID_MIME_TYPES:
        error = "%s: format not supported" % content_type
        logger.error(error)
        return make_response(jsonify({'error': error}), 415)
    else:
        suffix = VALID_MIME_TYPES[content_type]

    content_length = int(request.headers.get('Content-length'))
    if content_length == 0:
        error = "request data has zero length"
        logger.error(error)
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
            delta = datetime.now() - start_time
            logger.info("Converted %s/%d bytes in %d"  % (content_type, content_length, delta.total_seconds()))
            return send_file(res)
        except Exception as e:
            error = str(e)
            logger.error(error)
            return make_response(jsonify({'error': error}), 500)
        finally:
            with contextlib.suppress(FileNotFoundError):
                logger.debug("Removing temp file %s", tmp.name)
                os.remove(tmp.name)
                logger.debug("Removing temp PDF file %s", res)
                os.remove(res)

@atexit.register
def cleanup():
    app.logger.info("Shutting down odf2pdf converter")
    backend.shutdown()

if __name__ == '__main__':
    app.run(debug = False, port = 4000)