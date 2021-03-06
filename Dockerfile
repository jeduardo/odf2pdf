FROM debian:jessie
MAINTAINER J. Eduardo <j.eduardo@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

RUN echo "deb http://ftp.de.debian.org/debian jessie main contrib non-free" > /etc/apt/sources.list
RUN echo "deb http://http.debian.net/debian jessie-backports main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update
RUN apt-get -y -q install libreoffice libreoffice-writer ure libreoffice-java-common libreoffice-core libreoffice-common openjdk-7-jre fonts-opensymbol hyphen-fr hyphen-de hyphen-en-us hyphen-it hyphen-ru fonts-dejavu fonts-dejavu-core fonts-dejavu-extra fonts-droid fonts-dustin fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-liberation fonts-lmodern fonts-lyx fonts-sil-gentium fonts-texgyre fonts-tlwg-purisa ttf-mscorefonts-installer fonts-crosextra-carlito fonts-crosextra-caladea wget

RUN apt-get install fontforge -y
RUN wget https://gist.github.com/maxwelleite/10774746/raw/ttf-vista-fonts-installer.sh -q -O - | bash

RUN apt-get install python3 python3-gunicorn gunicorn3 python3-flask -y

RUN mkdir /srv/odf2pdf
COPY *.py /srv/odf2pdf/
COPY odf2pdf /srv/odf2pdf/
RUN chmod +x /srv/odf2pdf/odf2pdf

VOLUME ["/tmp"]

ENTRYPOINT ["/srv/odf2pdf/odf2pdf"]
