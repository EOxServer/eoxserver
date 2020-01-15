#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
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
 This module contains format handling utilities.
"""
#-------------------------------------------------------------------------------

import re
import sys
import imp
import logging
import os.path

from django.conf import settings

from eoxserver.contrib import gdal
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config, typelist, strip

try:
    # Python 2
    xrange
except NameError:
    # Python 3, xrange is now named range
    xrange = range

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------


class FormatRegistryException(Exception):
    pass


class Format(object):

    """
    Format record class.
    The class is rather structure with read-only properties (below).
    The class implements ``__str__()`` and ``__eq__()`` methods.
    """

    def __init__(self, mime_type, driver, extension, is_writeable):
        self.__mimeType = mime_type
        self.__driver = driver
        self.__defaultExt = extension
        self.__isWriteable = is_writeable

    mimeType = property(lambda self: self.__mimeType, doc="MIME-type")
    driver = property(lambda self: self.__driver, doc="library/driver identifier")
    defaultExt = property(lambda self: self.__defaultExt, doc="default extension (including dot)")
    isWriteable = property(lambda self: self.__isWriteable, doc="boolean flag indicating that output can be produced")

    @property
    def wcs10name(self):
        """ get WCS 1.0 format name """
        if self.driver.startswith("GDAL/"):
            s = self.driver.split('/')[1]
            if s == "GTiff":
                s = "GeoTIFF"
        else:
            s = self.driver.replace("/", ":")
        return s

    def __str__(self):
        return "%s,%s,%s #%s" % (
            self.mimeType, self.driver, self.defaultExt,
            "rw" if self.isWriteable else "ro"
        )

    def __eq__(self, other):
        try:
            return (
                self.mimeType == other.mimeType and
                self.driver == other.driver and
                self.defaultExt == other.defaultExt
            )
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.mimeType, self.driver, self.defaultExt, self.isWriteable))

# ------------------------------------------------------------------------------

__FORMAT_REGISTRY = None


class FormatRegistry(object):
    """
    The :class:`FormatRegistry` class represents cofiguration of file supported
    formats and of the auxiliary methods. The formats' configuration relies
    on two configuration files:

    * the default formats' configuration (``eoxserver/conf/default_formats.conf``)
    * the optional instance configuration (``conf/format.conf`` in the instance
      directory)

    Configuration values are read from these files.
    """

    #---------------------------------------------------------------------------

    def __init__(self, config):
        # get path to EOxServer installation
        path_eoxs = self.__get_path_eoxs()

        # default formats' configuration
        path_formats_def = os.path.join(path_eoxs, "conf", "default_formats.conf")

        if not os.path.exists(path_formats_def):
            # try alternative location
            path_formats_def = os.path.join(
                sys.prefix, "eox_server", "conf", "default_formats.conf"
            )

            if not os.path.exists(path_formats_def):
                # failed to read the file
                raise FormatRegistryException(
                    "Cannot find the default file formats' configuration file."
                )

        # optional formats' configuration
        path_formats_opt = os.path.join(
            settings.PROJECT_DIR, "conf", "formats.conf"
        )

        if not os.path.exists(path_formats_opt):
            path_formats_opt = None  # no user defined formats' configuration
            logger.debug(
                "Optional, user-defined file formats' specification not found. "
                "Only the installation defaults will be used."
            )

        # load the formats' configuaration
        self.__load_formats(path_formats_def, path_formats_opt)

        # parse the config options
        self.__parse_config(config)

    # --------------------------------------------------------------------------
    # getters

    def getFormatsAll(self):
        """ Get list of all registered formats """

        return self.__mime2format.values()

    def getFormatsByDriver(self, driver_name):
        """
        Get format records for the given GDAL driver name.
        In case of no match empty list is returned.
        """

        return self.__driver2format.get(valDriver(driver_name), [])

    def getFormatsByWCS10Name(self, wcs10name):
        """
        Get format records for the given GDAL driver name. In case of no
        match an empty list is returned.
        """

        # convert WCS 1.0 format name to driver name
        if ":" in wcs10name:
            driver_name = wcs10name.replace(":", "/")
        else:
            if "GeoTIFF" == wcs10name:
                wcs10name = "GTiff"
            driver_name = "GDAL/%s" % wcs10name

        return self.getFormatsByDriver(driver_name)

    def getFormatByMIME(self, mime_type):
        """
        Get format record for the given MIME type.
        In case of no match None is returned.
        """
        return self.__mime2format.get(valMimeType(mime_type), None)

    # --------------------------------------------------------------------------
    # OWS specific getters

    def getSupportedFormatsWCS(self):
        """
            Get list of formats to be announced as supported WCS formats.

            The the listed formats must be:
            * defined in EOxServers configuration (section "services.ows.wcs", item "supported_formats") 
            * defined in the formats' configuration ("default_formats.conf" or "formats.conf")   
            * supported by the used GDAL installation
        """
        return self.__wcs_supported_formats

    def getSupportedFormatsWMS(self):
        """
            Get list of formats to be announced as supported WMS formats.

            The the listed formats must be:
            * defined in EOxServers configuration (section "services.ows.wms", item "supported_formats") 
            * defined in the formats' configuration ("default_formats.conf" or "formats.conf")   
            * supported by the used GDAL installation
        """
        return self.__wms_supported_formats

    def mapSourceToNativeWCS20(self, format):
        """ Map source format to WCS 2.0 native format.

        Both the input and output shall be instances of :class:`Formats` class.
        The input format can be obtained, e.g., by the `getFormatByDriver` or `getFormatByMIME` 
        method.

        To force the default native format use None as the source format.

        The format mapping follows these rules:

        1. Mapping based on the explicite rules is applied if possible (defined in EOxServers
           configuration, section "services.ows.wcs20", item "source_to_native_format_map").
           If there is no mapping available the source format is kept.
        2. If the format resulting from step 1 is not a writable GDAL format or
           it is not among the supported WCS formats than it is
           replaced by the default native format (defined in EOxServers
           configuration, section "services.ows.wcs20", item "default_native_format"). 
           In case of writable GDAL format, the result of step 1 is returned.
        """

        # 1. apply mapping
        format = self.__wcs20_format_mapping.get(format, format)

        # 2. fallback to default
        if format is None or not format.isWriteable \
                or format not in self.getSupportedFormatsWCS():

            format = self.__wcs20_def_native_format

        return format

    def getDefaultNativeFormat(self):
        """ Get default nativeFormat as defined in section 'services.ows.wcs20'.
        """
        return self.__wcs20_def_native_format

    # --------------------------------------------------------------------------
    # loading of configuration - private auxiliary subroutines

        # parse the config options
    def __parse_config(self, config):
        """
        Parse the EOxServer configuration.
        """

        reader = FormatConfigReader(config)

        #  WMS and WCS suported formats

        nonNone = lambda v: (v is not None)
        self.__wms_supported_formats = list(filter(nonNone, map(self.getFormatByMIME, reader.supported_formats_wms)))
        self.__wcs_supported_formats = list(filter(nonNone, map(self.getFormatByMIME, reader.supported_formats_wcs)))

        #  WCS 2.0.1 source to native format mapping

        tmp = self.getFormatByMIME(reader.default_native_format)

        self.__wcs20_def_native_format = tmp

        if tmp is None or tmp not in self.getSupportedFormatsWCS():
            raise ValueError(
                "Invalid value of configuration option 'services.ows.wcs20' "
                "'default_native_format'! value=\"%s\"" % src
            )

        tmp = reader.source_to_native_format_map
        tmp = list(map(lambda m: self.getFormatByMIME(m.strip()), list(tmp.split(','))))
        tmp = [(tmp[i], tmp[i + 1]) for i in xrange(0, (len(tmp) >> 1) << 1, 2)]
        tmp = list(filter(lambda p: list(p)[0] is not None and list(p)[1] is not None, tmp))
        self.__wcs20_format_mapping = dict(tmp)

    def __load_formats(self, path_formats_def, path_formats_opt):
        """
        Load and parse the formats' configuration.
        """

        # register GDAL drivers
        gdal.AllRegister()

        # reset iternall format storage
        self.__driver2format = {}
        self.__mime2format = {}

        # read default configuration
        logger.debug("Loading formats' configuration from: %s" % path_formats_def)
        with open(path_formats_def) as f:
            for ln, line in enumerate(f):
                self.__parse_line(line, path_formats_def, ln + 1)

        # read the optional configuration
        if path_formats_opt:
            logger.debug("Loading formats' configuration from: %s" % path_formats_opt)
            with open(path_formats_opt) as f:
                for ln, line in enumerate(f):
                    self.__parse_line(line, path_formats_opt, ln + 1)

        # finalize format specification
        self.__postproc_formats()

    def __postproc_formats(self):
        """
        Postprocess format specificaions after the loading was finished.
        """

        for frec in list(self.__mime2format.values()):
            # driver to format dictionary
            if frec.driver in self.__driver2format:
                self.__driver2format.append(frec)
            else:
                self.__driver2format[frec.driver] = [frec]

    def __parse_line(self, line, fname, lnum):
        """
        Parse single line of configuration.
        """

        # parse line
        try:
            line = line.partition("#")[0].strip()  # strip comments and white characters 

            if not line:
                return

            (mime_type, driver, extension) = line.split(',')

            mime_type = valMimeType(mime_type.strip())
            driver = valDriver(driver.strip())
            extension = extension.strip()

            if None in (driver, mime_type):
                raise ValueError("Invalid input format specification \"%s\"!" % line)

            # check the check the driver
            backend, _, ldriver = driver.partition("/")

            # no-other backend than GDAL currently supported

            if backend == "GDAL":
                gdriver = gdal.GetDriverByName(ldriver)

                if gdriver is None:
                    raise ValueError("Invalid GDAL driver \"%s\"!" % driver)

                #get the writebility
                is_writeable = (gdriver.GetMetadataItem("DCAP_CREATECOPY") == "YES")

            else:

                raise ValueError("Invalid driver backend \"%s\"!" % driver)

            # create new format record
            frec = Format(mime_type, driver, extension, is_writeable)

            # store format record
            self.__mime2format[mime_type] = frec

            logger.debug("Adding new file format: %s" % frec)

        except Exception as e:
            logger.warning(
                "%s:%i Invalid file format specification! Line ignored! "
                "line=\"%s\" message=\"%s\"" % (
                    fname, lnum, line, e
                )
            )

    def __get_path_eoxs(self):
        """
        Get path to the EOxServer installation.
        """

        try:
            return imp.find_module("eoxserver")[1]
        except ImportError:
            raise FormatRegistryException(
                "Filed to find the 'eoxserver' module! Check your modules' path!"
            )


class FormatConfigReader(config.Reader):
    section = "services.ows.wms"
    supported_formats_wms = config.Option("supported_formats", typelist(strip, ","))

    section = "services.ows.wcs"
    supported_formats_wcs = config.Option("supported_formats", typelist(strip, ","))

    section = "services.ows.wcs20"
    default_native_format = config.Option(type=strip)
    source_to_native_format_map = config.Option()


#-------------------------------------------------------------------------------
# regular expression validators

#: MIME-type regular expression validator (compiled reg.ex. pattern)
_gerexValMime = re.compile("^[\w][-\w]*/[\w][-+\w]*(;[-\w]*=[-\w]*)*$")

#: library driver regular expression validator (compiled reg.ex. pattern)
_gerexValDriv = re.compile("^[\w][-\w]*/[\w][-\w]*$")


def valMimeType(string):
    """
    MIME type reg.ex. validator. If pattern not matched 'None' is returned
    otherwise the input is returned.
    """
    rv = string if _gerexValMime.match(string) else None
    if None is rv:
        logger.warning("Invalid MIME type \"%s\"." % string)
    return rv


def valDriver(string):
    """
    Driver identifier reg.ex. validator. If pattern not matched 'None' is returned 
    otherwise the input is returned.
    """
    rv = string if _gerexValDriv.match(string) else None
    if None is rv:
        logger.warning("Invalid driver's identifier \"%s\"." % string)
    return rv

#-------------------------------------------------------------------------------
# public API


def getFormatRegistry():
    """
        Get initialised instance of the FormatRegistry class.
        This is the preferable way to get the Format Registry.
    """

    global __FORMAT_REGISTRY

    if __FORMAT_REGISTRY is None:

        logger.debug(" --- getFormatRegistry() --- ")
        logger.debug(repr(__FORMAT_REGISTRY))
        logger.debug(repr(_gerexValMime))
        logger.debug(repr(_gerexValDriv))

        # load configuration if not already loaded
        __FORMAT_REGISTRY = FormatRegistry(get_eoxserver_config())

        logger.debug(repr(__FORMAT_REGISTRY))

    return __FORMAT_REGISTRY

#-------------------------------------------------------------------------------
