#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

"""
This module implements variaous managers providing API for operation over 
the stored datasets. For details of the provided functionality see the
documentation of the individual manager classes. 

.. warning:: 

    This module has been deprecated. Although it still works it will be
    removed eventually. Use ``eoxserver.resources.coverages.managers``
    module instead. 

    See :ref:`module_resources_coverages_managers` documentation. 

"""

import warnings 
import logging 

warnings.warn("The 'eoxserver.resources.coverages.covmrgs' module is "
    "deprecated. Use ``eoxserver.resources.coverages.managers`` instead."
    , Warning, stacklevel=2)

logging.warn("The 'eoxserver.resources.coverages.covmrgs' module is "
    "deprecated. Use 'eoxserver.resources.coverages.managers' instead." ) 

#import os.path
#from ConfigParser import RawConfigParser
#import logging
#from uuid import uuid4
#from datetime import timedelta

#from django.contrib.gis.geos.geometry import MultiPolygon
#try:
#    from django.utils import timezone
#except ImportError:
#    from datetime import datetime as timezone

#from eoxserver.core.system import System
#from eoxserver.core.exceptions import InternalError
#from eoxserver.core.util.timetools import UTCOffsetTimeZoneInfo
#from eoxserver.resources.coverages.exceptions import (
#    ManagerError, NoSuchCoverageException, CoverageIdReservedError,
#    CoverageIdInUseError, CoverageIdReleaseError
#, MetadataException)
#from eoxserver.resources.coverages.models import (
#    PlainCoverageRecord, RectifiedDatasetRecord, 
#    ReferenceableDatasetRecord, RectifiedStitchedMosaicRecord,
#    ReservedCoverageIdRecord, CoverageRecord, DatasetSeriesRecord
#) 
#from eoxserver.resources.coverages.metadata import EOMetadata
#from eoxserver.processing.mosaic import make_mosaic

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import *
