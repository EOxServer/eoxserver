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


from lxml.builder import ElementMaker

from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap

ns_wms = NameSpace("http://www.opengis.net/wms")
ns_xlink = NameSpace("http://www.w3.org/1999/xlink", "xlink")
nsmap = NameSpaceMap(ns_wms, ns_xlink)

WMS = ElementMaker(namespace=ns_wms.uri, nsmap=nsmap)


class WMS13Encoder(XMLEncoder):
    def encode_capabilities(self, config, ows_url, srss, formats, info_formats,
                            layer_descriptions):
        return WMS("WMS_Capabilities",
            WMS("Service",
                WMS("Name", config.name),
                WMS("Title", config.title),
                WMS("Abstract", config.abstract),
                WMS("KeywordList", *[
                    WMS("Keyword", keyword)
                    for keyword in config.keywords
                ]),
                WMS("OnlineResource", config.onlineresource),

                WMS("ContactInformation",
                    WMS("ContactPersonPrimary",
                        WMS("ContactPerson", config.individual_name),
                        WMS("ContactOrganization",  config.provider_name),
                    ),
                    WMS("ContactPosition", config.position_name),
                    WMS("ContactAddress",
                        WMS("AddressType", "postal"),
                        WMS("Address", config.delivery_point),
                        WMS("City", config.city),
                        WMS("StateOrProvince", config.administrative_area),
                        WMS("PostCode", config.postal_code),
                        WMS("Country", config.country),
                    ),
                    WMS("ContactVoiceTelephone", config.phone_voice),
                    WMS("ContactFacsimileTelephone", config.phone_facsimile),
                    WMS("ContactElectronicMailAddress",
                        config.electronic_mail_address
                    ),
                ),
                WMS("Fees", config.fees),
                WMS("AccessConstraints", config.access_constraints),

                # TODO:
                # <LayerLimit>16</LayerLimit>
                # <MaxWidth>2048</MaxWidth>
                # <MaxHeight>2048</MaxHeight>
            ),
            WMS("Capability",
                WMS("Request",
                    WMS("GetCapabilities",
                        WMS("Format", "text/xml"),
                        self.encode_dcptype(ows_url)
                    ),
                    WMS("GetMap", *[
                            WMS("Format", frmt.mimeType)
                            for frmt in formats
                        ] + [
                            self.encode_dcptype(ows_url)
                        ]
                    ),
                    WMS("GetFeatureInfo",
                        WMS("Format",
                            # TODO
                        ),
                        self.encode_dcptype(ows_url)
                    ),
                    # TODO: describe layer?
                ),
                WMS("Exception",
                    WMS("Format", "XML"),
                    WMS("Format", "INIMAGE"),
                    WMS("Format", "BLANK"),
                ),
                WMS("Layer",
                    WMS("Title", config.title),
                    *([
                        WMS("CRS", srs)
                        for srs in srss
                    ] + [
                        self.encode_bbox(
                            minx="-180", miny="-90", maxx="180", maxy="90"
                        )
                    ] + [
                        self.encode_layer(layer_description)
                        for layer_description in layer_descriptions
                    ])
                )
            ),
            version="1.3.0", updateSequence=config.update_sequence
        )

    def encode_dcptype(self, ows_url):
        return WMS("DCPType",
            WMS("HTTP",
                WMS("Get",
                    WMS("OnlineResource", **{
                        ns_xlink("href"): ows_url,
                        ns_xlink("type"): "simple"
                    })
                )
            )
        )

    def encode_bbox(self, minx, miny, maxx, maxy):
        return WMS("EX_GeographicBoundingBox",
            WMS("westBoundLongitude", minx),
            WMS("eastBoundLongitude", maxx),
            WMS("southBoundLatitude", miny),
            WMS("northBoundLatitude", maxy),
        )

    def encode_layer(self, layer_description):
        elems = [
            WMS("Name", layer_description.name)
        ]

        title = getattr(layer_description, 'title')
        if title:
            elems.append(WMS("Title", title))

        if layer_description.bbox:
            bbox = list(map(str, layer_description.bbox))
            elems.append(
                self.encode_bbox(
                    minx=bbox[0], miny=bbox[1], maxx=bbox[2], maxy=bbox[3]
                )
            )

        elems.extend(
            WMS("Style",
                WMS("Name", style),
                WMS("Title", style),
                WMS("Abstract", style),
            ) for style in layer_description.styles
        )

        elems.extend(
            self.encode_layer(sub_layer)
            for sub_layer in layer_description.sub_layers
        )

        dimensions = []

        for dimension_name, dimension in layer_description.dimensions.items():
            if "min" in dimension and "max" in dimension and "step" in dimension:
                extent_text = "%s/%s/%s" % (
                    dimension["min"], dimension["max"], dimension["step"]
                )
            elif "values" in dimension:
                extent_text = ",".join(dimension["values"])

            dimension_elem = WMS("Dimension", extent_text, name=dimension_name)
            if "units" in dimension:
                dimension_elem.attrib["units"] = dimension["units"]

            if "default" in dimension:
                dimension_elem.attrib["default"] = dimension["default"]

            if dimension.get("multivalue"):
                dimension_elem.attrib["multipleValues"] = "1"

            dimensions.append(dimension_elem)

        elems.extend(dimensions)

        return WMS("Layer",
            *elems,
            queryable="1" if layer_description.queryable else "0"
        )
