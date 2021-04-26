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


from lxml.builder import E, ElementMaker

from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap

ns_xlink = NameSpace("http://www.w3.org/1999/xlink", "xlink")
nsmap = NameSpaceMap(ns_xlink)
E_WITH_XLINK = ElementMaker(nsmap=nsmap)


class WMS11Encoder(XMLEncoder):
    def encode_capabilities(self, config, ows_url, srss, formats, info_formats,
                            layer_descriptions):
        return E("WMT_MS_Capabilities",
            E("Service",
                E("Name", config.name),
                E("Title", config.title),
                E("Abstract", config.abstract),
                E("KeywordList", *[
                    E("Keyword", keyword)
                    for keyword in config.keywords
                ]),
                E("OnlineResource", config.onlineresource),

                E("ContactInformation",
                    E("ContactPersonPrimary",
                        E("ContactPerson", config.individual_name),
                        E("ContactOrganization",  config.provider_name),
                    ),
                    E("ContactPosition", config.position_name),
                    E("ContactAddress",
                        E("AddressType", "postal"),
                        E("Address", config.delivery_point),
                        E("City", config.city),
                        E("StateOrProvince", config.administrative_area),
                        E("PostCode", config.postal_code),
                        E("Country", config.country),
                    ),
                    E("ContactVoiceTelephone", config.phone_voice),
                    E("ContactFacsimileTelephone", config.phone_facsimile),
                    E("ContactElectronicMailAddress",
                        config.electronic_mail_address
                    ),
                ),
                E("Fees", config.fees),
                E("AccessConstraints", config.access_constraints),
            ),
            E("Capability",
                E("Request",
                    E("GetCapabilities",
                        E("Format", "application/vnd.ogc.wms_xml"),
                        self.encode_dcptype(ows_url)
                    ),
                    E("GetMap", *[
                            E("Format", frmt.mimeType)
                            for frmt in formats
                        ] + [
                            self.encode_dcptype(ows_url)
                        ]
                    ),
                    E("GetFeatureInfo",
                        E("Format",
                            # TODO
                        ),
                        self.encode_dcptype(ows_url)
                    ),
                    # TODO: describe layer?
                ),
                E("Exception",
                    E("Format", "application/vnd.ogc.se_xml"),
                    E("Format", "application/vnd.ogc.se_inimage"),
                    E("Format", "application/vnd.ogc.se_blank"),
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
            version="1.1.1", updateSequence=config.update_sequence
        )

    def encode_dcptype(self, ows_url):
        return E("DCPType",
            E("HTTP",
                E("Get",
                    E_WITH_XLINK("OnlineResource", **{
                        ns_xlink("href"): ows_url,
                        ns_xlink("type"): "simple"
                    })
                )
            )
        )

    def encode_layer(self, layer_description):
        elems = [
            E("Name", layer_description.name)
        ]

        title = getattr(layer_description, 'title')
        if title:
            elems.append(E("Title", title))

        if layer_description.bbox:
            bbox = [str(v) for v in layer_description.bbox]
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

        dimensions = []
        extents = []

        for dimension_name, dimension in layer_description.dimensions.items():
            dimension_elem = E("Dimension", name=dimension_name)
            if "units" in dimension:
                dimension_elem.attrib["units"] = dimension["units"]
            dimensions.append(dimension_elem)

            if "min" in dimension and "max" in dimension and "step" in dimension:
                extent_text = "%s/%s/%s" % (
                    dimension["min"], dimension["max"], dimension["step"]
                )
            elif "values" in dimension:
                extent_text = ",".join(dimension["values"])

            extent_elem = E("Extent", extent_text, name=dimension_name)

            if "default" in dimension:
                extent_elem.attrib["default"] = dimension["default"]

            if dimension.get("multivalue"):
                extent_elem.attrib["multipleValues"] = "1"

            extents.append(extent_elem)

        elems.extend(dimensions)
        elems.extend(extents)

        return E("Layer",
            *elems,
            queryable="1" if layer_description.queryable else "0"
        )
