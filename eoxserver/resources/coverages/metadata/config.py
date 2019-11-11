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


DEFAULT_EOXS_COVERAGE_METADATA_FORMAT_READERS = [
    'eoxserver.resources.coverages.metadata.coverage_formats.gsc.GSCFormatReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.dimap_general.DimapGeneralFormatReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.eoom.EOOMFormatReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.gdal_dataset.GDALDatasetMetadataReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.inspire.InspireFormatReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.native.NativeFormat',
    'eoxserver.resources.coverages.metadata.coverage_formats.native_config.NativeConfigFormatReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.landsat8_l1.Landsat8L1CoverageMetadataReader',
]

DEFAULT_EOXS_COVERAGE_METADATA_GDAL_DATASET_FORMAT_READERS = [
    'eoxserver.resources.coverages.metadata.coverage_formats.gdal_dataset_envisat.GDALDatasetEnvisatMetadataFormatReader',
]

DEFAULT_EOXS_PRODUCT_METADATA_FORMAT_READERS = [
    'eoxserver.resources.coverages.metadata.product_formats.sentinel1.S1ProductFormatReader',
    'eoxserver.resources.coverages.metadata.product_formats.sentinel2.S2ProductFormatReader',
    'eoxserver.resources.coverages.metadata.product_formats.landsat8_l1.Landsat8L1ProductMetadataReader',
    'eoxserver.resources.coverages.metadata.coverage_formats.eoom.EOOMFormatReader',
    'eoxserver.resources.coverages.metadata.product_formats.gsc.GSCProductMetadataReader',
]
