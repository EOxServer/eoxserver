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

DEFAULT_EOXS_CAPABILITIES_RENDERERS = [
    'eoxserver.services.native.wcs.capabilities_renderer.NativeWCS20CapabilitiesRenderer',
    'eoxserver.services.mapserver.wcs.capabilities_renderer.MapServerWCSCapabilitiesRenderer',
]

DEFAULT_EOXS_COVERAGE_DESCRIPTION_RENDERERS = [
    'eoxserver.services.mapserver.wcs.coverage_description_renderer.CoverageDescriptionMapServerRenderer',
    'eoxserver.services.native.wcs.coverage_description_renderer.NativeWCS20CoverageDescriptionRenderer',
]

DEFAULT_EOXS_COVERAGE_RENDERERS = [
    'eoxserver.services.mapserver.wcs.coverage_renderer.RectifiedCoverageMapServerRenderer',
    'eoxserver.services.gdal.wcs.referenceable_dataset_renderer.GDALReferenceableDatasetRenderer',
]

DEFAULT_EOXS_COVERAGE_ENCODING_EXTENSIONS = [
    'eoxserver.services.ows.wcs.v20.encodings.geotiff.WCS20GeoTIFFEncodingExtension'
]