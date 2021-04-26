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


from lxml.builder import E

from eoxserver.core.util.xmltools import XMLEncoder


class WMS10Encoder(XMLEncoder):
    def encode_capabilities(self, config, ows_url, srss, formats, info_formats,
                            layer_descriptions):

        mime_to_name = {
            "image/gif": "GIF",
            "image/png": "PNG",
            "image/jpeg": "JPEG",
            "image/tiff": "GeoTIFF",

        }

        return E("WMT_MS_Capabilities",
            E("Service",
                E("Name", config.name),
                E("Title", config.title),
                E("Abstract", config.abstract),
                E("Keywords", " ".join(config.keywords)),
                E("OnlineResource", config.onlineresource),
                E("Fees", config.fees),
                E("AccessConstraints", config.access_constraints),
            ),
            E("Capability",
                E("Request",
                    E("Map",
                        E("Format", *[
                                E(mime_to_name[frmt.mimeType])
                                for frmt in formats
                                if frmt.mimeType in mime_to_name
                            ]
                        ),
                        E("DCPType",
                            E("HTTP",
                                E("Get", onlineResource=ows_url)
                            )
                        )
                    ),
                    E("Capabilities",
                        E("Format",
                            E("WMS_XML")
                        ),
                        E("DCPType",
                            E("HTTP",
                                E("Get", onlineResource=ows_url)
                            )
                        )
                    ),
                    E("FeatureInfo",
                        E("Format",
                            # TODO
                        ),
                        E("DCPType",
                            E("HTTP",
                                E("Get", onlineResource=ows_url)
                            )
                        )
                    ),
                ),
                E("Exception",
                    E("Format",
                        E("BLANK"),
                        E("INIMAGE"),
                        E("WMS_XML")
                    ),
                ),
                E("Layer",
                    E("Title", config.title),
                    E("LatLonBoundingBox",
                        minx="-180", miny="-90", maxx="180", maxy="90"
                    ), *([
                        E("SRS", srs)
                        for srs in srss
                    ] + [
                        self.encode_layer(layer_description)
                        for layer_description in layer_descriptions
                    ])
                )
            ),
            version="1.0.0", updateSequence=config.update_sequence
        )

    def encode_layer(self, layer_description):
        elems = [
            E("Name", layer_description.name)
        ]

        title = getattr(layer_description, 'title')
        if title:
            elems.append(E("Title", title))

        if layer_description.bbox:
            bbox = list(map(str, layer_description.bbox))
            elems.append(
                E("LatLonBoundingBox",
                    minx=bbox[0], miny=bbox[1], maxx=bbox[2], maxy=bbox[3]
                )
            )

        elems.extend(
            E("Style",
                E("Name", style),
                E("Title", style),
                E("Abstract", style),
            ) for style in layer_description.styles
        )

        elems.extend(
            self.encode_layer(sub_layer)
            for sub_layer in layer_description.sub_layers
        )

        return E("Layer",
            *elems,
            queryable="1" if layer_description.queryable else "0"
        )
