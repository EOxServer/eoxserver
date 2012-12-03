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
 
class MetadataException(EOxSException):
    pass

class NoSuchCoverageException(EOxSException):
    pass

class NoSuchDatasetSeriesException(EOxSException):
    pass

class SynchronizationErrors(EOxSException):
    def __init__(self, *errors):
        self.errors = errors
        if len(errors):
            self.msg = errors[0]
    
    def __iter__(self):
        return iter(self.errors)

    def __str__(self):
        return str(self.errors)

class EngineError(EOxSException):
    """
    This error shall be raised when a coverage engine (e.g. GDAL) fails.
    """
    pass

class ManagerError(EOxSException):
    """
    This error shall be raised when the Manager has encountered an error.
    """
    pass

class CoverageIdError(EOxSException):
    """
    Subclasses of this error shall be raised when errors with Coverage IDs are
    encountered.
    """
    pass

class CoverageIdReservedError(CoverageIdError):
    """
    This error shall be raised when a Coverage ID is already reserved and tried
    to be reserved again.
    """
    pass

class CoverageIdInUseError(CoverageIdError):
    """
    This error shall be raised when a Coverage ID is already used by an existing
    coverage and tried to be reserved.
    """
    pass

class CoverageIdReleaseError(CoverageIdError):
    """
    This error shall be raised when a Coverage ID is released which was not 
    previously reserved.
    """
    pass
