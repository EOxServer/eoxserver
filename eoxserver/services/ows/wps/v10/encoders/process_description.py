#-------------------------------------------------------------------------------
#
# WPS 1.0 ProcessDescriptsions XML encoders
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

from eoxserver.services.ows.wps.v10.util import (
    OWS, WPS, NIL, ns_wps, ns_xlink, ns_xml
)
from .parameters import encode_input_descr, encode_output_descr
from .base import WPS10BaseXMLEncoder
from eoxserver.services.ows.wps.parameters import fix_parameter


class WPS10ProcessDescriptionsXMLEncoder(WPS10BaseXMLEncoder):
    """ WPS 1.0 ProcessDescriptions XML response encoder. """

    @staticmethod
    def encode_process_descriptions(processes):
        """ Encode the ProcessDescriptions XML document. """
        _proc = [encode_process_full(p) for p in processes]
        _attr = {
            "service": "WPS",
            "version": "1.0.0",
            ns_xml("lang"): "en-US",
        }
        return WPS("ProcessDescriptions", *_proc, **_attr)


def encode_process_brief(process):
    """ Encode a brief process description (Process element) of the
    Capabilities XML document.
    """
    return _encode_process_brief(process, WPS("Process"))


def encode_process_full(process):
    """ Encode a full process description (ProcessDescription element) of the
    ProcessDescriptions XML document.
    """
    if getattr(process, 'asynchronous', False):
        supports_store = True
        supports_update = True
    else:
        supports_store = False
        supports_update = False

    # TODO: remove backward compatibility support for inputs/outputs dicts
    if isinstance(process.inputs, dict):
        process.inputs = process.inputs.items()
    if isinstance(process.outputs, dict):
        process.outputs = process.outputs.items()

    inputs = [
        item for item in (
            encode_input_descr(fix_parameter(n, p)) for n, p in process.inputs
        ) if item is not None
    ]
    outputs = [
        encode_output_descr(fix_parameter(n, p)) for n, p in process.outputs
    ]

    elem = _encode_process_brief(process, NIL("ProcessDescription"))
    if supports_store:
        elem.attrib["storeSupported"] = "true"
    if supports_update:
        elem.attrib["statusSupported"] = "true"
    elem.append(NIL("DataInputs", *inputs))
    elem.append(NIL("ProcessOutputs", *outputs))

    return elem


def _encode_process_brief(process, elem):
    """ Insert a brief process description into an XML element passed as the
    second argument.
    The brief process description is shared by both the Capabilities and
    ProcessDescriptions XML encoders.
    """
    identifier = getattr(process, 'identifier', type(process).__name__)
    title = getattr(process, 'title', identifier)
    abstract = getattr(process, 'description', process.__doc__)
    version = getattr(process, "version", "1.0.0")
    metadata = getattr(process, "metadata", {})
    profiles = getattr(process, "profiles", [])
    wsdl = getattr(process, "wsdl", None)

    elem.append(OWS("Identifier", identifier))
    elem.append(OWS("Title", title))
    elem.attrib[ns_wps("processVersion")] = version
    if abstract:
        elem.append(OWS("Abstract", abstract))
    elem.extend(_encode_metadata(k, metadata[k]) for k in metadata)
    elem.extend(WPS("Profile", profile) for profile in profiles)
    if wsdl:
        elem.append(WPS("WSDL", **{ns_xlink("href"): wsdl}))

    return elem


def _encode_metadata(title, href):
    """ Encode one Metadata element. """
    return OWS("Metadata", **{ns_xlink("title"): title, ns_xlink("href"): href})
