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

import traceback

from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from eoxserver.core.system import System
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import CoverageIdManager
from eoxserver.resources.coverages.managers import getRectifiedStitchedMosaicManager
from eoxserver.resources.coverages.managers import getDatasetSeriesManager

#------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-a','--all',
            action='store_true',
            dest='synchronise_all',
            default=False,
            help=('Optional switch to enable the synchronization for all ' 
                  'registered containers.')
        ),
    )

    args = '--all | <id> [<id> ...]'
    
    help = (
    """
    Synchronizes all specified containers (RectifiedStitchedMosaic or 
    DatasetSeries) with the file system.

    Examples:
        python manage.py %(name)s --all
        
        python manage.py %(name)s MER_FRS_1P_RGB_reduced \\
            MER_FRS_1P_reduced
    """ % ({"name": __name__.split(".")[-1]})
    )

    #--------------------------------------------------------------------------

    def _error( self , entity , ds , msg ): 
        self.print_err( "Failed to synchronise %s '%s'!"
                        " Reason: %s"%( entity , ds, msg ) ) 

    #--------------------------------------------------------------------------
    
    def handle(self, *args, **options):

        # set up

        System.init()
        
        self.verbosity = int(options.get('verbosity', 1))
        

        #----------------------------------------------------------------------
        # prepare managers
        
        dsMngr = { 
            "RectifiedStitchedMosaic" : getRectifiedStitchedMosaicManager(),
            "DatasetSeries" : getDatasetSeriesManager() } 
        
        cidMngr = CoverageIdManager()

        #----------------------------------------------------------------------
        # parse arguments

        ids = []

        if options.get("synchronise_all", False):

            # synchronise all container entities 
            for mngr in dsMngr.values() : 
                ids.extend( mngr.get_all_ids() ) 
        
        else:

            # read ids from the commandline  
            ids.extend( args ) 


        #----------------------------------------------------------------------
        # synchronise objects 

        success_count = 0 # success counter - counts finished syncs

        for id in ids : 

            # get type of the entity 

            dsType = cidMngr.getType( id )

            # check the entity type  

            if not dsMngr.has_key( dsType ) : 
                self.print_msg( "'%s' is neither mosaic nor series!"%id,2) 
                self._error( id , "Invalid identifier." ) 
                continue # continue by next entity 

            self.print_msg( "Synchronising %s: '%s'" % ( dsType, id )  ) 

            try:

                with transaction.commit_on_success():
                    dsMngr[dsType].synchronize(id)

            except Exception as e :

                # print stack trace if required 
                if options.get("traceback", False):
                    self.print_msg(traceback.format_exc())

                self._error( dsType, id, "%s: %s"%(type(e).__name__, str(e)) )
        
                continue # continue by next dataset
            
            success_count += 1 #increment the success counter  
            self.print_msg( "%s successfully synchronised."%dsType,2) 

        #----------------------------------------------------------------------
        # print the final info 
        
        count = len(ids) 
        error_count = count - success_count

        if ( error_count > 0 ) : 
            self.print_msg( "Failed to synchronise %d objects." % (
                error_count ) , 1 )  

        if ( success_count > 0 ) : 
            self.print_msg( "Successfully synchronised %d of %s objects." % (
                success_count , count ) , 1 )
        else : 
            self.print_msg( "No object synchronised." ) 

        if ( error_count > 0 ) : 
            raise CommandError("Not all objects could be synchronised.")
