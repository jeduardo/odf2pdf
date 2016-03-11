# ODF2PDF

ODF2PDF is a converter server based on Flask that will receive open document files
and will return converted PDF files. The initial implementation should focus
only in .odt (word processing) documents. 

The server should be called through HTTP.

## API definitions

###  /api/v1/pdf

Converts a document to PDF.

Input parameters:
- (Header) Content-Type: MIME type of the document. Supported content types:
* application/vnd.oasis.opendocument.text
- (Body) Request body: binary file to be conveted
Output parameters:
- (HTTP Code) HTTP result code: 200 OK
- (Body) Response body: conversion result

## Testing

curl -v -H "Content-Type: application/vnd.oasis.opendocument.text" -o document.pdf http://localhost:4000/api/v1/pdf --data-binary @samples/0116GS3-OpenSourceStandardsDoc.odt

## Benchmarking

ab -n 100 -c 10 -T 'application/vnd.oasis.opendocument.text' -p samples/0116GS3-OpenSourceStandardsDoc.odt http://localhost:4000/api/v1/pdf

## TODOs

* Unique IDs per request for logging
* Cron job or Celery task for removing old files

## References

* ODF Mime Types: https://www.openoffice.org/framework/documentation/mimetypes/mimetypes.html
* MS Office Mime Types: http://blogs.msdn.com/b/vsofficedeveloper/archive/2008/05/08/office-2007-open-xml-mime-types.aspx
* LibreOffice Filters: https://ask.libreoffice.org/en/question/59186/what-are-the-5x-impress-importexport-filters/
* Reading streaming data with Werkzeug: http://blog.pelicandd.com/article/80/streaming-input-and-output-in-flask
* Official reference for HTTP return codes: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
* OpenOffice Connection URL: https://www.openoffice.org/udk/common/man/spec/uno-url.html

