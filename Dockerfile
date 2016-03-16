FROM debian:jessie
MAINTAINER J. Eduardo <j.eduardo@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

RUN echo "deb http://ftp.de.debian.org/debian jessie main contrib non-free" > /etc/apt/sources.list
RUN echo "deb http://http.debian.net/debian jessie-backports main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update && apt-get -y -q install libreoffice libreoffice-writer ure libreoffice-java-common libreoffice-core libreoffice-common openjdk-7-jre fonts-opensymbol hyphen-fr hyphen-de hyphen-en-us hyphen-it hyphen-ru fonts-dejavu fonts-dejavu-core fonts-dejavu-extra fonts-droid fonts-dustin fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-liberation fonts-lmodern fonts-lyx fonts-sil-gentium fonts-texgyre fonts-tlwg-purisa python3 python3-gunicorn ttf-mscorefonts-installer fonts-crosextra-carlito fonts-crosextra-caladea wget

RUN apt-get install fontforge -y
RUN wget https://gist.github.com/maxwelleite/10774746/raw/ttf-vista-fonts-installer.sh -q -O - | bash

RUN apt-get install gunicorn3

COPY odf2pdf.py /odf2pdf.py
COPY libreoffice.py /odf2pdf.py
COPY odf2pdf /odf2pdf
RUN chmod +x /odf2pdf

VOLUME ["/tmp"]

ENTRYPOINT ["/odf2pdf"]
