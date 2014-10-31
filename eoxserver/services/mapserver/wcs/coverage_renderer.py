#-------------------------------------------------------------------------------
# $Id$
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


from datetime import datetime
from urllib import unquote
import logging

from lxml import etree

from eoxserver.core import implements, ExtensionPoint
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import models, crss
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.services.exceptions import NoSuchCoverageException
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.ows.wcs.v20.util import (
    ScaleSize, ScaleExtent, ScaleAxis
)
from eoxserver.services.mapserver.interfaces import (
    ConnectorInterface, LayerFactoryInterface
)
from eoxserver.services.subset import Subsets
from eoxserver.services.mapserver.wcs.base_renderer import (
    BaseRenderer, is_format_supported
)
from eoxserver.services.ows.version import Version
from eoxserver.services.result import result_set_from_raw_data, ResultBuffer
from eoxserver.services.exceptions import (
    RenderException, OperationNotSupportedException, 
    InterpolationMethodNotSupportedException
)


logger = logging.getLogger(__name__)

INTERPOLATION_TRANS = {
    "nearest-neighbour": "NEAREST",
    "linear": "BILINEAR",
    "bilinear": "BILINEAR",
    "cubic": "BICUBIC",
    "average": "AVERAGE"
}


class RectifiedCoverageMapServerRenderer(BaseRenderer):
    """ A coverage renderer for rectified coverages. Uses mapserver to process
        the request.
    """

    implements(WCSCoverageRendererInterface)

    # ReferenceableDatasets are not handled in WCS >= 2.0
    versions_full = (Version(1, 1), Version(1, 0))
    versions_partly = (Version(2, 0),)
    versions = versions_full + versions_partly

    handles_full = (
        models.RectifiedDataset,
        models.RectifiedStitchedMosaic,
        models.ReferenceableDataset
    )

    handles_partly = (models.RectifiedDataset, models.RectifiedStitchedMosaic)
    handles = handles_full + handles_partly

    connectors = ExtensionPoint(ConnectorInterface)
    layer_factories = ExtensionPoint(LayerFactoryInterface)

    def supports(self, params):
        return (
            (params.version in self.versions_full
            and issubclass(params.coverage.real_type, self.handles_full))
            or
            (params.version in self.versions_partly
            and issubclass(params.coverage.real_type, self.handles_partly))
        )

    def render(self, params):
        # get coverage related stuff
        coverage = params.coverage

        # ReferenceableDataset are not supported in WCS < 2.0
        if issubclass(coverage.real_type, models.ReferenceableDataset):
            raise NoSuchCoverageException((coverage.identifier,))

        data_items = self.data_items_for_coverage(coverage)

        range_type = coverage.range_type
        bands = list(range_type)

        subsets = params.subsets

        if subsets:
            srid = subsets.srid
            if srid is not None:
                if not crss.validateEPSGCode(srid):
                    raise RenderException(
                        "Failed to extract an EPSG code from the CRS URI "
                        "'%s'." % srid, "subset"
                    )

        # create and configure map object
        map_ = self.create_map()

        # configure outputformat
        native_format = self.get_native_format(coverage, data_items)
        if get_format_by_mime(native_format) is None:
            native_format = "image/tiff"

        frmt = params.format or native_format

        if frmt is None:
            raise RenderException("Format could not be determined", "format")

        mime_type, frmt = split_format(frmt)

        imagemode = ms.gdalconst_to_imagemode(bands[0].data_type)
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        basename = "%s_%s" % (coverage.identifier, time_stamp)
        of = create_outputformat(
            mime_type, frmt, imagemode, basename,
            getattr(params, "encoding_params", {})
        )

        map_.appendOutputFormat(of)
        map_.setOutputFormat(of)

        # TODO: use layer factory here
        layer = self.layer_for_coverage(coverage, native_format, params.version)

        map_.insertLayer(layer)

        for connector in self.connectors:
            if connector.supports(data_items):
                break
        else:
            raise OperationNotSupportedException(
                "Could not find applicable layer connector.", "coverage"
            )

        try:
            connector.connect(coverage, data_items, layer, {})
            # create request object and dispatch it against the map
            request = ms.create_request(
                self.translate_params(params, range_type)
            )
            request.setParameter("format", mime_type)
            raw_result = ms.dispatch(map_, request)

        finally:
            # perform any required layer related cleanup
            connector.disconnect(coverage, data_items, layer, {})

        result_set = result_set_from_raw_data(raw_result)

        if params.version == Version(2, 0):
            if getattr(params, "mediatype", None) in ("multipart/mixed", "multipart/related"):
                encoder = WCS20EOXMLEncoder()
                is_mosaic = issubclass(
                    coverage.real_type, models.RectifiedStitchedMosaic
                )

                if not is_mosaic:
                    tree = encoder.alter_rectified_dataset(
                        coverage, getattr(params, "http_request", None),
                        etree.parse(result_set[0].data_file).getroot(),
                        subsets.bounding_polygon(coverage) if subsets else None
                    )
                else:
                    tree = encoder.alter_rectified_stitched_mosaic(
                        coverage.cast(), getattr(params, "http_request", None),
                        etree.parse(result_set[0].data_file).getroot(),
                        subsets.bounding_polygon(coverage) if subsets else None
                    )

                result_set[0] = ResultBuffer(
                    encoder.serialize(tree), 
                    encoder.content_type
                )

        # "default" response
        return result_set

    def translate_params(self, params, range_type):
        """ "Translate" parameters to be understandable by mapserver.
        """
        if params.version.startswith("2.0"):
            for key, value in params:
                if key == "interpolation":
                    interpolation = INTERPOLATION_TRANS.get(value)
                    if not interpolation:
                        raise InterpolationMethodNotSupportedException(
                            "Interpolation method '%s' is not supported." 
                            % value
                        )
                    yield key, value

                else:
                    yield key, value

            rangesubset = params.rangesubset
            if rangesubset:
                yield "rangesubset", ",".join(
                    map(str, rangesubset.get_band_indices(range_type, 1))
                )

            # TODO: this only works in newer MapServer implementations 
            # (since 6.4?).
            SCALE_AVAILABLE = ms.msGetVersionInt() > 60401
            scalefactor = params.scalefactor
            if scalefactor is not None:
                if SCALE_AVAILABLE:
                    yield "scalefactor", str(scalefactor)
                else:
                    raise RenderException(
                        "'ScaleFactor' is not supported by MapServer in the "
                        "current version.", "scalefactor"
                    )


            for scale in params.scales:
                scaleaxes = []
                if isinstance(scale, ScaleSize):
                    yield "size", "%s(%d)" % (scale.axis, scale.size)
                elif isinstance(scale, ScaleExtent):
                    yield "size", "%s(%d)" % (scale.axis, scale.high-scale.low)
                elif isinstance(scale, ScaleAxis):
                    if SCALE_AVAILABLE:
                        scaleaxes.append(scale)
                    else:
                        raise RenderException(
                            "'ScaleAxes' is not supported by MapServer in the "
                            "current version.", "scaleaxes"
                        )

                if scaleaxes:
                    yield "scaleaxes", ",".join(
                        "%s(%f)" % (scale.axis, scale.value) 
                        for scale in scaleaxes
                    )

        else:
            for key, value in params:
                yield key, value


def split_format(frmt):
    parts = unquote(frmt).split(";")
    mime_type = parts[0]
    options = map(
        lambda kv: map(lambda i: i.strip(), kv.split("=")), parts[1:]
    )
    return mime_type, options
        

def create_outputformat(mime_type, options, imagemode, basename, parameters):
    """ Returns a ``mapscript.outputFormatObj`` for the given format name and 
        imagemode.
    """

    reg_format = get_format_by_mime(mime_type)

    if not reg_format:
        raise RenderException(
            "Unsupported output format '%s'." % mime_type, "format"
        )

    outputformat = ms.outputFormatObj(reg_format.driver, "custom")
    outputformat.name = reg_format.wcs10name
    outputformat.mimetype = reg_format.mimeType
    outputformat.extension = reg_format.defaultExt
    outputformat.imagemode = imagemode

    #for key, value in options:
    #    outputformat.setOption(str(key), str(value))

    if mime_type == "image/tiff":
        _apply_gtiff(outputformat, **parameters)


    filename = basename + reg_format.defaultExt
    outputformat.setOption("FILENAME", str(filename))

    return outputformat


def _apply_gtiff(outputformat, compression=None, jpeg_quality=None, 
                 predictor=None, interleave=None, tiling=False, 
                 tilewidth=None, tileheight=None):

    logger.info("Applying GeoTIFF parameters.")

    if compression:
        if compression.lower() == "huffman":
            compression = "CCITTRLE"
        outputformat.setOption("COMPRESS", str(compression.upper()))

    if jpeg_quality is not None:
        outputformat.setOption("JPEG_QUALITY", str(jpeg_quality))

    if predictor:
        pr = ["NONE", "HORIZONTAL", "FLOATINGPOINT"].index(predictor.upper())
        if pr == -1:
            raise ValueError("Invalid compression predictor '%s'." % predictor)
        outputformat.setOption("PREDICTOR", str(pr + 1))

    if interleave:
        outputformat.setOption("INTERLEAVE", str(interleave.upper()))

    if tiling:
        outputformat.setOption("TILED", "YES")
        if tilewidth is not None:
            outputformat.setOption("BLOCKXSIZE", str(tilewidth))
        if tileheight is not None:
            outputformat.setOption("BLOCKYSIZE", str(tileheight))


def get_format_by_mime(mime_type):
    """ Convenience function to return an enabled format descriptior for the 
        given mime type or WCS 1.0 format name. Returns ``None``, if none 
        applies.
    """

    registry = getFormatRegistry()
    reg_format = registry.getFormatByMIME(mime_type)

    if not reg_format:
        wcs10_frmts = registry.getFormatsByWCS10Name(mime_type)
        if wcs10_frmts:
            reg_format = wcs10_frmts[0]

    if reg_format and not is_format_supported(reg_format.mimeType):
        return None

    return reg_format
