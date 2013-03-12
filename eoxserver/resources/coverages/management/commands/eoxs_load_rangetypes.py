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

# try the python default json module 
try : import json 
except ImportError: 
    #try the original simplejson module
    try: import simplejson as json
    except ImportError: 
        #try the simplejson module packed in django
        try: import django.utils.simplejson as json 
        except ImportError: 
            raise ImportError( "Failed to import any usable json module!" ) 
    
#------------------------------------------------------------------------------

from eoxserver.core.system import System

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.rangetype import isRangeTypeName
from eoxserver.resources.coverages.rangetype import setRangeType

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

#------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-i','--input',
            dest='filename',
            action='store', type='string',
            default='-',
            help=("Optional. Read input from a file rather than from the "
                  "default standard input." )
        ),
        
    )

    help = ( """ Load rangetypes stored in JSON format from standard input.""" )

    #--------------------------------------------------------------------------

    def _error( self , rt_name , msg ): 
        self.print_err( "Failed to register rangetype '%s'!"
                        " Reason: %s"%( rt_name, msg ) ) 

    #--------------------------------------------------------------------------

    def handle(self, *args, **options):

        # Collect parameters
        self.traceback = bool(options.get("traceback", False) ) 
        self.verbosity = int(options.get('verbosity', 1))
        filename       = options.get('filename','-')

        # dataset's (coverages') ids
        rt_list = args

        #----------------------------------------------------------------------
        # load and parse the input data  

        try :  
            
            if filename == "-" : 

                # standard input 
                rts = json.load( sys.stdin ) 

            else : 

                # file input 
                with open(filename,"r") as fin : 
                    rts = json.load( fin ) 

        except IOError as e : 

            # print stack trace if required 
            if self.traceback : 
                self.print_msg(traceback.format_exc())

            raise CommandError( "Failed to open the input file '%s' ! "
                                    "REASON: %s " % ( filename , str(e) ) ) 
            
        #----------------------------------------------------------------------
        # initialize EOxServer binding

        System.init()

        #----------------------------------------------------------------------
        # insert the range types to DB 

        success_count = 0 # success counter - counts finished syncs

        for i,rt in enumerate(rts) : 

            # extract RT name 

            rt_name = rt.get('name',None) 

            if not ( isinstance(rt_name, basestring) and rt_name ) : 

                self.print_err( "Range type #%d rejected as it has no valid"
                                " name."%(i+1) ) 
                continue 
            
            if isRangeTypeName( rt_name ): 

                self.print_err( "The name '%s' is already used by another "
                "range type! Import of range type #%d aborted!" \
                        %( rt_name , (i+1) ) )

                continue 

            #------------------------------------------------------------------

            try : 

                # create rangetype record 
                setRangeType( rt ) 
        
                success_count += 1 # increment success counter 

            except Exception as e: 

                # print stack trace if required 
                if self.traceback : 
                    self.print_msg(traceback.format_exc())

                self._error( rt['name'], "%s: %s"%(type(e).__name__, str(e)) )

                continue # continue by next dataset 


            self.print_msg( "Range type '%s' loaded."%rt['name']) 

        #----------------------------------------------------------------------
        # print the final info 
        
        count = len(rts) 
        error_count = count - success_count

        if ( error_count > 0 ) : 
            self.print_msg( "Failed to load %d range types." % (
                error_count ) , 1 )  

        if ( success_count > 0 ) : 
            self.print_msg( "Successfully loaded %d of %s range types." % (
                success_count , count ) , 1 )
        else : 
            self.print_msg( "No range type loaded." ) 

#------------------------------------------------------------------------------
