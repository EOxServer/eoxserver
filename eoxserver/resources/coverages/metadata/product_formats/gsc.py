#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from eoxserver.core.util.xmltools import parse
from eoxserver.core.decoders import xml, to_dict, InvalidParameterException

from eoxserver.resources.coverages.metadata.utils.gsc import (
    NS_GSC, nsmap, GSCFormatDecoder
)


class GSCFormatExtendedDecoder(xml.Decoder):
    namespaces = nsmap

    identifier = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:identifier/text()", type=str, num="?")
    parent_identifier = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:parentIdentifier/text()", type=str, num="?")
    production_status = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:status/text()", type=str, num="?")
    acquisition_type = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:acquisitionType/text()", type=str, num="?") 
    orbit_number = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/eop:orbitNumber/text()", type=int, num="?")
    orbit_direction = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/eop:orbitDirection/text()", type=str, num="?")
    
    swath_identifier = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:swathIdentifier/text()", type=str, num="?")
   

    product_version = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:resultOf/eop:EarthObservationResult/eop:product/eop:ProductInformation/eop:version/text()", type=float, num="?")
    product_quality_status = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:resultOf/eop:EarthObservationMetaData/eop:productQualityStatus/text()", type=str, num="?")
    product_quality_degradation_tag = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:productQualityDegradationTag/text()", type=str, num="?")
    processing_center = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:processingCenter/text()", type=str, num="?")
    creation_date = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:creationDate/text()", type=str, num="?") # insertion into catalog
    modification_date = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:modificationDate/text()", type=str, num="?") # last modification in catalog
    processing_date = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:processingDate/text()", type=str, num="?")
    sensor_mode = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:operationalMode/text()", type=str, num="?")
    archiving_center = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:archivedIn/eop:ArchivingInformation/eop:archivingCenter/text()", type=str, num="?")
    processing_mode = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:processing/eop:ProcessingInformation/eop:processingMode/text()", type=str, num="?")
    # acquisition type metadata
    
    acquisition_station = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:downlinkedTo/eop:DownlinkInformation/eop:acquisitionStation/text()", type=str, num="?")
    acquisition_sub_type = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:acquisitionSubType/text()", type=str, num="?")
    start_time_from_ascending_node = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:startTimeFromAscendingNode/text()", type=str, num="?")
    completion_time_from_ascending_node = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/eop:Acquisition/eop:completionTimeFromAscendingNode/text()", type=str, num="?")
    illumination_azimuth_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/opt:illuminationAzimuthAngle/text()", type=float, num="?")
    illumination_zenith_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/opt:illuminationZenithAngle/text()", type=float, num="?")
    illumination_elevation_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/opt:illuminationElevationAngle/text()", type=float, num="?")
    across_track_incidence_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/eop:acrossTrackIncidenceAngle/text()", type=float, num="?")
    along_track_incidence_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/opt:Acquisition/eop:alongTrackIncidenceAngle/text()", type=float, num="?")
    polarisation_mode = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:polarisationMode/text()", type=str, num="?")
    polarization_channels = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:polarisationChannels/text()", type=str, num="?")
    antenna_look_direction = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:antennaLookDirection/text()", type=str, num="?")
    minimum_incidence_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:minimumIncidenceAngle/text()", type=float, num="?")
    maximum_incidence_angle = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:maximumIncidenceAngle/text()", type=float, num="?")
    # for SAR acquisitions
    doppler_frequency = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:dopplerFrequency/text()", type=float, num="?")
    incidence_angle_variation = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/eop:EarthObservationEquipment/eop:acquisitionParameters/sar:Acquisition/sar:incidenceAngleVariation/text()", type=float, num="?")
    # for OPT/ALT
    cloud_cover = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:resultOf/opt:EarthObservationResult/opt:cloudCoverPercentage/text()", type=float, num="?")
    snow_cover = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:resultOf/opt:EarthObservationResult/opt:snowCoverPercentage/text()", type=float, num="?")
    
    #TODO
    # add track and frame 
    # add the following values:
    # availability_time = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/om:resultTime/gml:TimeInstant/ gml:timePosition/text()", type=str, num="?")
    # lowest_location = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/lmb:Footprint/lmb:minimumAltitude/text()", type=float, num= "?")
    # highest_location = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:using/lmb:Footprint/lmb:maximumAltitude/text()", type=float, num= "?")

class GSCProductMetadataReader(object):
    def test(self, obj):
        tree = parse(obj)

        tag = tree.getroot().tag if tree is not None else None
        return tree is not None and tag == NS_GSC('report')

    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            decoder = GSCFormatDecoder(tree)
            values = {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": decoder.footprint,
                "format": "gsc",
            }
            values.update(to_dict(GSCFormatExtendedDecoder(tree)))
            return values
