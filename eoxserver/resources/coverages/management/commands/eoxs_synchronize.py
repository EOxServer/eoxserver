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

from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from eoxserver.core.system import System
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='all',
            help=('Optional switch to enable the synchronization for all ' 
                  'registered containers.')
        ),
        #make_option('-i', '--id', '--ids', '--eoid', '--eoids',
        #    dest='ids',
        #    action='callback', callback=_variable_args_cb,
        #    default=None,
        #    help=('Mandatory. One or more paths to a files '
        #          'containing the image data. These paths can '
        #          'either be local, ftp paths, or rasdaman '
        #          'collection names.')
        #),
    )
    
    help = ('Synchronizes all specified containers (RectifiedStitchedMosaic or'
            'DatasetSeries) with the file system.')
    args = '--all | EO-ID1 [EO-ID2 [...]]'
    
    def handle(self, *args, **options):
        #=======================================================================
        # set up
        #=======================================================================
        System.init()
        
        self.verbosity = int(options.get('verbosity', 1))
        
        coverage_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        datasetseries_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
        
        mosaic_ids = []
        series_ids = []
        
        #=======================================================================
        # parse arguments
        #=======================================================================
        
        if options.get("all", False):
            mosaic_ids = [
                mosaic.getEOID() 
                for mosaic in coverage_factory.find(
                    impl_ids=["resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"]
                )
            ]
            
            series_ids = [
                datasetseries.getEOID() 
                for datasetseries in datasetseries_factory.find()
            ]
        
        
        elif len(args) == 0:
            raise CommandError("No container object specified.")
        
        else:
            for eoid in args:
                wrapper = datasetseries_factory.get(obj_id=eoid)
                if wrapper is not None:
                    series_ids.append(wrapper.getEOID())
                    continue
                
                wrapper = coverage_factory.get(
                    impl_id="resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
                    obj_id=eoid
                )
                if wrapper is not None:
                    mosaic_ids.append(wrapper.getEOID())
                
                else:
                    raise CommandError("ID '%s' does neither refer to a "
                                       "RectifiedStitchedMosaic nor to a "
                                       "DatasetSeries." % eoid)
        
        #=======================================================================
        # Create managers
        #=======================================================================
        
        mosaic_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_stitched_mosaic"
            }
        )
        
        series_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.dataset_series"
            }
        )
        
        #=======================================================================
        # Dispatch synchronization
        #=======================================================================
        
        if series_ids:
            self.print_msg(
                "Synchronizing DatasetSeries with IDs: %s"%", ".join(series_ids), 2
            )
        if series_ids:
            self.print_msg(
                "Synchronizing RectifiedStitchedMosaics with IDs: %s"%", ".join(mosaic_ids), 2
            )
        
        for eoid in mosaic_ids:
            try:
                with transaction.commit_on_success():
                    mosaic_mgr.synchronize(eoid)
            except:
                self.print_msg(
                    "Synchronization of Recitified Stitched Mosaic '%s' failed." % eoid
                )
        
        for eoid in series_ids:
            try:
                with transaction.commit_on_success():
                    series_mgr.synchronize(eoid)
            except:
                self.print_msg(
                    "Synchronization of Dataset Series '%s' failed." % eoid
                )
