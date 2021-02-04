# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

import contextlib
import time
import logging
try:
    from cgi import escape
except ImportError:
    from html import escape
import tempfile
import os

try:
    from mapscript import *
except ImportError:
    # defaults for document generation
    if os.environ.get('READTHEDOCS', None) == 'True':
        class mapObj: pass
        class layerObj: pass
        class classObj: pass
        class styleObj: pass
        class shapeObj: pass
        class colorObj: pass
        MS_LAYER_RASTER = 0
        MS_LAYER_POLYGON = 1
        MS_GET_REQUEST = 0
    else:
        raise
else:
    msversion = msGetVersionInt()

from lxml import etree
from eoxserver.core.util.multiparttools import iterate
from eoxserver.contrib import gdal
from eoxserver.services.result import result_set_from_raw_data

logger = logging.getLogger(__name__)


class MapServerException(Exception):
    def __init__(self, message, locator, code=None):
        super(MapServerException, self).__init__(message)
        self.locator = locator
        self.code = code


class MetadataMixIn(object):
    """ Mix-In for classes that wrap mapscript objects with associated metadata.
    """

    def __init__(self, metadata=None):
        super(MetadataMixIn, self).__init__()
        if metadata:
            self.setMetaData(metadata)

    def __getitem__(self, key):
        self.getMetaData(key)

    def __setitem__(self, key, value):
        self.setMetaData(key, value)

    def setMetaData(self, key_or_params, value=None, namespace=None):
        """ Convenvience method to allow setting multiple metadata values with
            one call and optionally setting a 'namespace' for each entry.
        """
        if value is None:
            for key, value in key_or_params.items():
                if namespace:
                    key = "%s_%s" % (namespace, key)

                super(MetadataMixIn, self).setMetaData(key, value)
        else:
            if namespace:
                key = "%s_%s" % (namespace, key_or_params)
            else:
                key = key_or_params

            return super(MetadataMixIn, self).setMetaData(key, value)


class Map(MetadataMixIn, mapObj):
    def dispatch(self, request):
        return dispatch(self, request)


def dispatch(map_, request):
    """ Wraps the ``OWSDispatch`` method. Perfoms all necessary steps for a
        further handling of the result.
    """

    logger.debug("MapServer: Installing stdout to buffer.")
    msIO_installStdoutToBuffer()

    # write the map if debug is enabled
    if logger.isEnabledFor(logging.DEBUG):
        fd, filename = tempfile.mkstemp(text=True)
        try:
            with os.fdopen(fd) as f:
                map_.save(filename)
                logger.debug(f.read())
        finally:
            os.remove(filename)

    try:
        logger.debug("MapServer: Dispatching.")
        ts = time.time()
        # Execute the OWS request by mapserver, obtain the status in
        # dispatch_status (0 is OK)
        status = map_.OWSDispatch(request)
        te = time.time()
        logger.debug("MapServer: Dispatch took %f seconds." % (te - ts))
    except Exception as e:
        raise MapServerException(str(e), "NoApplicableCode")

    raw_bytes = msIO_getStdoutBufferBytes()

    # check whether an error occurred
    if status != 0:
        # First try to get the error message through the error object
        obj = msGetErrorObj()
        if obj and obj.message:
            raise MapServerException(obj.message, obj.code)

        try:
            # try to parse the output as XML
            result = result_set_from_raw_data(raw_bytes)
            tree = etree.fromstring(result[0].data)
            exception_elem = tree.xpath("*[local-name() = 'Exception']|*[local-name() = 'ServiceException']")[0]
            locator = exception_elem.attrib.get("locator")
            code = exception_elem.attrib.get("exceptionCode")
            message = exception_elem[0].text

            raise MapServerException(message, locator, code)

        except (etree.XMLSyntaxError, IndexError, KeyError):
            pass

        # Fallback: raise arbitrary error
        raise MapServerException("Unexpected Error.", "NoApplicableCode")

    logger.debug("MapServer: Performing MapServer cleanup.")
    # Workaround for MapServer issue #4369
    if msversion < 60004 or (msversion < 60200 and msversion >= 60100):
        msCleanup()
    else:
        msIO_resetHandlers()

    return raw_bytes


class Layer(MetadataMixIn, layerObj):
    def __init__(self, name, metadata=None, type=MS_LAYER_RASTER, mapobj=None):
        layerObj.__init__(self, mapobj)
        MetadataMixIn.__init__(self, metadata)
        self.name = name
        self.status = MS_ON
        if type == MS_LAYER_RASTER:
            self.dump = MS_TRUE
            self.setConnectionType(MS_RASTER, "")
        self.type = type


class Class(classObj):
    def __init__(self, name, mapobj=None):
        classObj.__init__(self, mapobj)
        self.name = name


class Style(styleObj):
    def __init__(self, name, mapobj=None):
        styleObj.__init__(self, mapobj)
        self.name = name


def create_request(values, request_type=MS_GET_REQUEST):
    """ Creates a mapserver request from
    """
    used_keys = {}

    request = OWSRequest()
    request.type = request_type

    if request_type == MS_GET_REQUEST:
        for key, value in values:
            key = key.lower()
            used_keys.setdefault(key, 0)
            # addParameter() available in MapServer >= 6.2
            # https://github.com/mapserver/mapserver/issues/3973
            try:
                request.addParameter(key.lower(), escape(value))
            # Workaround for MapServer 6.0
            except AttributeError:
                used_keys[key] += 1
                request.setParameter(
                    "%s_%d" % (key, used_keys[key]), escape(value)
                )
    elif request_type == MS_POST_REQUEST:
        request.postrequest = value

    return request


def gdalconst_to_imagemode(const):
    """
    This function translates a GDAL data type constant as defined in the
    :mod:`gdalconst` module to a MapScript image mode constant.
    """
    if const == gdal.GDT_Byte:
        return MS_IMAGEMODE_BYTE
    elif const in (gdal.GDT_Int16, gdal.GDT_UInt16):
        return MS_IMAGEMODE_INT16
    elif const == gdal.GDT_Float32:
        return MS_IMAGEMODE_FLOAT32
    else:
        raise ValueError(
            "MapServer is not capable to process the datatype '%s' (%d)."
            % (gdal.GetDataTypeName(const), const)
        )


def gdalconst_to_imagemode_string(const):
    """
    This function translates a GDAL data type constant as defined in the
    :mod:`gdalconst` module to a string as used in the MapServer map file
    to denote an image mode.
    """
    if const == gdal.GDT_Byte:
        return "BYTE"
    elif const in (gdal.GDT_Int16, gdal.GDT_UInt16):
        return "INT16"
    elif const == gdal.GDT_Float32:
        return "FLOAT32"


def setMetaData(obj, key_or_params, value=None, namespace=None):
    """ Convenvience function to allow setting multiple metadata values with
        one call and optionally setting a 'namespace' for each entry.
    """
    if value is None:
        for key, value in key_or_params.items():
            if namespace:
                key = "%s_%s" % (namespace, key)

            obj.setMetaData(key, value)
    else:
        if namespace:
            key = "%s_%s" % (namespace, key_or_params)
        else:
            key = key_or_params

        obj.setMetaData(key, value)

# alias
set_metadata = setMetaData


def set_env(map_obj, env, fail_on_override=False, return_old=False):
    old_values = {} if return_old else None
    for key, value in env.items():
        if fail_on_override or return_old:
            old_value = map_obj.getConfigOption(str(key))
            if fail_on_override and old_value is not None \
                    and old_value != value:
                raise Exception(
                    'Would override previous value of %s: %s with %s'
                    % (key, old_value, value)
                )
            elif old_value != value and return_old:
                old_values[key] = old_value

        map_obj.setConfigOption(str(key), str(value))

    return old_values

@contextlib.contextmanager
def config_env(map_obj, env, fail_on_override=False, reset_old=True):
    old_env = set_env(env, fail_on_override, reset_old)
    yield
    if reset_old:
        set_env(old_env, False, False)
