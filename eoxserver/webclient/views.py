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
from itertools import chain

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.timezone import now

from eoxserver.core.util.timetools import isoformat
from eoxserver.resources.coverages import models


logger = logging.getLogger(__name__)


def index(request):
    return render_to_response(
        'webclient/index.html', {
            "path": request.path,
        },
        context_instance=RequestContext(request)
    )


def configuration(request):
    collections = models.Collection.objects.all()
    coverages = filter(
        lambda c: not models.iscollection(c),
        models.Coverage.objects.filter(
            visible=True, collections__isnull=True
        )
    )

    all_objects = list(chain(collections, coverages))
    try:
        start_time = min(o.begin_time for o in all_objects if o.begin_time)
        end_time = max(o.end_time for o in all_objects if o.end_time)
    except ValueError:
        start_time = now() - timedelta(days=5)
        end_time = now()

    return render_to_response(
        'webclient/config.json', {
            "layers": all_objects,
            "start_time_full": isoformat(start_time - timedelta(days=5)),
            "end_time_full": isoformat(end_time + timedelta(days=5)),
            "start_time": isoformat(start_time),
            "end_time": isoformat(end_time)
        },
        context_instance=RequestContext(request)
    )
