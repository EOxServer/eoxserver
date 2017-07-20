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
            granule = ds.granules[0]
            values['identifier'] = ds._product_metadata.findtext(
                './/PRODUCT_URI'
            )
            values['begin_time'] = ds.product_start_time
            values['end_time'] = ds.product_stop_time
            values['footprint'] = ds.footprint.wkt

            values['masks'] = [
                ('clouds', granule.cloudmask.wkt),
                ('nodata', granule.nodata_mask.wkt),
            ]
            values['browses'] = [
                (None, granule.pvi_path)
            ]

            # TODO: extended metadata

            # values['parent_identifier']
            # values['production_status']
            # values['acquisition_type']
            values['orbit_number'] = ds.sensing_orbit_number
            values['orbit_direction'] = ds.sensing_orbit_direction
            # values['track']
            # values['frame']
            values['swath_identifier'] = ds._product_metadata.find('.//Product_Info/Datatake').attrib['datatakeIdentifier']
            values['product_version'] = ds._product_metadata.findtext('.//Product_Info/PROCESSING_BASELINE')
            # values['product_quality_status']
            # values['product_quality_degradation_tag']
            # values['processor_name']
            # values['processing_center']
            # values['creation_date']
            # values['modification_date']
            values['processing_date'] = ds.generation_time
            # values['sensor_mode']
            # values['archiving_center']
            # values['processing_mode']

        return values
