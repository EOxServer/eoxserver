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

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.core.decoders import config


# default for EOXS_OPENSEARCH_FORMATS
DEFAULT_EOXS_OPENSEARCH_FORMATS = [
    'eoxserver.services.opensearch.formats.atom.AtomResultFormat',
    'eoxserver.services.opensearch.formats.rss.RSSResultFormat',
    'eoxserver.services.opensearch.formats.html.HTMLResultFormat',
    'eoxserver.services.opensearch.formats.kml.KMLResultFormat',
    'eoxserver.services.opensearch.formats.geojson.GeoJSONResultFormat',

]

DEFAULT_EOXS_RESULT_ITEM_FEED_LINK_GENERATORS = []

# default for EOXS_OPENSEARCH_EXTENSIONS
DEFAULT_EOXS_OPENSEARCH_EXTENSIONS = [
    'eoxserver.services.opensearch.extensions.eo.EarthObservationExtension',
    'eoxserver.services.opensearch.extensions.geo.GeoExtension',
    'eoxserver.services.opensearch.extensions.time.TimeExtension',
    'eoxserver.services.opensearch.extensions.cql.CQLExtension',
]

# default for EOXS_OPENSEARCH_SUMMARY_TEMPLATE
DEFAULT_EOXS_OPENSEARCH_SUMMARY_TEMPLATE = "opensearch/summary.html"

# default for the EOXS_OPENSEARCH_RECORD_MODEL
DEFAULT_EOXS_OPENSEARCH_RECORD_MODEL = "eoxserver.resources.coverages.models.EOObject"

# default ordering (field name) for opensearch queries
DEFAULT_EOXS_OPENSEARCH_DEFAULT_ORDERING = None

# when True, adds exceptions=text/html to all GetCoverage links in opensearch response
EOXS_OPENSEARCH_GETCOVERAGE_HTML_EXCEPTION = False

def get_opensearch_record_model():
    class_name = getattr(
        settings, 'EOXS_OPENSEARCH_RECORD_MODEL', DEFAULT_EOXS_OPENSEARCH_RECORD_MODEL
    )
    return import_string(class_name)


def get_opensearch_default_ordering():
    return getattr(
        settings,
        'EOXS_OPENSEARCH_DEFAULT_ORDERING',
        DEFAULT_EOXS_OPENSEARCH_DEFAULT_ORDERING
    )


class OpenSearchConfigReader(config.Reader):
    section = "services.opensearch"
    default_count = config.Option(type=int, default=100)
    max_count = config.Option(type=int, default=200)
