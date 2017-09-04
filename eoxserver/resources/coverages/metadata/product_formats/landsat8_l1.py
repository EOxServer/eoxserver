# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------


from django.contrib.gis.geos import Polygon

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.resources.coverages.metadata.utils.landsat8_l1 import (
    is_landsat8_l1_metadata_file, parse_landsat8_l1_metadata_file
)


class Landsat8L1ProductMetadataReader(object):
    def test_path(self, path):
        return is_landsat8_l1_metadata_file(path)

    def read_path(self, path):
        md = parse_landsat8_l1_metadata_file(path)

        p = md['PRODUCT_METADATA']
        ul = float(p['CORNER_UL_LON_PRODUCT']), float(p['CORNER_UL_LAT_PRODUCT'])
        ur = float(p['CORNER_UR_LON_PRODUCT']), float(p['CORNER_UR_LAT_PRODUCT'])
        ll = float(p['CORNER_LL_LON_PRODUCT']), float(p['CORNER_LL_LAT_PRODUCT'])
        lr = float(p['CORNER_LR_LON_PRODUCT']), float(p['CORNER_LR_LAT_PRODUCT'])

        values = {}
        values['identifier'] = md['METADATA_FILE_INFO']['LANDSAT_SCENE_ID']
        values['footprint'] = Polygon([ul, ur, lr, ll, ul])
        time = parse_iso8601('%sT%s' % (
            p['DATE_ACQUIRED'], p['SCENE_CENTER_TIME']
        ))
        values['begin_time'] = values['end_time'] = time
        values['cloud_cover'] = float(md['IMAGE_ATTRIBUTES']['CLOUD_COVER'])
        values['track'] = p['WRS_PATH']
        values['frame'] = p['WRS_ROW']

        values['processing_date'] = parse_iso8601(
            md['METADATA_FILE_INFO']['FILE_DATE']
        )

        # TODO: maybe convert additional fields from Metadata file

        return values

        # from pprint import pprint; pprint(values)

        # values['parent_identifier']
        # values['production_status']
        # values['acquisition_type']
        # values['orbit_number'] = ds.sensing_orbit_number
        # values['orbit_direction'] = ds.sensing_orbit_dir
        # values['track']
        # values['frame']
        # values['swath_identifier'] = metadata.find('.//P
        # values['product_version'] = metadata.findtext('.
        # values['product_quality_status']
        # values['product_quality_degradation_tag']
        # values['processor_name']
        # values['processing_center']
        # values['creation_date']
        # values['modification_date']
        # values['processing_date'] = ds.generation_time
        # values['sensor_mode']
        # values['archiving_center'] = granule_metadata.fi
        # values['processing_mode']
        # values['availability_time'] = ds.generation_time
        # values['acquisition_station']
        # values['acquisition_sub_type']
        # values['start_time_from_ascending_node']
        # values['completion_time_from_ascending_node']
        # values['illumination_azimuth_angle'] = metadata.
        # values['illumination_zenith_angle'] = metadata.f
        # values['illumination_elevation_angle']
        # values['polarisation_mode']
        # values['polarization_channels']
        # values['antenna_look_direction']
        # values['minimum_incidence_angle']
        # values['maximum_incidence_angle']
        # values['doppler_frequency']
        # values['incidence_angle_variation']
        # values['cloud_cover'] = metadata.findtext(".//Cl
        # values['snow_cover']
        # values['lowest_location']
        # values['highest_location']
