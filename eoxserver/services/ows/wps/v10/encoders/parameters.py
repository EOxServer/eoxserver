#-------------------------------------------------------------------------------
#
# WPS 1.0 common XML encoders
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

from eoxserver.services.ows.wps.parameters import (
    is_literal_type, LiteralData, ComplexData, BoundingBoxData, Format
)

from eoxserver.services.ows.wps.v10.util import (
    OWS, WPS, ns_ows, ns_wps, ns_xlink, ns_xml
)

#-------------------------------------------------------------------------------

def _encode_format(frmt):

    elem = WPS("Format",
        WPS("MimeType", frmt.mime_type)
    )

    if frmt.encoding:
        elem.append(WPS("Encoding", frmt.encoding))

    if frmt.encoding:
        elem.append(WPS("Schema", frmt.schema))


#-------------------------------------------------------------------------------

def _encode_literal(prm, is_input):

    elem = WPS("LiteralData" if is_input else "LiteralOutput")

    tname = prm.type_name

    if tname:
        tmp = {
            ns_ows("reference"): "http://www.w3.org/TR/xmlschema-2/#%s"%tname,
        }
        elem.append(OWS("DataType", tname, **tmp))

    if prm.uoms:
        elem.append(WPS("UOMs",
            WPS("Default", OWS("UOM", prm.uoms[0])),
            WPS("Supported", *((OWS("UOM", u) for u in prm.uoms)))
        ))

    if is_input:

        if prm.allowed_values:
            tmp = ((OWS("AllowedValue", str(v)) for v in prm.allowed_values))
            elem.append(OWS("AllowedValues", *tmp))

        elif prm.values_reference:
            tmp = {
                ns_ows("reference"): prm.values_reference,
                "valuesForm": prm.values_reference,
            }
            elem.append(WPS("ValuesReference", **tmp))

        else:
            elem.append(OWS("AnyValue"))

        if prm.default is not None:
            elem.append(WPS("Default", str(prm.default)))

    return elem

#-------------------------------------------------------------------------------

def _encode_complex(prm, is_input):

    formats = prm.formats

    if isinstance(formats, Format):
        formats = (formats,)

    return WPS("ComplexData" if is_input else "ComplexOutput",
        WPS("Default", _encode_format(formats[0])),
        WPS("Supported", *((_encode_format(f) for f in formats)))
    )

#-------------------------------------------------------------------------------

def _encode_bbox(prm, is_input):

    return WPS("BoundingBoxData" if is_input else "BoundingBoxOutput",
        WPS("Default", WPS("CRS", prm.crss[0])),
        WPS("Supported", *((WPS("CRS", c) for c in prm.crss)))
    )

#-------------------------------------------------------------------------------

def _encode_parameter(name, prm, is_input):

    # support for the shorthand
    if is_literal_type(prm):
        prm = LiteralData(name, prm)

    elem = WPS("Input" if is_input else "Output",
        OWS("Identifier", prm.identifier or name)
    )

    # TODO: minOccurs/maxOccurs correct
    # occurance attributes
    if is_input:
        elem.attrib["minOccurs"] = ("1", "0")[bool(prm._is_optional)]
        elem.attrib["maxOccurs"] = "1"

    if prm.title:
        elem.append(OWS("Title", prm.title))

    if prm.description:
        elem.append(OWS("Abstract", prm.description))


    if isinstance(prm, LiteralData):
        elem.append(_encode_literal(prm, is_input))

    elif isinstance(prm, ComplexData):
        elem.append(_encode_complex(prm, is_input))

    elif isinstance(prm, BoundingBoxData):
        elem.append(_encode_bbox(prm, is_input))

    return elem

#-------------------------------------------------------------------------------

def encode_input_def(name, parameter):
    """Encode input parameter definition."""
    return _encode_parameter(name, parameter, True)

def encode_output_def(name, parameter):
    """Encode output result definition."""
    return _encode_parameter(name, parameter, False)

