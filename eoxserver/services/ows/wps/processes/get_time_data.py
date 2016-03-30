#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

import csv
from datetime import datetime

from eoxserver.core import Component, implements
from eoxserver.core.util.timetools import isoformat

from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, CDAsciiTextBuffer, FormatText
)
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError

from eoxserver.resources.coverages import models


class GetTimeDataProcess(Component):
    """ GetTimeDataProcess defines a WPS process needed by the EOxClient
        time-slider componenet """

    implements(ProcessInterface)

    identifier = "getTimeData"
    title = "Get times of collection coverages."
    decription = ("Query collection and get list of coverages and their times "
                  "and spatial extents. The process is used by the time-slider "
                  "of the EOxClient (web client).")

    metadata = {}
    profiles = ['EOxServer:GetTimeData']

    inputs = {
        "collection": LiteralData("collection",
            title="Collection name (a.k.a. dataset-series identifier)."),
        "begin_time": LiteralData("begin_time", datetime, optional=True,
            title="Optional start of the time interval."),
        "end_time": LiteralData("end_time", datetime, optional=True,
            title="Optional end of the time interval."),
    }

    outputs = {
        "times": ComplexData("times",
                    formats=(FormatText('text/csv'), FormatText('text/plain')),
                    title="Comma separated list of collection's coverages, "
                          "their extents and times.",
                    abstract="NOTE: The use of the 'text/plain' format is "
                             "deprecated! This format will be removed!'"
                )
    }

    @staticmethod
    def execute(collection, begin_time, end_time, **kwarg):
        """ The main execution function for the process.
        """

        # get the dataset series matching the requested ID
        try:
            model = models.EOObject.objects.get(identifier=collection)
        except models.EOObject.DoesNotExist:
            raise InvalidInputValueError(
                "collection", "Invalid collection name '%s'!" % collection
            )

        if models.iscollection(model):
            model = model.cast()

            # recursive dataset series lookup
            def _get_children_ids(ds):
                ds_rct = ds.real_content_type
                id_list = [ds.id]
                for child in model.eo_objects.filter(real_content_type=ds_rct):
                    id_list.extend(_get_children_ids(child))
                return id_list

            collection_ids = _get_children_ids(model)

            # prepare coverage query set
            coverages_qs = models.Coverage.objects.filter(
                collections__id__in=collection_ids
            )
            if end_time is not None:
                coverages_qs = coverages_qs.filter(begin_time__lte=end_time)
            if begin_time is not None:
                coverages_qs = coverages_qs.filter(end_time__gte=begin_time)
            coverages_qs = coverages_qs.order_by('begin_time', 'end_time')
            coverages_qs = coverages_qs.values_list("begin_time", "end_time", "identifier", "min_x", "min_y", "max_x", "max_y")

        else:
            min_x, min_y, max_x, max_y = model.extent_wgs84
            coverages_qs = ((model.begin_time, model.end_time, model.identifier, min_x, min_y, max_x, max_y),)

        # create the output
        output = CDAsciiTextBuffer()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        header = ["starttime", "endtime", "bbox", "identifier"]
        writer.writerow(header)

        for starttime, endtime, identifier, min_x, min_y, max_x, max_y in coverages_qs:
            bbox = (min_x, min_y, max_x, max_y)
            writer.writerow([isoformat(starttime), isoformat(endtime), bbox, identifier])

        return output
