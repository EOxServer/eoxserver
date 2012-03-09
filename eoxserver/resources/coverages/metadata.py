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

"""
This module contains the implementation of basic XML EO metadata formats and
EO metadata objects.
"""


from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.system import System
from eoxserver.core.exceptions import (
    InternalError, ImplementationAmbiguous, ImplementationNotFound
)
from eoxserver.core.util.xmltools import XMLDecoder
from eoxserver.core.util.timetools import getDateTime
from eoxserver.core.util.geotools import posListToWkt
from eoxserver.resources.coverages.interfaces import (
    GenericEOMetadataInterface, EOMetadataFormatInterface,
    EOMetadataReaderInterface
)
from eoxserver.resources.coverages.exceptions import MetadataException

#-------------------------------------------------------------------------------
# defining namespaces 

NS_EOP="http://www.opengis.net/eop/2.0"
NS_OMD="http://www.opengis.net/om/2.0"
NS_GML="http://www.opengis.net/gml/3.2"

#-------------------------------------------------------------------------------

class MetadataFormat(object):
    """
    Abstract base class for metada formats. A blueprint for implementing
    :class:`~.MetadataFormatInterface`.
    """
    def test(self, test_params):
        """
        Not implemented. Raises :exc:`~.InternalError`.
        """
        
        raise InternalError("Not implemented.")

    def getName(self):
        """
        Not implemented. Raises :exc:`~.InternalError`.
        """
        
        raise InternalError("Not implemented.")
    
    def getMetadataKeys(self):
        """
        Not implemented. Raises :exc:`~.InternalError`.
        """
        
        raise InternalError("Not implemented.")
        
    def getMetadataValues(self, keys, raw_metadata):
        """
        Not implemented. Raises :exc:`~.InternalError`.
        """
        
        raise InternalError("Not implemented.")
    
class XMLMetadataFormat(MetadataFormat):
    """
    This is a base class for XML based metadata formats. It inherits from
    :class:`MetadataFormat`.
    """
    
    # concrete formats must define an XML decoding schema as defined by
    # core.util.xmltools.XMLDecoder here
    #PARAM_SCHEMA = {}
    
    def getMetadataKeys(self):
        """
        Returns the keys for key-value-pair metadata access.
        """
        
        return self.PARAM_SCHEMA.keys()
    
    def getMetadataValues(self, keys, raw_metadata):
        """
        Returns metadata key-value-pairs for the given ``keys``. The argument
        ``raw_metadata`` is expected to be a string containing valid XML. This
        method raises :exc:`~.InternalError` if ``raw_metadata`` is not a
        string or :exc:`~.MetadataException` if it cannot be parsed as valid
        XML.
        """
        
        if not isinstance(raw_metadata, str) or isinstance(raw_metadata, unicode):
            raise InternalError(
                "XML metadata formats cannot decode raw metadata of type '%s'." %\
                raw_metadata.__class__.__name__
            )
        
        try:
            decoder = XMLDecoder(raw_metadata, self.PARAM_SCHEMA)
        except Exception, e:
            raise MetadataException(
                "Invalid XML input to XMLMetadataFormat.getMetadataValues(). Error message: '%s'" %\
                str(e)
            )
        
        ret_dict = {}
        
        for key in keys:
            if key not in self.PARAM_SCHEMA:
                ret_dict[key] = None
            else:
                ret_dict[key] = decoder.getValue(key)
        
        return ret_dict

class XMLEOMetadataFormat(XMLMetadataFormat):
    """
    This is the base class for XML EO Metadata formats implementing 
    :class:`~.EOMetadataFormatInterface`. It adds :meth:`getEOMetadata` to
    the :class:`XMLMetadataFormat` implementation it inherits from.
    """
    
    def getEOMetadata(self, raw_metadata):
        """
        This method decodes the raw XML metadata passed to it and returns
        an :class:`EOMetadata` instance. The method raises
        :exc:`~.InternalError` if ``raw_metadata`` is not a string or
        :exc:`~.MetadataException` if it cannot be parsed as valid XML.
        """
        if not isinstance(raw_metadata, str) or isinstance(raw_metadata, unicode):
            raise InternalError(
                "XML EO metadata formats cannot decode raw metadata of type '%s'." %\
                raw_metadata.__class__.__name__
            )
        
        try:
            decoder = XMLDecoder(raw_metadata, self.PARAM_SCHEMA)
        except Exception, e:
            raise MetadataException(
                "Invalid XML input to XMLMetadataFormat.getEOMetadata(). Error message: '%s'" %\
                str(e)
            )
        
        return EOMetadata(
            eo_id = self._get_eo_id(decoder),
            begin_time = self._get_begin_time(decoder),
            end_time = self._get_end_time(decoder),
            footprint = self._get_footprint(decoder),
            md_format = self,
            raw_metadata = raw_metadata
        )
    
    def _get_eo_id(self, decoder):
        return decoder.getValue("eoid")
        
    def _get_begin_time(self, decoder):
        return getDateTime(decoder.getValue("begintime"))
    
    def _get_end_time(self, decoder):
        return getDateTime(decoder.getValue("endtime"))
    
    def _get_footprint(self, decoder):
        polygon_dicts = decoder.getValue("footprint")
        
        polygon_wkts = []
        for polygon_dict in polygon_dicts:
            exterior_wkt = "(%s)" % posListToWkt(polygon_dict["exterior_ring"])
            interior_wkts = ["(%s)" % posListToWkt(interior_ring) for interior_ring in polygon_dict["interior_rings"]]
            
            if len(interior_wkts) == 0:
                polygon_wkts.append("(%s)" % exterior_wkt)
            else:
                polygon_wkts.append("(%s,%s)" % (exterior_wkt, ",".join(interior_wkts)))
        
        if len(polygon_wkts) == 1:
            wkt = "POLYGON%s" % polygon_wkts[0]
        elif len(polygon_wkts) == 0:
            wkt = ""
        else:
            wkt = "MULTIPOLYGON(%s)" % ",".join(polygon_wkts)
        
        return GEOSGeometry(wkt)

class NativeMetadataFormat(XMLEOMetadataFormat):
    """
    This is an implementation of an EOxServer native metadata format. This
    format was designed to be as simple as possible and is intended for use in
    a testing environment. A template XML snippet looks like::
    
        <Metadata>
            <EOID>some_unique_eoid</EOID>
            <BeginTime>YYYY-MM-DDTHH:MM:SSZ</BeginTime>
            <EndTime>YYYY-MM-DDTHH:MM:SSZ</EndTime>
            <Footprint>
                <Polygon>
                    <Exterior>Mandatory - some_pos_list as all-space-delimited Lat Lon pairs (closed polygon i.e. 5 coordinate pairs for a rectangle) in EPSG:4326</Exterior>
                    [
                     <Interior>Optional - some_pos_list as all-space-delimited Lat Lon pairs (closed polygon) in EPSG:4326</Interior>
                     ...
                    ]
                </Polygon>
            </Footprint>
        </Metadata>
    """
    REGISTRY_CONF = {
        "name": "EOxServer Native EO Metadata Format",
        "impl_id": "resources.coverages.metadata.NativeMetadataFormat"
    }
    
    PARAM_SCHEMA = {
        "eoid": {"xml_location": "/EOID", "xml_type": "string"},
        "begintime": {"xml_location": "/BeginTime", "xml_type": "string"},
        "endtime": {"xml_location": "/EndTime", "xml_type": "string"},
        "footprint": {"xml_location": "/Footprint/Polygon", "xml_type": "dict[1:]", "xml_dict_elements": {
            "exterior_ring": {"xml_location": "Exterior", "xml_type": "floatlist"},
            "interior_rings": {"xml_location": "Interior", "xml_type": "floatlist[]"}
        }}
    }
    
    def test(self, test_params):
        """
        This method is required by the :class:`~.Registry`. It tests whether
        XML input can be interpreted as EOxServer native XML. It expects one
        dictionary entry ``root_name`` in the ``test_params`` dictionary. It
        will raise :exc:`~.InternalError` if it is missing.
        
        The method will return ``True`` if the ``root_name`` is ``"Metadata"``,
        ``False`` otherwise.
        """
        if "root_name" in test_params:
            return test_params["root_name"] == "Metadata"
        else:
            raise InternalError(
                "Missing mandatory 'root_name' test parameter for metadata format detection."
            )

    def getName(self):
        """
        Returns ``"native"``.
        """
        
        return "native"
        
NativeMetadataFormatImplementation = \
EOMetadataFormatInterface.implement(NativeMetadataFormat)

class EOOMFormat(XMLEOMetadataFormat):
    """
    This is a basic implementation of the OGC (and ESA HMA) EO O&M metadata
    format.
    """
    
    REGISTRY_CONF = {
        "name": "EO O&M Metadata Format",
        "impl_id": "resources.coverages.metadata.EOOMFormat"
    }

    PARAM_SCHEMA = {
        "eoid": {"xml_location": "/{%s}metaDataProperty/{%s}EarthObservationMetaData/{%s}identifier"%(NS_EOP,NS_EOP,NS_EOP), "xml_type": "string"},
        "begintime": {"xml_location": "/{%s}phenomenonTime/{%s}TimePeriod/{%s}beginPosition"%(NS_OMD,NS_GML,NS_GML), "xml_type": "string"},
        "endtime": {"xml_location": "/{%s}phenomenonTime/{%s}TimePeriod/{%s}endPosition"%(NS_OMD,NS_GML,NS_GML), "xml_type": "string"},
        "footprint": {"xml_location": "/{%s}featureOfInterest/{%s}Footprint/{%s}multiExtentOf/{%s}MultiSurface/{%s}surfaceMember/{%s}Polygon"%(NS_OMD,NS_EOP,NS_EOP,NS_GML,NS_GML,NS_GML), "xml_type": "dict[1:]", "xml_dict_elements": {
            "exterior_ring": {"xml_location": "{%s}exterior/{%s}LinearRing/{%s}posList"%(NS_GML,NS_GML,NS_GML), "xml_type": "floatlist"},
            "interior_rings": {"xml_location": "{%s}interior/{%s}LinearRing/{%s}posList"%(NS_GML,NS_GML,NS_GML), "xml_type": "floatlist[]"}
        }}
    }

    def test(self, test_params):
        """
        This method is required by the :class:`~.Registry`. It tests whether
        XML input can be interpreted as EOxServer native XML. It expects one
        dictionary entry ``root_name`` in the ``test_params`` dictionary. It
        will raise :exc:`~.InternalError` if it is missing.
        
        The method will return ``True`` if the ``root_name`` is ``"Metadata"``,
        ``False`` otherwise.
        """
        if "root_name" in test_params:
            return test_params["root_name"] == "EarthObservation"
        else:
            raise InternalError(
                "Missing mandatory 'root_name' test parameter for metadata format detection."
            )

    def getName(self):
        """
        Returns ``"eogml"``.
        """
        
        return "eogml"

EOOMFormatImplementation = EOMetadataFormatInterface.implement(EOOMFormat)

class DIMAPFormat(MetadataFormat):
    # NOT YET IMPLEMENTED
    
    def test(self, test_params):
        return False

    def getName(self):
        return "dimap"
        
class EOMetadata(object):
    """
    This is an implementation of :class:`~.GenericEOMetadataInterface`. It
    is an object containing the basic set of EO Metadata required by EOxServer.
    Additional metadata is available using the generic metadata access methods.
    
    Instances of this object are returned by metadata format implementations.
    """
    
    REGISTRY_CONF = {
        "name": "EO Metadata object",
        "impl_id": "resources.coverages.metadata.EOMetadata"
    }
    
    def __init__(self, eo_id, begin_time, end_time, footprint, md_format=None, raw_metadata=None):
        self.eo_id = eo_id
        self.begin_time = begin_time
        self.end_time = end_time
        self.footprint = footprint
        
        self.md_format = md_format
        self.raw_metadata = raw_metadata
    
    def getEOID(self):
        """
        Returns the EO ID of the object.
        """
        return self.eo_id
    
    def getBeginTime(self):
        """
        Returns the acquisition begin time as :class:`datetime.datetime`
        object.
        """
        return self.begin_time
        
    def getEndTime(self):
        """
        Returns the acquisition end time as :class:`datetime.datetime`
        object.
        """
        return self.end_time
        
    def getFootprint(self):
        """
        Returns the acquisition footprint as
        :class:`django.contrib.gis.geos.GEOSGeometry` object.
        """
        return self.footprint
    
    def getMetadataFormat(self):
        """
        Returns the metadata format object, i.e. an implementation of
        :class:`~.EOMetadataFormatInterface` if one was defined when creating
        the object, ``None`` otherwise.
        """
        return self.md_format
        
    def getMetadataKeys(self):
        """
        Returns the keys of the metadata key-value-pairs that can be retrieved
        from this instance or an empty list if no metadata format has been
        specified that can decode the raw metadata.
        """
        if self.md_format:
            return self.md_format.getMetadataKeys()
        else:
            return []
    
    def getMetadataValues(self, keys):
        """
        Returns a dictionary of metadata key-value-pairs for the given keys.
        If there is no metadata format and/or no raw metadata object defined
        for the instance a dictionary mapping the keys to ``None`` is returned.
        """
        
        if self.md_format and self.raw_metadata:
            return self.md_format.getMetadataValues(keys, self.raw_metadata)
        else:
            return dict.fromkeys(keys)
    
    def getRawMetadata(self):
        return self.raw_metadata

EOMetadataImplementation = GenericEOMetadataInterface.implement(EOMetadata)

class XMLEOMetadataFileReader(object):
    """
    This is an implementation of :class:`~.EOMetadataReaderInterface` for
    local XML files, i.e. ``resources.coverages.interfaces.location_type``
    is ``local`` and ``resources.coverages.interfaces.encoding_type`` is
    ``xml``.
    """
    REGISTRY_CONF = {
        "name": "XML EO Metadata File Reader",
        "impl_id": "resources.coverages.metadata.XMLEOMetadataFileReader",
        "registry_values": {
            "resources.coverages.interfaces.location_type": "local",
            "resources.coverages.interfaces.encoding_type": "xml"
        }
    }
    
    def readEOMetadata(self, location):
        """
        Returns an :class:`EOMetadata` object for the XML file at the given
        local path. Raises :exc:`~.InternalError` if the location is not a
        path on the local file system or :exc:`~.DataAccessError` if it cannot
        be opened. :exc:`~.MetadataException` is raised if the file content
        is not valid XML or if the XML metadata format is unknown.
        """
        
        if location.getType() == "local":
            md_file = location.open()
        else:
            raise InternalError(
                "Attempt to read metadata from non-local location."
            )
        
        xml = md_file.read()
        
        md_file.close()

        DETECTION_SCHEMA = {
            "root_name": {"xml_location": "/", "xml_type": "localName"}
        }
    
        try:
            decoder = XMLDecoder(xml, DETECTION_SCHEMA)
        except Exception, e:
            raise MetadataException(
                "File at '%s' is not valid XML. Error message: '%s'" %\
                location.getPath(), str(e)
            )
        
        root_name = decoder.getValue("root_name")
        
        try:
            md_format = System.getRegistry().findAndBind(
                intf_id = "resources.coverages.interfaces.EOMetadataFormat",
                params = {"root_name": root_name}
            )
        except ImplementationNotFound:
            raise MetadataException(
                "Unknown XML EO Metadata format. XML root element name not '%s' not recognized." %\
                root_name
            )
        except ImplementationAmbiguous:
            raise InternalError(
                "Multiple XML EO Metadata Formats for XML root element name '%s'." %\
                root_name
            )
        
        return md_format.getEOMetadata(xml)

XMLEOMetadataFileReaderImplementation = \
EOMetadataReaderInterface.implement(XMLEOMetadataFileReader)
