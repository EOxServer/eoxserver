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

import os
from os.path import join, isdir, isfile
import zipfile

from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.xmltools import parse as parse_xml
from eoxserver.core.util.timetools import parse_iso8601


nsmap = {
    'safe': 'http://www.esa.int/safe/sentinel-1.0',
    'gml': 'http://www.opengis.net/gml'
}


class S1ProductFormatReader(object):
    def test_path(self, path):
        try:
            manifest = self.open_manifest(path)
            if not manifest:
                return False

            root = manifest.getroot()
            return root.xpath(
                'metadataSection/metadataObject[@ID="platform"]/metadataWrap/'
                'xmlData/safe:platform/safe:familyName/text()',
                namespaces=nsmap
            )[0] == "SENTINEL-1"
        except (IOError, RuntimeError, IndexError):
            return False

    def read_path(self, path):
        values = {}
        root = self.open_manifest(path).getroot()

        period_elem = root.xpath(
            'metadataSection/metadataObject[@ID="acquisitionPeriod"]/'
            'metadataWrap/xmlData/safe:acquisitionPeriod',
            namespaces=nsmap
        )[0]

        values['begin_time'] = parse_iso8601(
            period_elem.findtext('safe:startTime', namespaces=nsmap)
        )
        values['end_time'] = parse_iso8601(
            period_elem.findtext('safe:stopTime', namespaces=nsmap)
        )

        coordinates_elems = root.xpath(
            'metadataSection/metadataObject[@ID="measurementFrameSet"]/'
            'metadataWrap/xmlData/safe:frameSet/safe:frame/safe:footPrint/'
            'gml:coordinates',
            namespaces=nsmap
        )

        values['footprint'] = MultiPolygon([
            self.parse_coordinates(coordinates_elem.text)
            for coordinates_elem in coordinates_elems
        ]).wkt

        # values['identifier'] =

        # values['browses'] = [
        #     (None, tci_path(granule))
        # ]

        # TODO: extended metadata

        # values['parent_identifier']
        # values['production_status']
        # values['acquisition_type']
        # values['orbit_number'] =
        # values['orbit_direction'] =
        # values['track']
        # values['frame']
        # values['swath_identifier'] =
        # values['product_version'] =
        # values['product_quality_status']
        # values['product_quality_degradation_tag']
        # values['processor_name']
        # values['processing_center']
        # values['creation_date']
        # values['modification_date']
        # values['processing_date'] =
        # values['sensor_mode']
        # values['archiving_center'] =
        # values['processing_mode']

        # values['availability_time'] =
        # values['acquisition_station']
        # values['acquisition_sub_type']
        # values['start_time_from_ascending_node']
        # values['completion_time_from_ascending_node']
        # values['illumination_azimuth_angle'] =
        # values['illumination_zenith_angle'] =
        # values['illumination_elevation_angle']
        # values['polarisation_mode']
        # values['polarization_channels']
        # values['antenna_look_direction']
        # values['minimum_incidence_angle']
        # values['maximum_incidence_angle']

        # values['doppler_frequency']
        # values['incidence_angle_variation']

        # values['cloud_cover'] =
        # values['snow_cover']
        # values['lowest_location']
        # values['highest_location']

        return values

    def open_manifest(self, path):
        """ Tries to open the manifest of a given sentinel 1 SAFE product.
            Supported are:
                - directories containing a Sentinel-1 product
                - zip files containing a sentinel product
                - a direct path reference to a safe file
        """
        if isdir(path):
            manifest_path = join(path, 'manifest.safe')
            if not isfile(manifest_path):
                try:
                    manifest_path = join(
                        path,
                        get_immediate_subdirectories(path)[0],
                        'manifest.safe'
                    )
                except IndexError:
                    raise IOError(
                        "Could not locate 'manifest.safe' in %r" % path
                    )

            with open(manifest_path) as f:
                return parse_xml(f)
        elif zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zp_f:
                names = [
                    name for name in zp_f.namelist()
                    if name.endswith('manifest.safe')
                ]

                try:
                    return parse_xml(zp_f.open(names[0]))
                except IndexError:
                    raise IOError("Could not find 'manifest.safe' in %r" % path)

        elif isfile(path):
            with open(path) as f:
                return parse_xml(f)

        raise IOError('Could not open manifest for path %r' % path)

    def parse_coordinates(self, coords, swap=True):
        points = [
            tuple(float(v) for v in coord.split(','))
            for coord in coords.split()
        ]

        if swap:
            points[:] = [
                (p[1], p[0])
                for p in points
            ]

        points.append(points[0])
        return Polygon(points)


def get_immediate_subdirectories(a_dir):
    return [
        name
        for name in os.listdir(a_dir)
        if isdir(join(a_dir, name))
    ]
