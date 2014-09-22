#-------------------------------------------------------------------------------
#
# WPS 1.0 parameters' XML encoders
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
    LiteralData, ComplexData, BoundingBoxData,
    AllowedAny, AllowedEnum, AllowedRange, AllowedRangeCollection,
    AllowedByReference,
)

from eoxserver.services.ows.wps.v10.util import (
    OWS, WPS, NIL, ns_ows,
)

#-------------------------------------------------------------------------------

def encode_input_descr(prm):
    """ Encode process description input."""
    elem = NIL("Input", *_encode_param_common(prm))
    elem.attrib["minOccurs"] = ("1", "0")[bool(prm.is_optional)]
    elem.attrib["maxOccurs"] = "1"
    if isinstance(prm, LiteralData):
        elem.append(_encode_literal(prm, True))
    elif isinstance(prm, ComplexData):
        elem.append(_encode_complex(prm, True))
    elif isinstance(prm, BoundingBoxData):
        elem.append(_encode_bbox(prm, True))
    return elem

def encode_output_descr(prm):
    """ Encode process description output."""
    elem = NIL("Output", *_encode_param_common(prm))
    if isinstance(prm, LiteralData):
        elem.append(_encode_literal(prm, False))
    elif isinstance(prm, ComplexData):
        elem.append(_encode_complex(prm, False))
    elif isinstance(prm, BoundingBoxData):
        elem.append(_encode_bbox(prm, False))
    return elem

def encode_input_exec(prm):
    """ Encode common part of the execure response data input."""
    return WPS("Input", *_encode_param_common(prm, False))

def encode_output_exec(prm):
    """ Encode common part of the execure response data output."""
    return WPS("Output", *_encode_param_common(prm))

def encode_output_def(outdef):
    """ Encode the execure response output definition."""
    attrib = {}
    if outdef.uom is not None:
        attrib['uom'] = outdef.uom
    if outdef.crs is not None:
        attrib['crs'] = outdef.crs
    if outdef.mime_type is not None:
        attrib['mimeType'] = outdef.mime_type
    if outdef.encoding is not None:
        attrib['encoding'] = outdef.encoding
    if outdef.schema is not None:
        attrib['schema'] = outdef.schema
    if outdef.as_reference is not None:
        attrib['asReference'] = 'true' if outdef.as_reference else 'false'
    return WPS("Output", *_encode_param_common(outdef, False), **attrib)

def _encode_param_common(prm, title_required=True):
    """ Encode common sub-elements of all XML parameters."""
    elist = [OWS("Identifier", prm.identifier)]
    if prm.title or title_required:
        elist.append(OWS("Title", prm.title or prm.identifier))
    if prm.abstract:
        elist.append(OWS("Abstract", prm.abstract))
    return elist

#-------------------------------------------------------------------------------

def _encode_literal(prm, is_input):
    dtype = prm.dtype
    elem = NIL("LiteralData" if is_input else "LiteralOutput")

    elem.append(OWS("DataType", dtype.name, **{
        ns_ows("reference"): "http://www.w3.org/TR/xmlschema-2/#%s"%dtype.name,
    }))

    if prm.uoms:
        elem.append(NIL("UOMs",
            NIL("Default", OWS("UOM", prm.uoms[0])),
            NIL("Supported", *[OWS("UOM", u) for u in prm.uoms])
        ))

    if is_input:
        elem.append(_encode_allowed_value(prm.allowed_values))

        if prm.default is not None:
            elem.append(NIL("DefaultValue", str(prm.default)))

    return elem

def _encode_allowed_value(avobj):
    enum, ranges, elist = None, [], []

    if isinstance(avobj, AllowedAny):
        return OWS("AnyValue")
    elif isinstance(avobj, AllowedByReference):
        return WPS("ValuesReference", **{
            ns_ows("reference"): avobj.url,
            "valuesForm": avobj.url,
        })
    elif isinstance(avobj, AllowedEnum):
        enum = avobj
    elif isinstance(avobj, AllowedRange):
        ranges = [avobj]
    elif isinstance(avobj, AllowedRangeCollection):
        enum, ranges = avobj.enum, avobj.ranges
    else:
        raise TypeError("Invalid allowed value object! OBJ=%r"%avobj)

    dtype = avobj.dtype
    ddtype = dtype.get_diff_dtype()

    if enum is not None:
        elist.extend(OWS("Value", dtype.encode(v)) for v in enum.values)
    for range_ in ranges:
        attr, elms = {}, []
        if range_.closure != 'closed':
            attr = {ns_ows("rangeClosure"): range_.closure}
        if range_.minval is not None:
            elms.append(OWS("MinimumValue", dtype.encode(range_.minval)))
        if range_.maxval is not None:
            elms.append(OWS("MaximumValue", dtype.encode(range_.maxval)))
        if range_.spacing is not None:
            elms.append(OWS("Spacing", ddtype.encode(range_.spacing)))
        elist.append(OWS("Range", *elms, **attr))

    return OWS("AllowedValues", *elist)

#-------------------------------------------------------------------------------

def _encode_complex(prm, is_input):
    return NIL("ComplexData" if is_input else "ComplexOutput",
        NIL("Default", _encode_format(prm.default_format)),
        NIL("Supported", *[_encode_format(f) for f in prm.formats.itervalues()])
    )

def _encode_format(frmt):
    elem = NIL("Format", NIL("MimeType", frmt.mime_type))
    if frmt.encoding is not None:
        elem.append(NIL("Encoding", frmt.encoding))
    if frmt.schema is not None:
        elem.append(NIL("Schema", frmt.schema))
    return elem

#-------------------------------------------------------------------------------

def _encode_bbox(prm, is_input):
    return NIL("BoundingBoxData" if is_input else "BoundingBoxOutput",
        NIL("Default", NIL("CRS", prm.encode_crs(prm.default_crs))),
        NIL("Supported", *[NIL("CRS", prm.encode_crs(crs)) for crs in prm.crss])
    )

