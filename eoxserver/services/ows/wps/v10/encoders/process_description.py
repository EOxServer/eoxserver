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
    OWS, WPS, ns_ows, ns_wps, ns_xlink, ns_xml
)
from .parameters import encode_input_def, encode_output_def
from .base import WPS10BaseXMLEncoder


def encode_process_brief(process):
    id_ = getattr(process, 'identifier', process.__class__.__name__)
    title = getattr(process, 'title', id_)
    descr = getattr(process, 'description', process.__class__.__doc__)

    elem = WPS("Process",
        OWS("Identifier", id_),
        OWS("Title", title),
        OWS("Abstract", descr),
    )

    # TODO: Fix the metadata encoding to be compliant with the OWC common!
    #elem.extend([
    #    OWS("Metadata", metadata)
    #    for metadata in getattr(process, "metadata", [])
    #])

    elem.extend(OWS("Profile", p) for p in getattr(process, "profiles", []))

    version = getattr(process, "version", None)
    if version:
        elem.attr[ns_wps("processVersion")] = version

    return elem


def encode_process_full(process):
    elem = encode_process_brief(process)

    inputs = (encode_input_def(n, p) for n, p in process.inputs.items())
    outputs = (encode_output_def(n, p) for n, p in process.outputs.items())

    elem.append(WPS("DataInputs", *inputs))
    elem.append(WPS("DataOutputs", *outputs))

    return elem


class WPS10ProcessDescriptionsXMLEncoder(WPS10BaseXMLEncoder):
    @staticmethod
    def encode_process_descriptions(processes):
        tmp = (encode_process_full(p) for p in processes)
        return WPS("ProcessDescriptions", *tmp)
