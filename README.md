# ODF2PDF

ODF2PDF is a converter server based on Flask that will receive open document files
and will return converted PDF files. The initial implementation should focus
only in .odt (word processing) documents. 

The server should be called through HTTP.

## Configuration

Application configuration is controlled through environment variables.

| Variable  | Description | Default value |
|---|---|---|
| ODF2PDF_LOG_DIR | Location in the filesystem where logs will be saved.  | Default path where the application is located  |
| ODF2PDF_HOST  | Host from which application requests will be served. | 0.0.0.0  |
| ODF2PDF_PORT  | Default port number.  | 4000 |
| ODF2PDF_LOG_LEVEL | Log level to be used in the application.  | INFO  |
| ODF2PDF_WORKERS | How many workers will be instantiated. Each worker is bound to a LibreOffice server instance. | One worker per processor core. |
| ODF2PDF_REQUEST_CHUNK_SIZE | Size of the byte buffer that will be used to read requests from the API caller in bytes.  | 40960 bytes |


## API methods

The API exposes the following functions:

### /api/v1/pdf

Converts a document to PDF.

Input parameters:

* (Header) Content-Type: MIME type of the document. Supported content types:
    * application/vnd.oasis.opendocument.text (odt)
    * application/vnd.openxmlformats-officedocument.wordprocessingml.document (docx)
* (Body) Request body: binary file to be conveted
Output parameters:
* (HTTP Code) HTTP result code: 200 OK
* (Body) Response body: conversion result

HTTP Return Codes:

* 200: document converted successfully
* 411: input document has zero length
* 415: input document format not supported
* 500: internal application error

## Testing

curl -v -H "Content-Type: application/vnd.oasis.opendocument.text" -o document.pdf http://localhost:4000/api/v1/pdf --data-binary @samples/0116GS3-OpenSourceStandardsDoc.odt

## Benchmarking

* Simple document: ab -n 100 -c 10 -T 'application/vnd.oasis.opendocument.text' -p samples/lorem.odt http://localhost:4000/api/v1/pdf
* Complex document: ab -n 100 -c 10 -T 'application/vnd.oasis.opendocument.text' -p samples/lorem.odt http://localhost:4000/api/v1/pdf

## TODOs

* Unique IDs per request for logging

## Fonts

For best results, install the following packages:

* MS Core Fonts: apt-get install ttf-mscorefonts-installer)
* Carlito and Caladea (to replace Calibri and Cambria): apt-get install fonts-crosextra-carlito fonts-crosextra-caladea
* PowerPoint Viewer 97 fonts: https://gist.github.com/maxwelleite/10774746

## References

* ODF Mime Types: https://www.openoffice.org/framework/documentation/mimetypes/mimetypes.html
* MS Office Mime Types: http://blogs.msdn.com/b/vsofficedeveloper/archive/2008/05/08/office-2007-open-xml-mime-types.aspx
* LibreOffice Filters: https://ask.libreoffice.org/en/question/59186/what-are-the-5x-impress-importexport-filters/
* Reading streaming data with Werkzeug: http://blog.pelicandd.com/article/80/streaming-input-and-output-in-flask
* Official reference for HTTP return codes: https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
* OpenOffice Connection URL: https://www.openoffice.org/udk/common/man/spec/uno-url.html
* Starting multiple LibreOffice processes concurrently: https://ask.libreoffice.org/en/question/42975/how-can-i-run-multiple-instances-of-sofficebin-at-a-time/


