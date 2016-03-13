#!/bin/bash
# Launch the application

# Debian: apt-get install uwsgi-plugin-python3
# uwsgi --plugins python34 --http-socket 127.0.0.1:4000 --wsgi-file odf2pdf.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191

# Debian: apt-get install gunicorn3
LOGDIR="."
gunicorn3 -w $(nproc) --bind 0.0.0.0:4000 \
        --access-logfile $LOGDIR/odf2pdf.access.log \
        --error-logfile $LOGDIR/odf2pdf.error.log \
        odf2pdf:app