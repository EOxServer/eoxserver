#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013-2014 EOX IT Services GmbH
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

class OWS10Exception(Exception):
    """ Base OWS 1.0 exception of the WPS 1.0.0 exceptions """
    http_status_code = 400
    def __init__(self, code, locator, message):
        self.code = code
        self.locator = locator
        Exception.__init__(self, message)

#-------------------------------------------------------------------------------
# All possible WPS 1.0.0 exceptions. For list of OWS exception used by WPS
# see OGC 05-007r7 Table 38 and Table 62

class NoApplicableCode(OWS10Exception):
    http_status_code = 500
    def __init__(self, message, locator=None):
        OWS10Exception.__init__(self, "NoApplicableCode", locator, message)

class MissingParameterValue(OWS10Exception):
    def __init__(self, message, locator):
        OWS10Exception.__init__(self, "MissingParameterValue", locator, message)

class InvalidParameterValue(OWS10Exception):
    def __init__(self, message, locator):
        OWS10Exception.__init__(self, "InvalidParameterValue", locator, message)

class NotEnoughStorage(OWS10Exception):
    http_status_code = 507
    def __init__(self, message):
        OWS10Exception.__init__(self, "NotEnoughStorage", None, message)

class ServerBusy(OWS10Exception):
    http_status_code = 503
    def __init__(self, message):
        OWS10Exception.__init__(self, "ServerBusy", None, message)

class FileSizeExceeded(OWS10Exception):
    def __init__(self, message, locator):
        OWS10Exception.__init__(self, "FileSizeExceeded", locator, message)

class StorageNotSupported(OWS10Exception):
    def __init__(self, message):
        OWS10Exception.__init__(self, "StorageNotSupported", None, message)

class VersionNegotiationFailed(OWS10Exception):
    def __init__(self, message, locator):
        OWS10Exception.__init__(self, "VersionNegotiationFailed", locator, message)

#-------------------------------------------------------------------------------
# Derived specific exceptions.
#
# Note that WPS 1.0.0 allows use of "vendor specific exception code" as locator
# for the default "NoApplicableCode" exceptions.

class NoSuchProcessError(InvalidParameterValue):
    def __init__(self, identifier):
        msg = "No such process: %s" % identifier
        InvalidParameterValue.__init__(self, msg, "process identifier")

class InvalidOutputError(InvalidParameterValue):
    def __init__(self, output_id):
        message = "Invalid output '%s'!"%(output_id)
        InvalidParameterValue.__init__(self, message, output_id)

class InvalidOutputValueError(NoApplicableCode):
    def __init__(self, output_id, message=""):
        message = "Invalid output value of '%s'! %s"%(output_id, message)
        NoApplicableCode.__init__(self, message, output_id)

class InvalidOutputDefError(InvalidParameterValue):
    def __init__(self, output_id, message=""):
        message = "Invalid output definition of '%s'! %s"%(output_id, message)
        InvalidParameterValue.__init__(self, message, output_id)

class InvalidInputError(InvalidParameterValue):
    def __init__(self, input_id):
        message = "Invalid input '%s'!"%(input_id)
        InvalidParameterValue.__init__(self, message, input_id)

class InvalidInputValueError(InvalidParameterValue):
    def __init__(self, input_id, message=""):
        message = "Invalid input value of '%s'! %s"%(input_id, message)
        InvalidParameterValue.__init__(self, message, input_id)

class InvalidInputReferenceError(InvalidParameterValue):
    def __init__(self, input_id, message=""):
        message = "Invalid input '%s' reference! %s"%(input_id, message)
        InvalidParameterValue.__init__(self, message, input_id)

class MissingRequiredInputError(InvalidParameterValue):
    def __init__(self, input_id):
        message = "Missing required input '%s'!"%(input_id)
        InvalidParameterValue.__init__(self, message, input_id)

class ExecuteError(NoApplicableCode):
    def __init__(self, message="", locator="process.execute()"):
        NoApplicableCode.__init__(self, message, locator)


# This is defined in OGC 06-121r9 (referenced by WPS 2.0), not sure if also applicable in WPS 1.0
class OperationNotSupportedError(OWS10Exception):
    def __init__(self, message, locator=None):
        OWS10Exception.__init__(self, code="OperationNotSupported", locator=None, message=message)
