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

from lxml import etree

from eoxserver.core import implements, ExtensionPoint
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.services.exceptions import NoSuchCoverageException
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.mapserver.interfaces import (
    ConnectorInterface, LayerFactoryInterface
)
from eoxserver.services.subset import Subsets
from eoxserver.services.mapserver.wcs.base_renderer import BaseRenderer
from eoxserver.services.ows.version import Version
from eoxserver.services.result import result_set_from_raw_data, ResultBuffer


class RectifiedCoverageMapServerRenderer(BaseRenderer):
    """ A coverage renderer for rectified coverages. Uses mapserver to process 
        the request.
    """

    implements(WCSCoverageRendererInterface)

    # ReferenceableDatasets are not handled in WCS >= 2.0
    versions_full = (Version(1, 1), Version(1, 0))
    versions_partly = (Version(2, 0),)
    versions = versions_full + versions_partly
    handles_full = (models.RectifiedDataset, models.RectifiedStitchedMosaic, models.ReferenceableDataset)
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
        subsets = Subsets(params.subsets)

        # create and configure map object
        map_ = self.create_map()

        # configure outputformat
        native_format = self.get_native_format(coverage, data_items)
        if get_format_by_mime(native_format) is None:
            native_format = "image/tiff"

        frmt = params.format or native_format

        if frmt is None:
            raise Exception("format could not be determined")

        mime_type, frmt = split_format(frmt)

        # TODO: imagemode
        imagemode = ms.gdalconst_to_imagemode(bands[0].data_type)
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        basename = "%s_%s" % (coverage.identifier, time_stamp)
        of = create_outputformat(mime_type, frmt, imagemode, basename)

        map_.appendOutputFormat(of)
        map_.setOutputFormat(of)

        # TODO: use layer factory here
        layer = self.layer_for_coverage(coverage, native_format, params.version)
        
        map_.insertLayer(layer)

        for connector in self.connectors:
            if connector.supports(data_items):
                break
        else:
            raise Exception("Could not find applicable layer connector.")

        try:
            connector.connect(coverage, data_items, layer)
            # create request object and dispatch it agains the map
            request = ms.create_request(params)
            request.setParameter("format", mime_type)
            raw_result = ms.dispatch(map_, request)

        finally:
            # perform any required layer related cleanup
            connector.disconnect(coverage, data_items, layer)

        result_set = result_set_from_raw_data(raw_result)

        if getattr(params, "mediatype", None) in ("multipart/mixed", "multipart/related"):
            encoder = WCS20EOXMLEncoder()
            result_set[0] = ResultBuffer(
                encoder.serialize(
                    encoder.alter_rectified_dataset(
                        coverage, getattr(params, "http_request", None), 
                        etree.parse(result_set[0].data_file).getroot(), 
                        subsets.bounding_polygon(coverage)
                    )
                ), 
                encoder.content_type
            )
            

        # "default" response
        return result_set


def split_format(frmt):
    parts = unquote(frmt).split(";")
    mime_type = parts[0]
    options = map(
        lambda kv: map(lambda i: i.strip(), kv.split("=")), parts[1:]
    )
    return mime_type, options
        

def create_outputformat(mime_type, options, imagemode, basename):
    """ Returns a ``mapscript.outputFormatObj`` for the given format name and 
        imagemode.
    """

    reg_format = get_format_by_mime(mime_type)

    if not reg_format:
        raise Exception("Unsupported output format '%s'." % frmt)

    outputformat = ms.outputFormatObj(reg_format.driver, "custom")
    outputformat.name = reg_format.wcs10name
    outputformat.mimetype = reg_format.mimeType
    outputformat.extension = reg_format.defaultExt
    outputformat.imagemode = imagemode

    for key, value in options:
        outputformat.setOption(str(key), str(value))

    filename = basename + reg_format.defaultExt
    outputformat.setOption("FILENAME", str(filename))

    return outputformat


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

    return reg_format
