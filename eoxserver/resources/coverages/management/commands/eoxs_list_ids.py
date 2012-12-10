#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
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

import sys
import traceback
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from eoxserver.core.system import System
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.resources.coverages.management.commands import _variable_args_cb

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import CoverageIdManager
from eoxserver.resources.coverages.managers import getRectifiedDatasetManager
from eoxserver.resources.coverages.managers import getReferenceableDatasetManager
from eoxserver.resources.coverages.managers import getRectifiedStitchedMosaicManager
from eoxserver.resources.coverages.managers import getDatasetSeriesManager

#------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("-f","--filter","--type-filter", dest="filter_enabled", 
            action='store_true', default=False,
            help=("Optional. List of types to restrict the listed IDs.")
        ),
    ) 

    args = "-f <type> [<type> ...]|<id> [<id> ...]"

    help = (
    """
    Print either list of all or selected dataset (Coverage/EO) indentifiers 
    and their types. The selection passed as command-line arguments. 

    In case of listing of all registered IDs, the output can be filtered 
    by a given selection of types. 

    The commands prints list of <id> <type> pairs. The type can be either 
    "RectifiedDataset", "ReferenceableDataset", "RectifiedStitchedMosaic",
    "DatasetSeries", "Reserved" (reserved ID), "None" (non-existing id).

    """ % ({"name": __name__.split(".")[-1]})
    )

    #--------------------------------------------------------------------------

    def handle(self, *args, **options):

        # Collect parameters

        self.verbosity = int(options.get('verbosity', 1))


        # get filter 
        if options.get("filter_enabled",False) : 

            # arguments interpreted as filters 
            ids = [] # dataset's (coverages') ids
            type_filter = args # get filter 

        else : 

            # argument interpreted as ids 
            ids = args # dataset's (coverages') ids
            type_filter = [] # get filter 


        #----------------------------------------------------------------------

        # initialize EOxServer binding

        System.init()

        # prepare managers 

        id_manager = CoverageIdManager() 

        ds_managers = { 
            "RectifiedDataset" : getRectifiedDatasetManager() ,
            "ReferenceableDataset" : getReferenceableDatasetManager() , 
            "RectifiedStitchedMosaic" : getRectifiedStitchedMosaicManager() , 
            "DatasetSeries" : getDatasetSeriesManager() , 
        } 

        #----------------------------------------------------------------------
        # check the input rangetype names

        if not ids :

            # if no IDs specified get all identifiers
            for ds_type in ds_managers : 
                if not type_filter or ds_type in type_filter : 
                    for id in ds_managers[ds_type].get_all_ids() : 
                        print id , ds_type 

            # in addition print all reserved IDs 
            if not type_filter or "Reserved" in type_filter : 
                for id in id_manager.getAllReservedIds() : 
                    print id , "Reserved" 

        else :

            # get info for the specified identifiers 
            for id in ids : 
                print id , id_manager.getType(id) 
