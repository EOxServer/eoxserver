#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.util.xmltools import parse, NameSpace, NameSpaceMap
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core.decoders import xml, to_dict, InvalidParameterException
from eoxserver.core import Component

NS_EOP_20 = NameSpace("http://www.opengis.net/eop/2.0", "eop")
NS_OPT_20 = NameSpace("http://www.opengis.net/opt/2.0", "opt")
NS_SAR_20 = NameSpace("http://www.opengis.net/sar/2.0", "sar")
NS_ATM_20 = NameSpace("http://www.opengis.net/atm/2.0", "atm")

namespaces_20 = [NS_EOP_20, NS_OPT_20, NS_SAR_20, NS_ATM_20]

NS_EOP_21 = NameSpace("http://www.opengis.net/eop/2.1", "eop")
NS_OPT_21 = NameSpace("http://www.opengis.net/opt/2.1", "opt")
NS_SAR_21 = NameSpace("http://www.opengis.net/sar/2.1", "sar")
NS_ATM_21 = NameSpace("http://www.opengis.net/atm/2.1", "atm")

namespaces_21 = [NS_EOP_21, NS_OPT_21, NS_SAR_21, NS_ATM_21]

NS_OM = NameSpace("http://www.opengis.net/om/2.0", "om")
NS_GML = NameSpace("http://www.opengis.net/gml/3.2", "gml")

nsmap_20 = NameSpaceMap(NS_GML, NS_OM, *namespaces_20)
nsmap_21 = NameSpaceMap(NS_GML, NS_OM, *namespaces_21)
nsmap_gml = NameSpaceMap(NS_GML)


class EOOMFormatReader(Component):
    def test(self, obj):
        tree = parse(obj)
        tag = tree.getroot().tag if tree is not None else None
        return tree is not None and tag in [
            ns('EarthObservation') for ns in namespaces_20 + namespaces_21
        ]

    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            root = tree.getroot()
            root_ns = root.nsmap[root.prefix]
            use_21 = root_ns in namespaces_21
            decoder = EOOMFormatDecoder(tree, use_21)

            metadata_type = None

            if root_ns in (NS_OPT_20, NS_OPT_21):
                metadata_type = "OPT"
            # TODO: fixme
            # elif root_ns in (NS_ALT_20, NS_ALT_21):
            #     metadata_type = "ALT"
            elif root_ns in (NS_SAR_20, NS_SAR_21):
                metadata_type = "SAR"

            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": MultiPolygon(*decoder.polygons),
                "format": "eogml",
                "metadata": to_dict(EOOMExtraMetadataDecoder(tree, use_21)),
                # "product_metadata": to_dict(
                #     EOOMProductMetadataDecoder(tree, use_21)
                # ),
                # "metadata_type": metadata_type
            }

        raise Exception("Could not parse from obj '%s'." % repr(obj))


def parse_polygon_xml(elem):
    return Polygon(
        parse_ring(
            elem.xpath(
                "gml:exterior/gml:LinearRing/gml:posList", namespaces=nsmap_gml
            )[0].text
        ),
        *map(
            lambda e: parse_ring(e.text),
            elem.xpath(
                "gml:interior/gml:LinearRing/gml:posList", namespaces=nsmap_gml
            )
        )
    )


def parse_ring(string):
    raw_coords = map(float, string.split(" "))
    return [(lon, lat) for lat, lon in pairwise(raw_coords)]


class EOOMNamespaceMixIn(xml.Decoder):
    def __init__(self, tree, use_21):
        if use_21:
            self.namespaces = nsmap_21
        else:
            self.namespaces = nsmap_20
        super(EOOMNamespaceMixIn, self).__init__(tree)


class EOOMFormatDecoder(EOOMNamespaceMixIn, xml.Decoder):
    identifier = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:identifier/text()", type=str, num=1)
    begin_time = xml.Parameter("om:phenomenonTime/gml:TimePeriod/gml:beginPosition/text()", type=parse_iso8601, num=1)
    end_time = xml.Parameter("om:phenomenonTime/gml:TimePeriod/gml:endPosition/text()", type=parse_iso8601, num=1)
    polygons = xml.Parameter("om:featureOfInterest/eop:Footprint/eop:multiExtentOf/gml:MultiSurface/gml:surfaceMember/gml:Polygon", type=parse_polygon_xml, num="+")


class EOOMCollectionMetadataDecoder(EOOMNamespaceMixIn, xml.Decoder):
    spectral_range = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/ eop:wavelengthInformation/eop:WavelengthInformation/eop:spectralRange/text()", type=str, num="?")
    wavelengths = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/ eop:wavelengthInformation/eop:WavelengthInformation/eop:discreteWavelengths/text()", type=str, num="?")
    platform = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:platform/eop:Platform/eop:shortName/text()", type=str, num="?")
    platform_serial_identifier = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:platform/eop:Platform/eop:serialIdentifier/text()", type=str, num="?")
    instrument = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:instrument/eop:Instrument/eop:shortName/text()", type=str, num="?")
    sensor_type = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:sensorType/text()", type=str, num="?")
    composite_type = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:compositeType/text()", type=str, num="?")
    processing_level = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:processingLevel/text()", type=str, num="?")
    orbit_type = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:platform/eop:Platform/eop:orbitType/text()", type=str, num="?")


class EOOMProductMetadataDecoder(EOOMNamespaceMixIn, xml.Decoder):
    parent_identifier = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:parentIdentifier/text()", type=str, num="?")

    production_status = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:status/text()", type=str, num="?")
    acquisition_type = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:acquisitionType/text()", type=str, num="?")

    orbit_number = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:orbitNumber/text()", type=str, num="?")
    orbit_direction = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:orbitDirection/text()", type=str, num="?")

    track = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:wrsLongitudeGrid/text()", type=str, num="?")
    frame = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:wrsLatitudeGrid/text()", type=str, num="?")
    swath_identifier = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:swathIdentifier/text()", type=str, num="?")

    product_version = xml.Parameter("om:result/eop:EarthObservationResult/eop:product/eop:ProductInformation/eop:version/text()", type=str, num="?")
    product_quality_status = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:productQualityDegradation/text()", type=str, num="?")
    product_quality_degradation_tag = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:productQualityDegradationTag/text()", type=str, num="?")
    processor_name = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:processorName/text()", type=str, num="?")
    processing_center = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetadata/eop:processing/eop:ProcessingInformation/eop:processingCenter/text()", type=str, num="?")
    processing_date = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetadata/eop:processing/eop:ProcessingInformation/eop:processingDate/text()", type=parse_iso8601, num="?")
    sensor_mode = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:operationalMode/text()", type=str, num="?")
    archiving_center = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:archivedIn/eop:ArchivingInformation/eop:archivingCenter/text()", type=str, num="?")
    processing_mode = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:ProcessingMode/text()", type=str, num="?")
    creation_date = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:creationDate/text()", type=parse_iso8601, num="?")


class EOOMExtraMetadataDecoder(EOOMNamespaceMixIn, xml.Decoder):
    modification_date = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:modificationDate/text()", type=parse_iso8601, num="?")

    # TODO: get this into models
    # resolution = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:resolution/text()", type=str, num="?")

    cloud_cover = xml.Parameter("om:result/opt:EarthObservationResult/opt:cloudCoverPercentage/text()|om:result/atm:EarthObservationResult/atm:cloudCoverPercentage/text()", type=float, num="?")
    snow_cover = xml.Parameter("om:result/opt:EarthObservationResult/opt:snowCoverPercentage/text()|om:result/atm:EarthObservationResult/atm:snowCoverPercentage/text()", type=float, num="?")
    lowest_location = xml.Parameter("atm:EarthObservation/om:resultOf/atm:EarthObservationResult/atm:dataLayers/atm:DataLayer/atm:lowestLocation/text()", type=float, num="?")
    highest_location = xml.Parameter("atm:EarthObservation/om:resultOf/atm:EarthObservationResult/atm:dataLayers/atm:DataLayer/atm:highestLocation/text()", type=float, num="?")

    acquisition_station = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:downlinkedTo/eop:DownlinkInformation/eop:acquisitionStation/text()", type=str, num="?")
    availability_time = xml.Parameter("om:resultTime/gml:TimeInstant/gml:timePosition/text()", type=parse_iso8601, num="?")
    acquisition_sub_type = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:acquisitionSubType/text()", type=str, num="?")
    start_time_from_ascending_node = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:startTimeFromAscendingNode/text()", type=int, num="?")
    completion_time_from_ascending_node = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:completionTimeFromAscendingNode/text()", type=int, num="?")

    illumination_azimuth_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:illuminationAzimuthAngle/text()", type=float, num="?")
    illumination_zenith_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:illuminationZenithAngle/text()", type=float, num="?")
    illumination_elevation_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:illuminationElevationAngle/text()", type=float, num="?")

    polarisation_mode = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:polarisationMode/text()", type=str, num="?")
    polarization_channels = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:polarisationChannels/text()", type=str, num="?")
    antenna_look_direction = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:antennaLookDirection/text()", type=str, num="?")
    minimum_incidence_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:minimumIncidenceAngle/text()", type=float, num="?")
    maximum_incidence_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:maximumIncidenceAngle/text()", type=float, num="?")
    across_track_incidence_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/eop:acrossTrackIncidenceAngle/text()", type=float, num="?")
    along_track_incidence_angle = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/eop:alongTrackIncidenceAngle/text()", type=float, num="?")
    doppler_frequency = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:dopplerFrequency/text()", type=float, num="?")
    incidence_angle_variation = xml.Parameter("om:procedure/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:incidenceAngleVariation/text()", type=float, num="?")
