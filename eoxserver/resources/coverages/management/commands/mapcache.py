# -----------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import logging
from os import remove
from os.path import abspath, exists
import traceback
from sqlite3 import dbapi2
import textwrap

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime, parse_time
from django.contrib.gis.db.models import Extent

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


logger = logging.getLogger(__name__)


def decoder(conv_func):
    """
    Convert bytestrings from Python's sqlite3 interface to a regular string.
    """
    return lambda s: conv_func(s.decode())


dbapi2.register_converter("bool", b'1'.__eq__)
dbapi2.register_converter("time", decoder(parse_time))
dbapi2.register_converter("datetime", decoder(parse_datetime))
dbapi2.register_converter("timestamp", decoder(parse_datetime))
dbapi2.register_converter("TIMESTAMP", decoder(parse_datetime))


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    help = ("Synchronizes the MapCache SQLite DB holding times and extents.")

    def add_arguments(self, parser):
        sync_parser = self.add_subparser(parser, 'sync')
        sync_parser.add_argument(
            "--force", "-f",
            dest="force", action="store_true", default=False,
            help=(
                "Optional. Force the re-generation of the database file if "
                "it already exists."
            )
        )
        sync_parser.add_argument(
            "--unique-times", "-u",
            dest="unique_times", action="store_true", default=False,
            help=(
                "Optional. Force unique time entries. Extents are merged."
            )
        )
        sync_parser.add_argument(
            "--no-index",
            dest="index", action="store_false", default=True,
            help=(
                "Optional. Do not create an index."
            )
        )

    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: register, deregister.
        """
        if subcommand == "sync":
            self.handle_sync(*args, **kwargs)

    def handle_sync(self, force, unique_times=False, index=True, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))

        logger.info(
            "Starting synchronization of MapCache SQLite DB holding "
            "times and extents."
        )

        create_sql = textwrap.dedent('''
            CREATE TABLE "time" (
                "start_time" timestamp with time zone NOT NULL,
                "end_time" timestamp with time zone NOT NULL,
                "minx" double precision NOT NULL,
                "miny" double precision NOT NULL,
                "maxx" double precision NOT NULL,
                "maxy" double precision NOT NULL
            )
        ''')

        for collection in models.Collection.objects.all():
            db_path = abspath("%s.sqlite" % collection.identifier)
            if exists(db_path):
                if force:
                    logger.info("Deleting old MapCache SQLite file.")
                    remove(db_path)
                else:
                    logger.error("MapCache SQLite exists.")
                    raise CommandError("MapCache SQLite exists.")

            logger.info("Creating new MapCache SQLite file.")
            conn = dbapi2.connect(
                db_path,
                detect_types=dbapi2.PARSE_DECLTYPES | dbapi2.PARSE_COLNAMES,
            )
            conn.execute(create_sql)

            self.handle_collection(conn, collection, unique_times)

            if index:
                conn.execute(
                    'CREATE INDEX time_idx ON time '
                    '(start_time, end_time, minx, miny, maxx, maxy)'
                )

            conn.commit()
            conn.close()

        logger.info(
            "Finished generation of MapCache SQLite DB holding times "
            "and extents."
        )

    def handle_collection(self, conn, collection, unique_times):
        try:
            logger.info("Syncing layer '%s'" % collection.identifier)

            logger.debug("Starting query for browses")

            products_qs = models.Product.objects.filter(
                collections=collection,
            ).annotate(
                extent=Extent('footprint')
            ).values(
                'begin_time', 'end_time', 'extent'
            ).order_by(
                'begin_time', 'end_time'
            )

            logger.info("Number products: %s" % products_qs.count())

            if not unique_times:
                time_intervals = (
                    (
                        product['begin_time'],
                        product['end_time']
                    ) + product['extent']
                    for product in products_qs
                )
            else:
                logger.debug("Starting query for unique times")
                # optimization for when there are a lot of equal time entries
                # like for Sentinel-2
                unique_times_qs = models.Product.objects.filter(
                    collections=collection,
                ).values_list(
                    'begin_time', 'end_time'
                ).distinct(
                    'begin_time', 'end_time'
                ).order_by(
                    'begin_time', 'end_time'
                )
                logger.info(
                    "Number unique times: %s" % unique_times_qs.count()
                )

                logger.info("Iterating through unique times")
                time_intervals = []
                i = 1
                for begin_time, end_time in unique_times_qs:
                    logger.debug(
                        "Working on unique time %s: %s/%s " %
                        (i, begin_time, end_time)
                    )
                    i += 1

                    minx, miny, maxx, maxy = (None,) * 4

                    # search for all browses within that time interval and
                    # combine extent
                    time_qs = products_qs.filter(
                        begin_time=begin_time,
                        end_time=end_time
                    )

                    if time_qs.count() <= 0:
                        logger.errro(
                            "DB queries got different results which should "
                            "never happen."
                        )
                        raise CommandError("DB queries got different results.")
                    else:
                        for time in time_qs:
                            # decode extent from the above hack
                            minx_tmp, miny_tmp, maxx_tmp, maxy_tmp = \
                                time['extent']
                            # change one extent to ]0,360] if difference gets
                            # smaller
                            if minx is not None and maxx is not None:
                                if (minx_tmp <= 0 and maxx_tmp <= 0 and
                                        (minx-maxx_tmp) > (360+minx_tmp-maxx)):
                                    minx_tmp += 360
                                    maxx_tmp += 360
                                elif (minx <= 0 and maxx <= 0 and
                                        (minx_tmp-maxx) > (360+minx-maxx_tmp)):
                                    minx += 360
                                    maxx += 360
                            minx = min(
                                i for i in [minx_tmp, minx] if i is not None
                            )
                            miny = min(
                                i for i in [miny_tmp, miny] if i is not None
                            )
                            maxx = max(
                                i for i in [maxx_tmp, maxx] if i is not None
                            )
                            maxy = max(
                                i for i in [maxy_tmp, maxy] if i is not None
                            )

                    # check if previous element in ordered list overlaps
                    if (
                        len(time_intervals) > 0 and (
                            (
                                (
                                    begin_time == end_time or
                                    time_intervals[-1][0] ==
                                    time_intervals[-1][1]
                                ) and (
                                    time_intervals[-1][0] <= end_time and
                                    time_intervals[-1][1] >= begin_time
                                )
                            ) or (
                                time_intervals[-1][0] < end_time and
                                time_intervals[-1][1] > begin_time
                            )
                        )
                    ):
                        begin_time = min(begin_time, time_intervals[-1][0])
                        end_time = max(end_time, time_intervals[-1][1])
                        minx = min(minx, time_intervals[-1][2])
                        miny = min(miny, time_intervals[-1][3])
                        maxx = max(maxx, time_intervals[-1][4])
                        maxy = max(maxy, time_intervals[-1][5])
                        time_intervals.pop(-1)
                    time_intervals.append(
                        (begin_time, end_time, minx, miny, maxx, maxy)
                    )

                logger.info(
                    "Number non-overlapping time intervals: %s" %
                    len(time_intervals)
                )

            logger.info(
                "Starting saving time intervals to MapCache SQLite file"
            )

            conn.executemany(
                'INSERT INTO time VALUES (?, ?, ?, ?, ?, ?)',
                time_intervals
            )

            logger.info(
                "Finished saving time intervals to MapCache SQLite file"
            )

        except Exception as e:
            logger.error(
                "Failure during generation of MapCache SQLite DB."
            )
            logger.error(
                "Exception was '%s': %s" % (type(e).__name__, str(e))
            )
            logger.debug(traceback.format_exc() + "\n")
