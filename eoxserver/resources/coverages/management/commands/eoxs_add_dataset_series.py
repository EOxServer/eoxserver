#-------------------------------------------------------------------------------
# $Id$
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

import datetime
from urlparse import urlparse
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.contrib.gis.geos.geometry import GEOSGeometry

from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, StringFormatCallback
)
from eoxserver.resources.coverages.metadata import EOMetadata

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import getDatasetSeriesManager

#-------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-i', '--eo-id', '--id',
            dest='eoid', metavar="EOID",
            default=None,
            help=('Mandatory. The EOID of the Dataset Series to be created.')
        ),
        make_option('-d','--data-source', '--data-sources',
            dest='data_sources',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=("Optional. A list of directories to be added as data sources "
                  "To this Dataset Series. If supplied, this will trigger "
                  "a synchronization. For FTP data sources this has to be a "
                  "URL in this format: ftp://user:password@host:port/path")
        ),
        make_option('-p', '--pattern', '--patterns',
            dest='patterns',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=("Optional but highly recommended. A list of search "
                  "patterns (regular expressions) to use to identify data "
                  "files. When only one is given, it is used for all data "
                  "sources.")
        ),
        make_option('-a','--add',
            dest='add',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=("Optional. A list of Coverage IDs identifying Referenceable "
                  "Datasets, Rectified Datasets or Stitched Mosaics. All "
                  "referenced datasets will be added to the Dataset Series.")
        ),
        make_option('--no-sync',
            dest="no_sync",
            action='store_true', default=False,
            help=("Optional. This switch explicitly turns off the "
                  "synchronization when data sources were added.")
        ),
        make_option('--begin-time','--default-begin-time',
            dest='default_begin_time',
            action="callback", callback=StringFormatCallback(getDateTime),
            default=None,
            help=("Optional. Default begin timestamp when no other EO-metadata " 
                  "is available. The format is ISO-8601.")
        ),
        make_option('--end-time','--default-end-time',
            dest='default_end_time',
            action="callback", callback=StringFormatCallback(getDateTime),
            default=None,
            help=("Optional. Default end timestamp when no other EO-metadata " 
                  "is available. The format is ISO-8601.")
        ),
        make_option('--footprint','--default-footprint',
            dest='default_footprint',
            action="callback", callback=StringFormatCallback(str),
            default=None,
            help=("Optional. The default footprint in WKT format when no other " 
                  "EO-metadata is available.")
        ),
    )
    
    help = (
    """
    Creates a new Dataset Series with initial data.
    
    Examples:
    With initial datasets:
        python manage.py %(name)s \\
            --id MER_FRS_1P_RGB_reduced --add MER_FRS_1PNPDE..._reduced
    
    With a local and a remote data source:
        python manage.py %(name)s \\
            --id MER_FRS_1P_RGB_reduced \\
            --data-sources data/meris/mosaic_MER_FRS_1P_RGB_reduced/ \\
            ftp://ftp_user:secret@some.host.com/data/meris/ \\
            --patterns "*.tif" "*.tif"
    
    With default metadata values:
        python manage.py %(name)s \\
            --id MER_FRS_1P_RGB_reduced \\
            --default-begin-time "`date -u --iso-8601=seconds`" \\
            --default-end-time "`date -u --iso-8601=seconds`" \\
            --default-footprint "POLYGON ((11.3610659999999992 
                32.2014459999999971, 11.3610659999999992 
                46.2520260000000007, 28.2838460000000005 
                46.2520260000000007, 28.2838460000000005  
                32.2014459999999971, 11.3610659999999992 
                32.2014459999999971))"
    """ % ({"name": __name__.split(".")[-1]}))
    args = '--eo-id EOID'

    def handle(self, *args, **options):
        System.init()
        
        #=======================================================================
        # Collect parameters
        #=======================================================================
        
        self.verbosity = int(options.get('verbosity', 1))
        
        eoid = options.get("eoid")
        if eoid is None:
            raise CommandError("Mandatory parameter `--eo-id` not supplied.")
        
        data_sources = options.get("data_sources", [])
        patterns = options.get("patterns", [])
        coverages = options.get("add", [])
        no_sync = options.get("no_sync", False)
        
        do_sync = len(data_sources) > 0 and not no_sync
        
        default_begin_time = options.get("default_begin_time")
        default_end_time = options.get("default_end_time")
        default_footprint = options.get("default_footprint")
        
        if default_footprint is not None:
            footprint = GEOSGeometry(default_footprint)
        else:
            footprint = MultiPolygon(Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))))
            self.print_msg("Using default footprint: %s" % footprint.wkt, 2)
        
        #=======================================================================
        # Create Dataset Series
        #=======================================================================
        
        dss_mgr = getDatasetSeriesManager() 
        
        self.print_msg("Creating Dataset Series with ID '%s'." % eoid, 1)
        
        with transaction.commit_on_success():
            dss_mgr.create(
                eo_metadata=EOMetadata(
                    eoid,
                    default_begin_time or datetime.datetime.now(),
                    default_end_time or datetime.datetime.now(),
                    footprint
                )
            )
            
            #===================================================================
            # Prepare data sources
            #===================================================================
            
            if len(data_sources) > 0:
                if len(patterns) == 1:
                    patterns *= len(data_sources)
                elif len(patterns) == 0:
                    self.print_msg( "No pattern is given. "
                                    "Using the default one.",2)
                    patterns = [None] * len(data_sources)
                elif len(patterns) != len(data_sources):
                    raise CommandError(
                        "Number of patterns given (%d) does not match number "
                        "of data sources (%d)." % (len(patterns), len(data_sources)) 
                    )
            
            data_dirs = []
            for location, pattern in zip(data_sources, patterns):
                opts = urlparse(location)
                if opts.scheme.lower() == "ftp":
                    args = {
                        "type": "ftp",
                        "host": opts.hostname,
                        "port": opts.port,
                        "user": opts.username,
                        "passwd": opts.password,
                        "path": opts.path,
                    }
                    
                    self.print_msg(
                        ("Adding FTP data source (host=%(host)s, "
                         "port=%(port)s, path=%(path)s, user=%(user)s, "
                         "password=%(passwd)s) to Dataset Series.") % args,
                        2
                    )
                else:
                    args = {
                        "type": "local",
                        "path": location
                    }
                    self.print_msg(
                        "Adding local data source (path=%s) to Dataset Series" % location, 
                        2
                    )
                
                if pattern is not None:
                    args["search_pattern"] = pattern
                data_dirs.append(args)
    
            #===================================================================
            # Update the Dataset Series with data sources and coverages
            #===================================================================
            
            args = {}
            if len(coverages) > 0:
                self.print_msg(
                    "Adding coverages (%s) to Dataset Series." % " , ".join(coverages),
                    2
                )
                args["coverage_ids"] = coverages
            if len(data_dirs) > 0:
                args["data_dirs"] = data_dirs
            
            if len(args) > 0:
                dss_mgr.update(
                    obj_id=eoid,
                    link=args
                )
            
            #===================================================================
            # Sync, if necessary/desired
            #===================================================================
            
            if do_sync:
                self.print_msg("Synchronizing Dataset Series.", 2)
                dss_mgr.synchronize(obj_id=eoid)
        
