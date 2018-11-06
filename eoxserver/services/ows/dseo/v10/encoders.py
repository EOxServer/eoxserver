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

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.common.v20.encoders import OWS20Encoder
from eoxserver.services.ows.common.v20.encoders import ns_xlink, ns_ows


ns_dseo = NameSpace("http://www.opengis.net/dseo/1.0", "dseo")
nsmap = NameSpaceMap(
    ns_xlink, ns_ows, ns_dseo
)

DSEO = ElementMaker(namespace=ns_dseo.uri, nsmap=nsmap)


class DSEO10CapabilitiesXMLEncoder(OWS20Encoder):
    def encode_capabilities(self, request, sections):
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        all_sections = "all" in sections
        caps = []
        if all_sections or "serviceidentification" in sections:
            caps.append(self.encode_service_identification(
                "DSEO", conf, []
            ))

        if all_sections or "serviceprovider" in sections:
            caps.append(self.encode_service_provider(conf))

        if all_sections or "operationsmetadata" in sections:
            caps.append(self.encode_operations_metadata(
                request, "DSEO", ["1.0.0"]
            ))

        return DSEO(
            "Capabilities", *caps,
            version="1.0.0", updateSequence=conf.update_sequence
        )
