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

import os.path

from lxml.etree import parse, fromstring
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.utils.six import iteritems
from eoxserver.resources.coverages import crss


try:
    import s2reader
    HAVE_S2READER = True
except ImportError:
    HAVE_S2READER = False


class S2ProductFormatReader(object):
    def test_path(self, path):
        if not HAVE_S2READER:
            return False

        try:
            with s2reader.open(path):
                pass
            return True
        except IOError:
            return False

    def read_path(self, path):
        values = {}
        with s2reader.open(path) as ds:
            metadata = ds._product_metadata
            granule = ds.granules[0]
            granule_metadata = granule._metadata

            values['identifier'] = metadata.findtext(
                './/PRODUCT_URI'
            )

            values['begin_time'] = ds.product_start_time
            values['end_time'] = ds.product_stop_time
            values['footprint'] = ds.footprint.wkt

            values['masks'] = [
                ('clouds', self._read_mask(granule, 'MSK_CLOUDS')),
                ('nodata', self._read_mask(granule, 'MSK_NODATA')),
            ]

            def tci_path(granule):
                tci_paths = [
                    path for path in granule.dataset._product_metadata.xpath(
                        ".//Granule[@granuleIdentifier='%s']/IMAGE_FILE/text()"
                        % granule.granule_identifier
                    ) if path.endswith('TCI')
                ]
                try:
                    return os.path.join(
                        ds._zip_root if ds.is_zip else ds.path,
                        tci_paths[0]
                    ) + '.jp2'
                except IndexError:
                    raise IOError(
                        "TCI path does not exist"
                    )

            values['browses'] = [
                (None, tci_path(granule))
            ]

            # TODO: extended metadata

            # values['parent_identifier']
            # values['production_status']
            # values['acquisition_type']
            values['orbit_number'] = ds.sensing_orbit_number
            values['orbit_direction'] = ds.sensing_orbit_direction
            # values['track']
            # values['frame']
            values['swath_identifier'] = metadata.find('.//Product_Info/Datatake').attrib['datatakeIdentifier']
            values['product_version'] = metadata.findtext('.//Product_Info/PROCESSING_BASELINE')
            # values['product_quality_status']
            # values['product_quality_degradation_tag']
            # values['processor_name']
            # values['processing_center']
            # values['creation_date']
            # values['modification_date']
            values['processing_date'] = ds.generation_time
            # values['sensor_mode']
            values['archiving_center'] = granule_metadata.findtext('.//ARCHIVING_CENTRE')
            # values['processing_mode']

            values['availability_time'] = ds.generation_time
            # values['acquisition_station']
            # values['acquisition_sub_type']
            # values['start_time_from_ascending_node']
            # values['completion_time_from_ascending_node']
            values['illumination_azimuth_angle'] = metadata.findtext('.//Mean_Sun_Angle/AZIMUTH_ANGLE')
            values['illumination_zenith_angle'] = metadata.findtext('.//Mean_Sun_Angle/ZENITH_ANGLE')
            # values['illumination_elevation_angle']
            # values['polarisation_mode']
            # values['polarization_channels']
            # values['antenna_look_direction']
            # values['minimum_incidence_angle']
            # values['maximum_incidence_angle']

            # values['doppler_frequency']
            # values['incidence_angle_variation']

            values['cloud_cover'] = metadata.findtext(".//Cloud_Coverage_Assessment")
            # values['snow_cover']
            # values['lowest_location']
            # values['highest_location']

        return values

    def _read_mask(self, granule, mask_type):
        for item in next(granule._metadata.iter("Pixel_Level_QI")):
            if item.attrib.get("type") == mask_type:
                gml_filename = os.path.join(
                    granule.granule_path, "QI_DATA", os.path.basename(item.text)
                )

        if granule.dataset.is_zip:
            root = fromstring(granule.dataset._zipfile.read(gml_filename))
        else:
            root = parse(gml_filename).getroot()
        return parse_mask(root)


def parse_mask(mask_elem):
    nsmap = {k: v for k, v in iteritems(mask_elem.nsmap) if k}
    # name = mask_elem.xpath('gml:name/text()', namespaces=nsmap)[0]
    try:
        crs = mask_elem.xpath(
            'gml:boundedBy/gml:Envelope/@srsName', namespaces=nsmap
        )[0]
    except IndexError:
        # just return an empty polygon when no mask available
        return MultiPolygon()

    srid = crss.parseEPSGCode(crs, [crss.fromURN])
    swap = crss.hasSwappedAxes(srid)

    mask_features = [
        parse_polygon(polygon_elem, nsmap, swap)
        for polygon_elem in mask_elem.xpath(
            'eop:maskMembers/eop:MaskFeature/eop:extentOf/gml:Polygon',
            namespaces=nsmap
        )
    ]
    return MultiPolygon(mask_features, srid=srid)


def parse_polygon(polygon_elem, nsmap, swap_axes):
    return Polygon(*[
            parse_pos_list(
                polygon_elem.xpath(
                    'gml:exterior/gml:LinearRing/gml:posList', namespaces=nsmap
                )[0], swap_axes
            )
        ] + [
            parse_pos_list(pos_list_elem, swap_axes)
            for pos_list_elem in polygon_elem.xpath(
                'gml:interior/gml:LinearRing/gml:posList', namespaces=nsmap
            )
        ]
    )


def parse_pos_list(pos_list_elem, swap_axes):
    # retrieve the number of elements per point
    dims = int(pos_list_elem.attrib.get('srsDimension', '2'))
    parts = [float(coord) for coord in pos_list_elem.text.strip().split()]

    ring = []
    i = 0
    while i < len(parts):
        ring.append(
            (parts[i + 1], parts[i]) if swap_axes else (parts[i], parts[i + 1])
        )
        i += dims

    return ring
