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

from eoxserver.core.decoders import (
    kvp, xml, enum, value_range, boolean, InvalidParameterException
)
from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap
from eoxserver.services.ows.wcs.v20.util import ns_wcs

class CompressionNotSupported(InvalidParameterException):
    code = "CompressionNotSupported"


class CompressionInvalid(InvalidParameterException):
    code = "CompressionInvalid"

class JpegQualityInvalid(InvalidParameterException):
    code = "JpegQualityInvalid"

class PredictorInvalid(InvalidParameterException):
    code = "PredictorInvalid"

class PredictorNotSupported(InvalidParameterException):
    code = "PredictorNotSupported"


class InterleavingInvalid(InvalidParameterException):
    code =  "InterleavingInvalid"

class TilingInvalid(InvalidParameterException):
    code = "TilingInvalid"

def parse_jpeg_quality(value):

    value = int(value)
    if value < 1 or value > 100:
        raise JpegQualityInvalid(
            "geotiff:jpeg_quality should be an integer between 1 and 100",
            "geotiff:jpeg_quality")
    return value

class WCS20GeoTIFFEncodingExtension(object):
    def supports(self, frmt, options):
        # To allow "native" GeoTIFF formats aswell
        if not frmt:
            return True
        return frmt.lower() == "image/tiff"

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GeoTIFFEncodingExtensionKVPDecoder(request.GET)
        else:
            return WCS20GeoTIFFEncodingExtensionXMLDecoder(request.body)

    def get_encoding_params(self, request):
        decoder = self.get_decoder(request)

        # perform some dependant value checking
        compression = decoder.compression
        predictor = decoder.predictor
        jpeg_quality = decoder.jpeg_quality
        tiling = decoder.tiling
        tileheight = decoder.tileheight
        tilewidth = decoder.tilewidth

        if predictor and compression not in ("LZW", "Deflate"):
            raise PredictorNotSupported(
                "geotiff:predictor requires compression method 'LZW' or "
                "'Deflate'.", "geotiff:predictor"
            )

        if jpeg_quality is not None:  
            if compression != "JPEG":
                raise CompressionNotSupported(
                    "geotiff:jpeg_quality requires compression method 'JPEG'.",
                    "geotiff:jpeg_quality"
                )
            else :
                parse_jpeg_quality(jpeg_quality)

        if tiling and (tileheight is None or tilewidth is None):
            raise TilingInvalid(
                "geotiff:tiling requires geotiff:tilewidth and "
                "geotiff:tileheight to be set.", "geotiff:tiling"
            )

        return {
            "compression": compression,
            "jpeg_quality": jpeg_quality,
            "predictor": predictor,
            "interleave": decoder.interleave,
            "tiling": tiling,
            "tileheight": tileheight,
            "tilewidth": tilewidth
        }


compression_enum = enum(
    ("None", "PackBits", "Huffman", "LZW", "JPEG", "Deflate"), True, CompressionInvalid
)
predictor_enum = enum(("None", "Horizontal", "FloatingPoint"), True, PredictorInvalid)
interleave_enum = enum(("Pixel", "Band"), True, InterleavingInvalid)

def parse_multiple_16(raw):
    value = int(raw)
    if value < 0:
        raise ValueError("Value must be a positive integer.")
    elif (value % 16) != 0:
        raise ValueError("Value must be a multiple of 16.")
    return value


class WCS20GeoTIFFEncodingExtensionKVPDecoder(kvp.Decoder):
    compression = kvp.Parameter("geotiff:compression", num="?", type=compression_enum)
    jpeg_quality = kvp.Parameter("geotiff:jpeg_quality", num="?", type=int)
    predictor   = kvp.Parameter("geotiff:predictor", num="?", type=predictor_enum)
    interleave  = kvp.Parameter("geotiff:interleave", num="?", type=interleave_enum)
    tiling      = kvp.Parameter("geotiff:tiling", num="?", type=boolean)
    tileheight  = kvp.Parameter("geotiff:tileheight", num="?", type=parse_multiple_16)
    tilewidth   = kvp.Parameter("geotiff:tilewidth", num="?", type=parse_multiple_16)


class WCS20GeoTIFFEncodingExtensionXMLDecoder(xml.Decoder):
    compression = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:compression/text()", num="?", type=compression_enum, locator="geotiff:compression")
    jpeg_quality = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:jpeg_quality/text()", num="?", type=int, locator="geotiff:jpeg_quality")
    predictor   = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:predictor/text()", num="?", type=predictor_enum, locator="geotiff:predictor")
    interleave  = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:interleave/text()", num="?", type=interleave_enum, locator="geotiff:interleave")
    tiling      = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:tiling/text()", num="?", type=boolean, locator="geotiff:tiling")
    tileheight  = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:tileheight/text()", num="?", type=parse_multiple_16, locator="geotiff:tileheight")
    tilewidth   = xml.Parameter("wcs:Extension/geotiff:parameters/geotiff:tilewidth/text()", num="?", type=parse_multiple_16, locator="geotiff:tilewidth")

    namespaces = NameSpaceMap(
        ns_wcs, NameSpace("http://www.opengis.net/gmlcov/geotiff/1.0", "geotiff")
    )
