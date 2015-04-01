from django.db.models import Q

from eoxserver.core import Component, implements
from eoxserver.core.decoders import kvp, enum
from eoxserver.core.util.xmltools import NameSpace
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.services.opensearch.interfaces import SearchExtensionInterface


class TimeExtension(Component):
    implements(SearchExtensionInterface)

    namespace = NameSpace(
        "http://a9.com/-/opensearch/extensions/time/1.0/", "time"
    )

    schema = {
        "start": ("start", True),
        "end": ("end", True),
        "timerel": ("relation", True)
    }

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
                # TODO: not possible for a coverage to contain an open interval
                pass
                #qs = qs.filter(Q(begin_time__lte=start) & Q(end_time__gte=end))
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
                pass
                # TODO: see above
                #qs = qs.filter(Q(begin_time__lte=start) & Q(end_time__gte=end))
            elif relation == "during":
                qs = qs.filter(end_time__lte=end)
            elif relation == "disjoint":
                qs = qs.filter(begin_time__gt=end)
            elif relation == "equals":
                qs = qs.filter(end_time=end)
        return qs


class TimeExtensionDecoder(kvp.Decoder):
    start = kvp.Parameter(num="?", type=parse_iso8601)
    end = kvp.Parameter(num="?", type=parse_iso8601)
    relation = kvp.Parameter(num="?",
        type=enum(("intersects", "contains", "disjoint", "equals"), False),
        default="intersects"
    )
