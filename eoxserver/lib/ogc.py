#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

"""
This module contains old style exception handlers that use the OGC
namespace for exception reports
"""

from eoxserver.lib.exceptions import EOxSInvalidRequestException
from eoxserver.lib.handlers import EOxSExceptionHandler, EOxSExceptionEncoder

class EOxSOGCExceptionHandler(EOxSExceptionHandler):
    def _filterExceptions(self, exception):
        if not isinstance(exception, EOxSInvalidRequestException):
            raise
    
    def _getEncoder(self):
        return EOxSOGCExceptionEncoder()
    
    def _getContentType(self, exception):
        return "application/vnd.ogs.se_xml"

class EOxSOGCExceptionEncoder(EOxSExceptionEncoder):
    def _initializeNamespaces(self):
        return {"ogc": "http://www.opengis.net/ogc"}
    
    def encodeExceptionReport(self, exception_text, exception_code, locator=None):
        if locator is None:
            return self._makeElement("ogc", "ServiceExceptionReport", [
                ("", "@version", "1.2.0"),
                ("ogc", "ServiceException", [
                    ("", "@code", exception_code),
                    ("", "@@", exception_text)
                ])
            ])
        else:
            return self._makeElement("ogc", "ServiceExceptionReport", [
                ("", "@version", "1.2.0"),
                ("ogc", "ServiceException", [
                    ("", "@code", exception_code),
                    ("", "@locator", locator),
                    ("", "@@", exception_text)
                ])
            ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code, exception.locator)
