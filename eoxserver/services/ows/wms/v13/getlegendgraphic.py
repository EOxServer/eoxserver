#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

from eoxserver.core import Component, implements, UniqueExtensionPoint
from eoxserver.core.decoders import kvp, InvalidParameterException
from eoxserver.resources.coverages import models
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface
)
from eoxserver.services.ows.wms.util import LayerSelection
from eoxserver.services.ows.wms.interfaces import (
    WMSLegendGraphicRendererInterface
)
from eoxserver.services.result import to_http_response


class WMS13GetLegendGraphicHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)

    renderer = UniqueExtensionPoint(WMSLegendGraphicRendererInterface)

    service = "WMS"
    versions = ("1.3.0", "1.3")
    request = "GetLegendGraphic"

    def handle(self, request):
        decoder = WMS13GetLegendGraphicDecoder(request.GET)

        layer_name = decoder.layer
        coverage_id = decoder.coverage

        suffixes = self.renderer.suffixes
        for suffix in suffixes:
            try:
                if len(suffix or "") == 0:
                    identifier = layer_name
                else:
                    identifier = layer_name[-len(suffix):]
                eo_object = models.EOObject.objects.get(identifier=identifier)
                break
            except models.EOObject.DoesNotExist:
                pass
        else:
            raise InvalidParameterException(
                "No such layer '%s'." % layer_name, "layer"
            )

        if models.iscollection(eo_object):
            def recursive_lookup(collection, used_ids, suffix):
                eo_objects = models.EOObject.objects.filter(
                    collections__in=[collection.pk]
                ).exclude(
                    pk__in=used_ids
                )

                result = []
                for eo_object in eo_objects:
                    used_ids.add(eo_object.pk)

                    if models.iscoverage(eo_object):
                        result.append((eo_object.cast(), suffix))
                    elif models.iscollection(eo_object):
                        result.extend(
                            recursive_lookup(eo_object, used_ids, suffix)
                        )
                    else:
                        pass

                return result

            used_ids = set()
            coverages = recursive_lookup(eo_object, used_ids, suffix)
            collection = eo_object

            if coverage_id:
                for coverage in coverages:
                    if coverage.identifier == coverage_id:
                        coverages = ((coverage, suffix),)
                        break
                else:
                    raise InvalidParameterException(
                        "Layer '%s' does not contain a coverage with ID '%s'.",
                        "coverage"
                    )
        else:
            collection = None
            coverages = ((eo_object.cast(), suffix),)

        layer_selection = LayerSelection(
            collection if collection else None
        )
        layer_selection.extend(coverages)

        result, _ = self.renderer.render(layer_selection, request.GET.items())
        return to_http_response(result)


class WMS13GetLegendGraphicDecoder(kvp.Decoder):
    layer    = kvp.Parameter(num=1)
    coverage = kvp.Parameter(num="?")
