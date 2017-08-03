#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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


from django.db.models import Q

from eoxserver.core.decoders import kvp, enum
from eoxserver.core.util.xmltools import NameSpace
from eoxserver.core.util.timetools import parse_iso8601


class TimeExtension(object):
    """ Implementation of the OpenSearch `'Time' extension
    <http://www.opensearch.org/Specifications/OpenSearch/Extensions/Time/1.0/Draft_1>`_.
    """

    namespace = NameSpace(
        "http://a9.com/-/opensearch/extensions/time/1.0/", "time"
    )

    def filter(self, qs, parameters):
        decoder = TimeExtensionDecoder(parameters)

        start = decoder.start
        end = decoder.end
        relation = decoder.relation

        if start and end:
            if relation == "intersects":
                qs = qs.filter(Q(begin_time__lte=end) & Q(end_time__gte=start))
            elif relation == "contains":
                qs = qs.filter(Q(begin_time__lte=start) & Q(end_time__gte=end))
            elif relation == "during":
                qs = qs.filter(Q(begin_time__gte=start) & Q(end_time__lte=end))
            elif relation == "disjoint":
                qs = qs.filter(Q(begin_time__gt=end) | Q(end_time__lt=start))
            elif relation == "equals":
                qs = qs.filter(Q(begin_time=start) & Q(end_time=end))
        elif start:
            if relation == "intersects":
                qs = qs.filter(end_time__gte=start)
            elif relation == "contains":
                # not possible for a coverage to contain an open interval
                pass
            elif relation == "during":
                qs = qs.filter(begin_time__gte=start)
            elif relation == "disjoint":
                qs = qs.filter(end_time__lt=start)
            elif relation == "equals":
                qs = qs.filter(begin_time=start)
        elif end:
            if relation == "intersects":
                qs = qs.filter(begin_time__lte=end)
            elif relation == "contains":
                # see above
                pass
            elif relation == "during":
                qs = qs.filter(end_time__lte=end)
            elif relation == "disjoint":
                qs = qs.filter(begin_time__gt=end)
            elif relation == "equals":
                qs = qs.filter(end_time=end)
        return qs

    def get_schema(self, collection=None, model_class=None):
        return (
            dict(name="start", type="start"),
            dict(name="end", type="end"),
            dict(name="timerel", type="relation",
                options=["intersects", "contains", "disjoint", "equals"]
            )
        )


class TimeExtensionDecoder(kvp.Decoder):
    start = kvp.Parameter(num="?", type=parse_iso8601)
    end = kvp.Parameter(num="?", type=parse_iso8601)
    relation = kvp.Parameter(num="?",
        type=enum(("intersects", "contains", "disjoint", "equals"), False),
        default="intersects"
    )
