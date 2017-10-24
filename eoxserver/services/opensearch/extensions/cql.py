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

from eoxserver.core.decoders import kvp
from eoxserver.core.util.xmltools import NameSpace
from eoxserver.services import filters, ecql


class CQLExtension(object):
    """ Implementation of the OpenSearch `'EO' extension
    <http://docs.opengeospatial.org/is/13-026r8/13-026r8.html>`_.
    """

    namespace = NameSpace(
        "http://a9.com/-/opensearch/extensions/cql/1.0/", "cql"
    )

    def filter(self, qs, parameters):
        mapping, mapping_choices = filters.get_field_mapping_for_model(qs.model)
        decoder = CQLExtensionDecoder(parameters)

        cql_text = decoder.cql
        if cql_text:
            ast = ecql.parse(cql_text)
            filter_expressions = ecql.to_filter(ast, mapping, mapping_choices)

            qs = qs.filter(filter_expressions)

        return qs

    def get_schema(self, collection=None, model_class=None):
        return (
            dict(name="cql", type="cql", profiles=[
                dict(
                    href="http://www.opengis.net/csw/3.0/cql",
                    title=(
                        "CQL (Common Query Language) is a query language "
                        "created by the OGC for the Catalogue Web Services "
                        "specification."
                    )
                )
            ]),
        )


class CQLExtensionDecoder(kvp.Decoder):
    cql = kvp.Parameter(num="?", type=str)
