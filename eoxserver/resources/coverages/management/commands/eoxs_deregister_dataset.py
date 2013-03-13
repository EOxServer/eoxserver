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
from django.db import transaction

#------------------------------------------------------------------------------

from eoxserver.core.system import System

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import CoverageIdManager
from eoxserver.resources.coverages.managers import getRectifiedDatasetManager
from eoxserver.resources.coverages.managers import getReferenceableDatasetManager

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

#------------------------------------------------------------------------------


class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--force',
            dest='force_dereg_autods',
            action='store_true',
            default=False,
            help=("Optional. Force deregistration of automatic datasets. "
                  "This option should be avoided or used with extreme "
                  "caution. (forced deregistration is disabled by default)")
        ), 
    )

    args = "<id> [<id> ...]"

    help = (
    """
    Deregister one or more datasets corresponding to the given ids.
    unless overridden by the '--force' option the removal of automatic datasets
    will be prevented.
    
    """ % ({"name": __name__.split(".")[-1]})
    )

    #--------------------------------------------------------------------------

    def _error( self , ds , msg ): 
        self.print_err( "Failed to deregister dataset '%s'!"
                        " Reason: %s"%( ds, msg ) )

    #--------------------------------------------------------------------------

    def handle(self, *args, **options):

        # Collect parameters
        
        self.verbosity = int(options.get('verbosity', 1))

        force_dereg_autods = bool(options.get('force_dereg_autods',False))

        # dataset's (coverages') ids 
        datasets = args 

        #----------------------------------------------------------------------
        # initialize EOxServer binding 

        System.init()

        #----------------------------------------------------------------------
        # prepare managers 
    
        dsMngr = { 
            "RectifiedDataset" : getRectifiedDatasetManager() ,
            "ReferenceableDataset" : getReferenceableDatasetManager() } 

        cidMngr = CoverageIdManager()

        #----------------------------------------------------------------------
        # remove datasets one by one 

        success_count = 0 # count successfull actions 

        for dataset in datasets : 

            self.print_msg( "Deregistering dataset: '%s'"%dataset ) 

            # check the dataset type                                                   
            dsType = cidMngr.getType( dataset )

            self.print_msg( "Dataset type: %s"%str(dsType) , 2 ) 

            # check the dataset type  

            if not dsMngr.has_key( dsType ) : 
                self.print_msg( "'%s' is neither rectified nor referenceable "
                    "dataset."%dataset,2) 
                self._error( dataset , "Invalid dataset identifier." ) 
                continue # continue by next dataset 

            # check whether the dataset is automatic or manual 

            if dsMngr[dsType].is_automatic( dataset ) : 

                self.print_msg( "'%s' is labeled as AUTOMATIC!"%dataset,2) 

                if not force_dereg_autods: 

                    self._error( dataset, "Dataset is labeled as automatic. "
                    "Deregistration of the automatic dataset is not allowed!" )
                    continue # continue by next dataset 

                self.print_msg( "Removal of AUTOMATIC datasets is allowed!",2) 

            # removing the dataset 

            try:

                with transaction.commit_on_success():
                    self.print_msg( "Removing dataset from the DB ...",2) 
                    dsMngr[dsType].delete( dataset ) 

            except Exception as e: 

                self.print_msg( "Dataset removal failed with an exception.",2) 

                # print stack trace if required 
                if options.get("traceback", False):
                    self.print_msg(traceback.format_exc())

                self._error( dataset, "%s: %s"%(type(e).__name__, str(e)) )

                continue # continue by next dataset 

            success_count += 1 #increment the success counter  
            self.print_msg( "Dataset successfully removed.",2) 

        #----------------------------------------------------------------------
        # print the final statistics  

        count = len(datasets) 
        error_count = count - success_count

        if ( error_count > 0 ) : 
            self.print_msg( "Failed to deregistered %d dataset%s." % (
                error_count , ("","s")[error_count!=1] ) , 1 )  

        if ( success_count > 0 ) : 
            self.print_msg( "Successfully deregistered %d of %s dataset%s." % (
                success_count , count , ("","s")[count!=1] ) , 1 )
        else : 
            self.print_msg( "No dataset deregistered." ) 

        if ( error_count > 0 ) : 
            raise CommandError("Not all datasets could be deregistered.")
