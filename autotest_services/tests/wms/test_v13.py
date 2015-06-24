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

from autotest_services import base as testbase
import base as wmsbase


class WMS13GetCapabilitiesValidTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WMS 1.3 GetCapabilities response"""

    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetCapabilities"
        return (params, "kvp")


class WMS13GetCapabilitiesEmptyTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid but empty WMS 1.3 GetCapabilities response (see #41)"""
    fixtures = [
        "range_types.json", "meris_range_type.json", "asar_range_type.json"
    ]
    
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetCapabilities"
        return (params, "kvp")


class WMSVersionNegotiationTestCase(testbase.XMLTestCase):
    """This test shall check version negotiation. A valid WMS 1.3 GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=WMS&request=GetCapabilities"
        return (params, "kvp")

class WMSVersionNegotiationNewStyleTestCase(testbase.XMLTestCase):
    """This test shall check new style version negotiation. A valid WMS 1.3 GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=WMS&acceptversions=1.3.0,1.0.0&request=GetCapabilities"
        return (params, "kvp")

class WMSVersionNegotiationFaultTestCase(testbase.ExceptionTestCase):
    """This test shall check new style version negotiation. A valid ows:ExceptionReport shall be returned"""
    def getRequest(self):
        params = "service=WMS&acceptversions=3.0.0&request=GetCapabilities"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "VersionNegotiationFailed"

    def getExceptionCodeLocation(self):
        return "ogc:ServiceException/@code"

class WMSVersionNegotiationOldStyleTestCase(testbase.XMLTestCase):
    """This test shall check old style version negotiation. A valid WMS 1.3 GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=WMS&version=3.0.0&request=GetCapabilities"
        return (params, "kvp")


class WMS13GetMapDatasetTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a simple dataset. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)

class WMS13GetMapNoServiceParameterTestCase(testbase.RasterTestCase):
    """This test shall retrieve a map while omitting the service parameter. """
    def getRequest(self):
        params = "version=1.3.0&request=GetMap&" \
                 "layers=mosaic_MER_FRS_1P_reduced_RGB&styles=&crs=epsg:4326&" \
                 "bbox=35,10,45,20&width=100&height=100&format=image/tiff"
        return (params, "kvp")

class WMS13GetMapMultipleDatasetsTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with two datasets. """
    layers = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
              "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
              )
    width = 200
    bbox = (-3.75, 32.19025, 28.29481, 46.268645)
    
class WMS13GetMapDatasetMultispectralTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset containing 15 bands. """
    layers = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)


class WMS13GetMapMosaicTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a stitched mosaic. """
    layers = ("mosaic_MER_FRS_1P_reduced_RGB",)
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    width = 200

class WMS13GetMapPNGDatasetTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.5, 32.2, 25.4, 46.3)
    frmt = "image/png"

class WMS13GetMapGIFDatasetTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.5, 32.2, 25.4, 46.3)
    frmt = "image/gif"

class WMS13GetMapTIFFDatasetTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.5, 32.2, 25.4, 46.3)
    frmt = "image/tiff"

class WMS13GetMapLayerNotDefinedFaultTestCase(wmsbase.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=INVALIDLAYER&bbox=0,0,1,1&crs=EPSG:4326&width=10&height=10&exceptions=XML&format=image/png"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "LayerNotDefined"

class WMS13GetMapFormatUnknownFaultTestCase(wmsbase.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=MER_FRS_1P_reduced&bbox=-32,-4,46,28&crs=EPSG:4326&width=100&height=100&format=image/INVALID&exceptions=application/vnd.ogc.se_xml"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidFormat"
    
class WMS13GetMapInvalidBoundingBoxTestCase(wmsbase.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=MER_FRS_1P_reduced&bbox=1,2,3&crs=EPSG:4326&width=100&height=100&format=image/jpeg&exceptions=application/vnd.ogc.se_xml"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

class WMS13GetMapInvalidCRSTestCase(wmsbase.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=MER_FRS_1P_reduced&bbox=0,0,1,1&crs=INVALIDCRS&width=100&height=100&format=image/jpeg&exceptions=application/vnd.ogc.se_xml"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidCRS"

class WMS13GetMapReferenceableGridTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775", )
    bbox = (17.0, -36.0, 22.0, -32.0)
    width = 500
    height = 400

class WMS13GetMapReferenceableGridReprojectionTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775", )
    crs = "EPSG:32734"
    bbox = (122043.08622624225, 6008645.867004246, 594457.4634022854, 6459127.468615601)
    width = 472
    height = 451
    swap_axes = False

class WMS13GetMapDatasetSeriesTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("MER_FRS_1P_reduced_RGB",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)

class WMS13GetMapDatasetSeriesTimePointTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("MER_FRS_1P_reduced_RGB",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    time = "2006-08-30T10:09:49Z"

class WMS13GetMapDatasetSeriesTimeIntervalTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("MER_FRS_1P_reduced_RGB",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    time = "2006-08-01T00:00:00Z/2006-08-22T23:59:59Z"

class WMS13GetMapDatasetSeriesTimeIntervalBorderTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("MER_FRS_1P_reduced_RGB",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    time = "2006-08-01T00:00:00Z/2006-08-16T09:09:29Z"

#===============================================================================
# Outlines
#===============================================================================

class WMS13GetMapDatasetSeriesOutlinesTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("MER_FRS_1P_reduced_outlines",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)

class WMS13GetMapRectifiedStitchedMosaicOutlinesTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("mosaic_MER_FRS_1P_reduced_RGB_outlines",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)

class WMS13GetMapRectifiedStitchedMosaicOutlinesWhiteTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("mosaic_MER_FRS_1P_reduced_RGB_outlines",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    styles = ("white",)

class WMS13GetMapDatasetSeriesOutlinesTimeIntervalTestCase(wmsbase.WMS13GetMapTestCase):
    layers = ("MER_FRS_1P_reduced_RGB_outlines",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    time = "2006-08-16T09:09:29Z/2006-08-16T09:15:46Z"

#===============================================================================
# Bands
#===============================================================================

class WMS13GetMapDatasetOneBandTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset containing 15 bands. """
    layers = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed_bands",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)
    dim_bands = "MERIS_radiance_01_uint16"

class WMS13GetMapDatasetThreeBandsTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset containing 15 bands. """
    layers = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed_bands",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)
    dim_bands = "MERIS_radiance_02_uint16,MERIS_radiance_08_uint16,MERIS_radiance_12_uint16"

#===============================================================================
# Reprojected
#===============================================================================

class WMS13GetMapReprojectedDatasetTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a reprojected dataset. """
    fixtures = testbase.OWSTestCase.fixtures + ["meris_coverages_reprojected_uint16.json"]
    
    layers = ("MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)

#===============================================================================
# Dateline crossing
#===============================================================================

class WMS13GetMapCrossesDatelineDatasetTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with a reprojected dataset. """
    fixtures = testbase.BASE_FIXTURES + ["crosses_dateline.json"]
    
    layers = ("crosses_dateline",)
    bbox = (-180, -90, 180, 90)
    width = 200

#===============================================================================
# Masked
#===============================================================================

MASK_FIXTURES = wmsbase.WMS13GetMapTestCase.fixtures + ["meris_coverages_rgb_mask.json"]

class WMS13GetMapDatasetMaskedTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with the masked layer for a dataset. """
    fixtures = MASK_FIXTURES

    layers = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced_masked",)
    bbox = (11, 32, 28, 46) 

class WMS13GetMapDatasetSeriesMaskedTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with the masked layer for a dataset series. """
    fixtures = MASK_FIXTURES

    layers = ("MER_FRS_1P_reduced_RGB_masked",)
    bbox = (11, 32, 28, 46)

#===============================================================================
# Cloud Mask
#===============================================================================

class WMS13GetMapDatasetCloudMaskTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request for cloudmask of a dataset. """
    fixtures = MASK_FIXTURES

    layers = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced_clouds",)
    styles = ("magenta",)
    bbox = (11, 32, 28, 46) 

class WMS13GetMapDatasetSeriesCloudMaskTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request for cloudmask of a dataset series. """
    fixtures = MASK_FIXTURES

    layers = ("MER_FRS_1P_reduced_RGB_clouds",)
    styles = ("magenta",)
    bbox = (11, 32, 28, 46) 

#===============================================================================
# Masked Outlines
#===============================================================================

class WMS13GetMapDatasetMaskedOutlinesTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with the masked outlines layer for a dataset. """
    fixtures = MASK_FIXTURES

    layers = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced_masked_outlines",)
    bbox = (11, 32, 28, 46)

class WMS13GetMapDatasetSeriesMaskedTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request with the masked layer for a dataset series. """
    fixtures = MASK_FIXTURES

    layers = ("MER_FRS_1P_reduced_RGB_masked",)
    bbox = (11, 32, 28, 46)

#===============================================================================
# Styled Coverages
#===============================================================================

# currently disabled because of segfaults in MapServer

'''
class WMS13GetMapDatasetStyledTestCase(wmsbase.WMS13GetMapTestCase):
    """ Test a GetMap request a dataset with an associated style. """
    fixtures = wmsbase.WMS13GetMapTestCase.fixtures + [
        "cryo_range_type.json", "cryo_coverages.json"
    ]

    layers = ("FSC_0.0025deg_201303030930_201303031110_MOD_Alps_ENVEOV2.1.00",)
    bbox = (6, 44.5, 16, 48)
    width = 200
'''
#===============================================================================
# Feature Info
#===============================================================================

class WMS13GetFeatureInfoTestCase(testbase.HTMLTestCase):
    """ Test a GetFeatureInfo on an outline layer. """
    
    def getRequest(self):
        params = "SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS=MER_FRS_1P_reduced_RGB_outlines&QUERY_LAYERS=MER_FRS_1P_reduced_RGB_outlines&STYLES=&BBOX=32.158895,-3.75,46.3,28.326165&FEATURE_COUNT=10&HEIGHT=100&WIDTH=200&FORMAT=image%2Fpng&INFO_FORMAT=text/html&CRS=EPSG:4326&I=100&J=50";
        return (params, "kvp")

class WMS13GetFeatureInfoTimeIntervalTestCase(testbase.HTMLTestCase):
    """ Test a GetFeatureInfo on an outline layer with a given time slice. """
    
    def getRequest(self):
        params = "SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS=MER_FRS_1P_reduced_RGB_outlines&QUERY_LAYERS=MER_FRS_1P_reduced_RGB_outlines&STYLES=&BBOX=24.433594,-8.986816,60.205078,58.908691&FEATURE_COUNT=10&HEIGHT=814&WIDTH=1545&FORMAT=image%2Fpng&INFO_FORMAT=text/html&CRS=EPSG:4326&I=598&J=504&TIME=2006-08-16T09:09:29Z/2006-08-16T09:12:46Z";
        return (params, "kvp")


class WMS13GetFeatureInfoEmptyTestCase(testbase.HTMLTestCase):
    """ Test a GetFeatureInfo request not hitting any datasets because of spatial/temporal bounds. """
    
    def getRequest(self):
        params = "LAYERS=MER_FRS_1P_reduced_RGB_outlines&QUERY_LAYERS=MER_FRS_1P_reduced_RGB_outlines&STYLES=&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&EXCEPTIONS=INIMAGE&BBOX=20.742187%2C-19.401855%2C56.513672%2C48.493652&FEATURE_COUNT=10&HEIGHT=814&WIDTH=1545&FORMAT=image%2Fpng&INFO_FORMAT=text%2Fhtml&CRS=EPSG%3A4326&I=1038&J=505"
        return (params, "kvp")


class WMS13GetFeatureInfoMaskedOutlinesTestCase(testbase.HTMLTestCase):
    """ Test a GetFeatureInfo request on masked outlines layers. """
    fixtures = MASK_FIXTURES

    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetFeatureInfo&bbox=32,11,46,28&crs=EPSG:4326&width=500&height=500&format=png&TRANSPARENT=TRUE&styles=&layers=MER_FRS_1P_reduced_RGB_masked_outlines&info_format=text/plain&query_layers=MER_FRS_1P_reduced_RGB_masked_outlines&i=250&j=250&feature_count=10"
        return (params, "kvp")


class WMS13GetFeatureInfoEOOMTestCase(testbase.XMLTestCase):
    """ Test a GetFeatureInfo on an outline layer. """
    
    def getRequest(self):
        params = "SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS=MER_FRS_1P_reduced_RGB_outlines&QUERY_LAYERS=MER_FRS_1P_reduced_RGB_outlines&STYLES=&BBOX=32.158895,-3.75,46.3,28.326165&FEATURE_COUNT=10&HEIGHT=100&WIDTH=200&FORMAT=image%2Fpng&INFO_FORMAT=application/xml&CRS=EPSG:4326&I=100&J=50";
        return (params, "kvp")

#===============================================================================
# Legend Graphic
#===============================================================================

# currently disabled because of segfaults in MapServer


class WMS13GetLegendGraphicDatasetStyledTestCase(testbase.RasterTestCase):
    """ Test a GetLegendGraphic request for a dataset with an associated style. """
    
    fixtures = wmsbase.WMS13GetMapTestCase.fixtures + [
        "cryo_range_type.json", "cryo_coverages.json"
    ]

    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=FSC_0.0025deg_201303030930_201303031110_MOD_Alps_ENVEOV2.1.00&SLD_VERSION=1.1.0"
        return params, "kvp"

    def getFileExtension(self, file_type):
        return "png"
