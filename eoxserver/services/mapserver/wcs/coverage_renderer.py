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

from eoxserver.core import implements, ExtensionPoint
from eoxserver.contrib.mapserver import (
    create_request, outputFormatObj, gdalconst_to_imagemode, 
)
from eoxserver.backends.cache import CacheContext
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.mapserver.interfaces import (
    ConnectorInterface, LayerFactoryInterface
)
from eoxserver.services.mapserver.wcs.base_renderer import BaseRenderer
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.formats import getFormatRegistry


class RectifiedCoverageMapServerRenderer(BaseRenderer):
    implements(WCSCoverageRendererInterface)

    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic)

    connectors = ExtensionPoint(ConnectorInterface)
    layer_factories = ExtensionPoint(LayerFactoryInterface)


    def render(self, coverage, request_values):
        with CacheContext() as cache:
            return self._render(coverage, request_values, cache)

    def _render(self, coverage, request_values, cache):
        # get coverage related stuff
        
        data_items = self.data_items_for_coverage(coverage)

        range_type = coverage.range_type
        bands = list(range_type)

        # create and configure map object
        map_ = self.create_map()

        # configure outputformat
        native_format = self.get_native_format(coverage, data_items)
        format = self.find_param(request_values, "format", native_format)

        if format is None:
            raise Exception("format could not be determined")

        # TODO: imagemode
        imagemode = gdalconst_to_imagemode(bands[0].data_type)
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        basename = "%s_%s" % (coverage.identifier, time_stamp) 
        of = create_outputformat(format, imagemode, basename)
        map_.appendOutputFormat(of)
        map_.setOutputFormat(of)

        # TODO: use layer factory here
        layer = self.layer_for_coverage(coverage, native_format)
        
        map_.insertLayer(layer)

        for connector in self.connectors:
            if connector.supports(data_items):
                break
        else:
            raise Exception("Could not find applicable layer connector.")

        try:
            connector.connect(coverage, data_items, layer, cache)
            # create request object and dispatch it agains the map
            request = create_request(request_values)
            response = map_.dispatch(request)

        finally:
            # perform any required layer related cleanup
            connector.disconnect(coverage, data_items, layer, cache)

        if self.find_param(request_values, "mediatype") in ("multipart/mixed", "multipart/related"):
            # TODO: change the response XML
            #encoder = WCS20EOXMLEncoder()
            #return , mediatype
            pass

        # "default" response
        return response.content, response.content_type
        


def create_outputformat(frmt, imagemode, basename):
    parts = unquote(frmt).split(";")
    mime_type = parts[0]
    options = map(
        lambda kv: map(lambda i: i.strip(), kv.split("=")), parts[1:]
    )

    registry = getFormatRegistry()
    reg_format = registry.getFormatByMIME(mime_type) 

    if not reg_format:
        wcs10_frmts = registry.getFormatsByWCS10Name(mime_type)
        if wcs10_frmts:
            reg_format = wcs10_frmts[0]

    if not reg_format:
        raise Exception("Unsupported output format '%s'." % frmt)

    outputformat = outputFormatObj(reg_format.driver, "custom")
    outputformat.name = reg_format.wcs10name
    outputformat.mimetype = reg_format.mimeType
    outputformat.extension = reg_format.defaultExt
    outputformat.imagemode = imagemode

    for key, value in options:
        print key, value
        outputformat.setOption(key, value)

    filename = basename + reg_format.defaultExt
    outputformat.setOption("FILENAME", str(filename))

    return outputformat


def pop_request_value(request_values, key, default=None):
    for request_value in request_values:
        if key == request_value[0]:
            request_values.remove(request_value)
            return request_values[1]
    return default
