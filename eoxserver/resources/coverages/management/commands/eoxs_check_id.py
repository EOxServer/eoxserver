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

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

#------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):

    args = '[-a|-r|-u] <ID>'

    option_list = BaseCommand.option_list + (
        make_option('-a','--is-available',
            dest='query_type',
            action='store_const', const="isAvailable", default="isAvailable",
            help=("Default. Query whether the given ID can be used for a new "
                  "entity (i.e., coverage, dataset, mosaic, or series).") 
        ), 
        make_option('-r','--is-reserved',
            dest='query_type',
            action='store_const', const="isReserved",
            help=("Query whether the given ID is reserved for creation of "
                  "a new entity (i.e., coverage, dataset, mosaic, or series). "
                  "When ID is reserved it may or may not be already used but "
                  " for sure it is not available.")
        ), 
        make_option('-u','--is-used',
            dest='query_type',
            action='store_const', const="isUsed",
            help=("Query whether the given ID is an existing entity such as "
                  " coverage, dataset, mosaic, or series.") 
        ), 
    )

    help = (
    """
    Query status of an ID (Coverage or EO ID). The options control the type 
    of query to be performed. The boolean answer is returned via the command 
    return-code. 
    """
    )

    #--------------------------------------------------------------------------

    def handle(self, *args, **opt):

        System.init()

        # prepare ID manager 
        id_manager = CoverageIdManager() 

        # get query type
        qtype = opt.get("query_type", "isAvailable" )

        #get queried ID 
        try: 
            id = args[0]
        except IndexError : 
            raise CommandError("Missing the mandatory quertied ID!")

        # select query based on the query type  
        if qtype == "isAvailable" : 
            result = id_manager.isAvailable( id )
        
        elif qtype == "isUsed" :
            result = id_manager.isUsed( id )
    
        elif qtype == "isReserved" :
            result = id_manager.isReserved( id )

        else : 
            raise CommandError("Invalid query type!") 


        # exit with propper exit code 
        sys.exit( int( not bool(result) ) ) 
