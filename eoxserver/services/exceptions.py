#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


class InvalidRequestException(Exception):
    """
    This exception indicates that the request was invalid and an exception
    report shall be returned to the client.
    
    The constructor takes three arguments, namely ``msg``, the error message,
    ``code``, the error code, and ``locator``, which is needed in OWS
    exception reports for indicating which part of the request produced the
    error.
    
    How exactly the exception reports are constructed is not defined by the
    exception, but by exception handlers.
    """
    def __init__(self, msg, code=None, locator=None):
        super(InvalidRequestException, self).__init__(msg)
    
        self.code = code or "InvalidRequest"
        self.locator = locator
    
    def __str__(self):
        return "Invalid Request: Code: %s; Locator: %s; Message: '%s'" % (
            self.code, self.locator, 
            super(InvalidRequestException, self).__str__()
        )

class VersionNegotiationException(Exception):
    """
    This exception indicates that version negotiation fails. Such errors can
    happen with OWS 2.0 compliant "new-style" version negotation.
    """
    code = "VersionNegotiationFailed"

    def __str__(self):
        return "Version negotiation failed."


class LocatorListException(Exception):
    """ Base class for exceptions that report that a number of items are missing
        or invalid
    """
    def __init__(self, items):
        self.items = items

    @property
    def locator(self):
        "This property provides a list of all missing/invalid items."
        return " ".join(self.items)


class InvalidAxisLabelException(LocatorListException):
    """
    This exception indicates that an invalid axis name was chosen in a WCS
    2.0 subsetting parameter.
    """
    code = "InvalidAxisLabels"


class InvalidSubsettingException(Exception):
    """
    This exception indicates an invalid WCS 2.0 subsetting parameter was
    submitted.
    """
    code = "InvalidSubsetting"
    locator = "subset"


class NoSuchCoverageException(LocatorListException):
    """ This exception indicates that the requested coverage(s) do not 
        exist.
    """
    code = "NoSuchCoverage"

    def __str__(self):
        return "Could not find Coverage%s with ID: %s" % (
            "" if len(self.items) == 1 else "s", ", ".join(self.items)
        )


class NoSuchDatasetSeriesOrCoverageException(LocatorListException):
    """ This exception indicates that the requested coverage(s) or dataset 
        series do not exist.
    """
    code = "NoSuchDatasetSeriesOrCoverage"

    def __str__(self):
        return "Could not find Coverage%s or Dataset Series with ID: %s" % (
            " " if len(self.items) == 1 else "s", ", ".join(self.items)
        )


class OperationNotSupportedException(Exception):
    """ Exception to be thrown when some operations are not supported or 
        disabled.
    """
    def __init__(self, message, operation=None):
        super(OperationNotSupportedException, self).__init__(message)
        self.operation = operation

    @property
    def locator(self):
        return self.operation

    code = "OperationNotSupported"


class ServiceNotSupportedException(OperationNotSupportedException):
    """ Exception to be thrown when a specific OWS service is not enabled.
    """
    def __init__(self, service):
        self.service = service

    def __str__(self):
        if self.service:
            return "Service '%s' is not supported." % self.service.upper()
        else:
            return "Service is not supported."


class VersionNotSupportedException(Exception):
    """ Exception to be thrown when a specific OWS service version is not 
        supported.
    """
    def __init__(self, service, version):
        self.service = service
        self.version = version

    def __str__(self):
        if self.service:
            return "Service '%s' version '%s' is not supported." % (
                self.service, self.version
            )
        else:
            return "Version '%s' is not supported." % self.version

    code = "InvalidParameterValue"
