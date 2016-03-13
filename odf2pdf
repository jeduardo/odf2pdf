#!/bin/bash
# Launch the application
# Debian: apt-get install gunicorn3
APPDIR="$(dirname "$0")"
LOGDIR=${ODF2PDF_LOG_DIR:-$APPDIR}
WORKERS=${ODF2PDF_WORKERS:-$(nproc)}
HOST=${ODF2PDF_HOST:-'0.0.0.0'}
PORT=${ODF2PDF_PORT:-4000}
gunicorn3 -w $WORKERS --bind $HOST:$PORT \
        --chdir $APPDIR \
        --access-logfile $LOGDIR/odf2pdf.access.log \
        --error-logfile $LOGDIR/odf2pdf.error.log \
        odf2pdf:apps