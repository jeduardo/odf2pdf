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

import uno
import subprocess
import time
import os
import sys

from enum import Enum
from com.sun.star.beans import PropertyValue

LIBREOFFICE_DEFAULT_PORT = 6519
LIBREOFFICE_DEFAULT_HOST = "localhost"

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

class LibreOffice(object):

    def __init__(self, host=LIBREOFFICE_DEFAULT_HOST, port=LIBREOFFICE_DEFAULT_PORT):
        self.host = host
        self.port = port
        self.local_context = uno.getComponentContext()
        self.resolver = self.local_context.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", self.local_context)
        self.connectionString = "socket,host=%s,port=%s,tcpNoDelay=1;urp;StarOffice.ComponentContext" % (self.host, self.port)
        self.context = None
        self.desktop = None
        self.runUnoProcess()
        self.__lastErrorMessage = ""

        try:
            self.context = self.resolver.resolve("uno:%s" % self.connectionString)
            self.desktop = self.context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.context)
        except Exception as e:
            self.__lastErrorMessage = str(e)

    @property 
    def lastError(self):
        return self.__lastErrorMessage

    def terminateProcess(self):
        try:
            if self.desktop:
                self.desktop.terminate()
        except Exception as e:
            self.__lastErrorMessage = str(e)
            return False

        return True

    def convertFile(self, inputFormat, outputFormat, inputFilename):
        if self.desktop:
            tOldFileName = os.path.splitext(inputFilename)
            outputFilename = "%s.%s" % (tOldFileName[0], outputFormat)
            #inputFormat = tOldFileName[1].replace(".","") # Temporary files will have no extension
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
                    print(e)
                    pass

                docFamily = self.getDocumentFamily(doc)
                if docFamily:
                    try:
                        outputProperties = LIBREOFFICE_EXPORT_TYPES[outputFormat][docFamily]
                        doc.storeToURL(outputUrl, self.propertyTuple(outputProperties))
                        doc.close(True)

                        return True
                    except Exception as e:
                        self.__lastErrorMessage = str(e)
        
        # self.terminateProcess() # This kills the process if an unsupported document is sent.
        return False

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
        except:
            pass

        return None

    def runUnoProcess(self):
        # subprocess.Popen('soffice --headless --norestore --accept="%s"' % self.connectionString, shell=True, stdin=None, stdout=None, stderr=None)
        subprocess.Popen('soffice --headless --norestore --accept="%s"' % self.connectionString, shell=True, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        time.sleep(3)

if __name__ == '__main__':
    # Simple command line support for testing
    office = LibreOffice()
    office.convertFile(sys.argv[1], "pdf", sys.argv[2])