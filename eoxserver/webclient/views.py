#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

import logging
from datetime import timedelta

from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Q, Max, Min

from eoxserver.core.util.timetools import isoformat
from eoxserver.resources.coverages import models


logger = logging.getLogger(__name__)


def index(request):
    return render(
        request, 'webclient/index.html', {
            "path": request.path,
        }
    )


def configuration(request):
    # select collections or coverages not contained in collections that are
    # visible
    qs = models.EOObject.objects.filter(
        Q(collection__isnull=False) |
        Q(mosaic__isnull=False) |
        Q(
            coverage__isnull=False,
            coverage__service_visibility__service="wc",
            coverage__service_visibility__visibility=True,
        )
    )

    # get the min/max values for begin and end time
    values = qs.aggregate(Min("begin_time"), Max("end_time"))
    start_time = values["begin_time__min"] or now() - timedelta(days=5)
    end_time = values["end_time__max"] or now()
    start_time_full = start_time - timedelta(days=5)
    end_time_full = end_time + timedelta(days=5)

    # try:
    #     # get only coverages that are in a collection or are visible
    #     # limit them to 10 and select the first time, so that we can limit the
    #     # initial brush
    #     coverages_qs = models.EOObject.objects.filter(
    #         Q(collection__isnull=True),
    #         Q(collections__isnull=False) | Q(coverage__visible=True)
    #     )
    #     first = list(coverages_qs.order_by("-begin_time")[:10])[-1]
    #     start_time = first.begin_time
    # except (models.EOObject.DoesNotExist, IndexError):
    #     pass

    return render(
        request, 'webclient/config.json', {
            "layers": qs,
            "start_time_full": isoformat(start_time_full),
            "end_time_full": isoformat(end_time_full),
            "start_time": isoformat(start_time),
            "end_time": isoformat(end_time)
        }
    )
