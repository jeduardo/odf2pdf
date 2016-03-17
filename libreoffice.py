#!/usr/bin/env python3
"""
    VIEW COMPLETE CODE AT
    =====================

    * https://github.com/six519/libreoffice_convert

    THANKS
    ======

    * Thanks to: Mirko Nasato for his PyODConverter http://www.artofsolving.com/opensource/pyodconverter

    TESTED USING
    ============

    * Fedora release 20 (Heisenbug)
    * Python 3.3.2

    INSTALL DEPENDENCIES
    ====================

    * yum install libreoffice-sdk

"""

import contextlib
import logging
import uno
import subprocess
import time
import os
import shutil
import sys

from enum import Enum
from random import randint
from com.sun.star.beans import PropertyValue

logger = logging.getLogger(__name__)

# Engine configuration
WAIT_FOR_START = int(os.environ.get('ODF2PDF_WAIT_FOR_START', 10))

class DocumentFamily(Enum):
    TextDocument = 0
    WebDocument = 1
    Spreadsheet = 2
    Presentation = 3
    Graphics = 4

LIBREOFFICE_IMPORT_TYPES = {
    "docx": {
        "FilterName": "Microsoft Word 2007-2013 XML"
    },
    "pdf": {
        "FilterName": "PDF - Portable Document Format"
    },
    "jpg": {
        "FilterName": "JPEG - Joint Photographic Experts Group"
    },
    "html": {
        "FilterName": "HTML Document"
    },
    "odp": {
        "FilterName": "OpenDocument Presentation Flat XML"
    },
    "pptx": {
        "FilterName": "Microsoft PowerPoint 2007-2013 XML"
    },
    # Added from official list
    "odt": {
        "FilterName": "OpenDocument Text (Flat XML)"
    },
    # Added from https://github.com/mirkonasato/pyodconverter/blob/master/DocumentConverter.py
    "txt": {
        "FilterName": "Text (encoded)",
        "FilterOptions": "utf8"
    },
    "csv": {
        "FilterName": "Text - txt - csv (StarCalc)",
        "FilterOptions": "44,34,0"
    }
}

LIBREOFFICE_EXPORT_TYPES = {
    "pdf": {
        DocumentFamily.TextDocument: {"FilterName": "writer_pdf_Export"},
        DocumentFamily.WebDocument: {"FilterName": "writer_web_pdf_Export"},
        DocumentFamily.Spreadsheet: {"FilterName": "calc_pdf_Export"},
        DocumentFamily.Presentation: {"FilterName": "impress_pdf_Export"},
        DocumentFamily.Graphics: {"FilterName": "draw_pdf_Export"}
    },
    "jpg": {
        DocumentFamily.Presentation: {"FilterName": "impress_jpg_Export"},
        DocumentFamily.Graphics: {"FilterName": "draw_jpg_Export"}
    },
    "html": {
        DocumentFamily.TextDocument: {"FilterName": "HTML (StarWriter)"},
        DocumentFamily.WebDocument: {"FilterName": "HTML"},
        DocumentFamily.Spreadsheet: {"FilterName": "HTML (StarCalc)"},
        DocumentFamily.Presentation: {"FilterName": "impress_html_Export"},
        DocumentFamily.Graphics: {"FilterName": "draw_html_Export"}
    },
    "docx": {
        DocumentFamily.TextDocument: {"FilterName": "MS Word 2007 XML"}
    },
    "odp": {
        DocumentFamily.Presentation: {"FilterName": "impress8"}
    },
    "pptx": {
        DocumentFamily.Presentation: {"FilterName": "Impress MS PowerPoint 2007 XML"}
    },
    # Extra filters added from https://github.com/mirkonasato/pyodconverter/blob/master/DocumentConverter.py
    "odt": {
        DocumentFamily.TextDocument: {"FilterName": "writer8"},
        DocumentFamily.WebDocument: {"FilterName": "writerweb8_writer"}
    },
    "doc": {
        DocumentFamily.TextDocument: {"FilterName": "MS Word 97"}
    },
    "rtf": {
        DocumentFamily.TextDocument: {"FilterName": "Rich Text Format"}
    },
    "txt": {
        DocumentFamily.TextDocument: {
            "FilterName": "Text",
            "FilterOptions": "utf8"
        }
    },
    "ods": {
        DocumentFamily.Spreadsheet: {"FilterName": "calc8"}
    },
    "xls": {
        DocumentFamily.Spreadsheet: {"FilterName": "MS Excel 97"}
    },
    "csv": {
        DocumentFamily.Spreadsheet: {
            "FilterName": "Text - txt - csv (StarCalc)",
            "FilterOptions": "44,34,0"
        }
    },
    "ppt": {
        DocumentFamily.Presentation: {"FilterName": "MS PowerPoint 97"}
    },
    "swf": {
        DocumentFamily.Graphics: {"FilterName": "draw_flash_Export"},
        DocumentFamily.Presentation: {"FilterName": "impress_flash_Export"}
    }
}

class LibreOfficeInstantiationException(Exception):
    pass

class LibreOfficeTerminationException(Exception):
    pass

class LibreOfficeConversionException(Exception):
    pass

class LibreOffice(object):

    def __init__(self):
        self.local_context = uno.getComponentContext()
        self.resolver = self.local_context.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", self.local_context)
        # self.connectionString = "socket,host=%s,port=%s,tcpNoDelay=1;urp;StarOffice.ComponentContext" % (self.host, self.port)
        self.pipe = "odf2pdf-%d" % randint(1, 10000);
        self.connectionString = "pipe,name=%s;urp;StarOffice.ComponentContext" % self.pipe
        logger.debug("LibreOffice connection string set to %s", self.connectionString)
        self.context = None
        self.desktop = None
        self.runProcess()

        try:
            self.context = self.resolver.resolve("uno:%s" % self.connectionString)
            self.desktop = self.context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.context)
            logger.info("Instantiated LibreOffice: PID %d, pipe: %s" % (self.pid, self.pipe))
        except Exception as e:
            raise LibreOfficeInstantiationException(e)

    def terminateProcess(self):
        try:
            if self.desktop:
                self.desktop.terminate()
        except Exception as e:
            raise LibreOfficeTerminationException(e)

        return True

    def convertFile(self, inputFormat, outputFormat, inputFilename):
        if self.desktop:
            tOldFileName = os.path.splitext(inputFilename)
            outputFilename = "%s.%s" % (tOldFileName[0], outputFormat)
            inputUrl = uno.systemPathToFileUrl(os.path.abspath(inputFilename))
            outputUrl = uno.systemPathToFileUrl(os.path.abspath(outputFilename))

            if inputFormat in LIBREOFFICE_IMPORT_TYPES:
                inputProperties = {
                    "Hidden": True
                }
                inputProperties.update(LIBREOFFICE_IMPORT_TYPES[inputFormat])
                doc = self.desktop.loadComponentFromURL(inputUrl, "_blank", 0, self.propertyTuple(inputProperties))
                
                try:
                    doc.refresh()
                except Exception as e:
                    raise LibreOfficeConversionException(e)

                docFamily = self.getDocumentFamily(doc)
                if docFamily:
                    try:
                        outputProperties = LIBREOFFICE_EXPORT_TYPES[outputFormat][docFamily]
                        doc.storeToURL(outputUrl, self.propertyTuple(outputProperties))
                        doc.close(True)
                    except Exception as e:
                        raise LibreOfficeConversionException(e)

    def propertyTuple(self, propDict):
        properties = []
        for k,v in propDict.items():
            property = PropertyValue()
            property.Name = k
            property.Value = v
            properties.append(property)

        return tuple(properties)

    def getDocumentFamily(self, doc):
        try:
            if doc.supportsService("com.sun.star.text.GenericTextDocument"):
                return DocumentFamily.TextDocument
            if doc.supportsService("com.sun.star.text.WebDocument"):
                return DocumentFamily.WebDocument
            if doc.supportsService("com.sun.star.sheet.SpreadsheetDocument"):
                return DocumentFamily.Spreadsheet
            if doc.supportsService("com.sun.star.presentation.PresentationDocument"):
                return DocumentFamily.Presentation
            if doc.supportsService("com.sun.star.drawing.DrawingDocument"):
                return DocumentFamily.Graphics
        except Exception as e:
            raise LibreOfficeConversionException(e)
        return None

    def runProcess(self):
        # subprocess.Popen('soffice --headless --norestore --accept="%s"' % self.connectionString, shell=True, stdin=None, stdout=None, stderr=None)
        self.proc = subprocess.Popen('soffice "-env:UserInstallation=file:////tmp/libreoffice-%s" --headless --norestore --accept="%s"' % (self.pipe, self.connectionString), shell=True, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        self.pid = self.proc.pid
        logger.info("Waiting for libreoffice to start (%s)" % self.connectionString)
        time.sleep(WAIT_FOR_START)

    def __str__(self):
        return "LibreOffice instance with PID %d and pipe %s" % (self.pid, self.pipe)

    def shutdown(self):
        logger.debug("Shutting down LibreOffice process under pid %d", self.proc.pid)
        self.proc.kill()
        with contextlib.suppress(FileNotFoundError):
            path = "/tmp/libreoffice-%s" % self.pipe
            logger.debug("Removing all files under %s" % path)
            shutil.rmtree(path, True)

if __name__ == '__main__':
    # Simple command line support for testing
    office = LibreOffice()
    office.convertFile(sys.argv[1], "pdf", sys.argv[2])