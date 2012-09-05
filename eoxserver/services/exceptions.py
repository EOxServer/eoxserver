#-------------------------------------------------------------------------------
# $Id$
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

from eoxserver.core.exceptions import EOxSException

class InvalidRequestException(EOxSException):
    """
    This exception indicates that the request was invalid and an exception
    report shall be returned to the client.
    
    The constructor takes three arguments, namely ``msg``, the error message,
    ``error_code``, the error code, and ``locator``, which is needed in OWS
    exception reports for indicating which part of the request produced the
    error.
    
    How exactly the exception reports are constructed is not defined by the
    exception, but by exception handlers.
    """
    def __init__(self, msg, error_code, locator):
        super(InvalidRequestException, self).__init__(msg)
        
        self.msg = msg
        self.error_code = error_code
        self.locator = locator
    
    def __str__(self):
        return "Invalid Request: ErrorCode: %s; Locator: %s; Message: '%s'" % (
            self.error_code, self.locator, self.msg
        )

class VersionNegotiationException(EOxSException):
    """
    This exception indicates that version negotiation fails. Such errors can
    happen with OWS 2.0 compliant "new-style" version negotation.
    """
    pass

class InvalidAxisLabelException(EOxSException):
    """
    This exception indicates that an invalid axis name was chosen in a WCS
    2.0 subsetting parameter.
    """
    pass

class InvalidSubsettingException(EOxSException):
    """
    This exception indicates an invalid WCS 2.0 subsetting parameter was
    submitted.
    """
    pass
