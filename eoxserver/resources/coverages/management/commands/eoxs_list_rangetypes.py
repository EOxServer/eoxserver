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

from eoxserver.resources.coverages.rangetype import getAllRangeTypeNames
from eoxserver.resources.coverages.rangetype import isRangeTypeName
from eoxserver.resources.coverages.rangetype import getRangeType

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

#------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--details',
            dest='details',
            action='store_true',
            default=False,
            help=("Optional. Print details of the reangetypes." )
        ),
        make_option('--json',
            dest='json_dump',
            action='store_true',
            default=False,
            help=("Optional. Dump rangetype(s) in JSON format. This JSON "
                  "dump can be loaded by another instance of EOxServer." )
        ),
        make_option('-o','--output',
            dest='filename',
            action='store', type='string',
            default='-',
            help=("Optional. Write output to a file rather than to the default"
                  " standard output." )
        ),
        
    )

    args = "[<rt-id> [<rt-id> ...]]"

    help = (
    """
    Print either list of all rangetype indentifiers and their details.
    When the range-type identifiers are specified than only these rangetypes
    are selected. In addition complete rangetypes cans be dumped in JSON 
    format which can be then loaded by another EOxServer instance. 
    """ % ({"name": __name__.split(".")[-1]})
    )

    #--------------------------------------------------------------------------

    def handle(self, *args, **options):

        # Collect parameters

        self.verbosity  = int(options.get('verbosity', 1))

        print_details   = bool(options.get('details',False))

        print_json      = bool(options.get('json_dump',False))

        filename        = options.get('filename','-')

        # dataset's (coverages') ids
        rt_list = args

            
        #----------------------------------------------------------------------
        # initialize EOxServer binding

        System.init()

        #----------------------------------------------------------------------
        # check the input rangetype names

        if not rt_list :

            # if no IDs specified get all identifiers

            rt_list = getAllRangeTypeNames()

        else :

            # filter existing range-type names

            def __checkRangeType( rt ) :
                rv = isRangeTypeName( rt )
                if not rv :
                    self.print_err( "Invalid range-type identifier '%s' !"%rt )
                return rv

            rt_list = filter( __checkRangeType , rt_list )

        #----------------------------------------------------------------------
        # output

        # select the right output driver 

        if print_json :         output = OutputJSON
        elif print_details :    output = OutputDetailed 
        else :                  output = OutputBrief 


        # write the output 

        def _write_out( fout ) : 
            fout.write( output.lead() ) 
            for i,rt_name in enumerate(rt_list) :
                if i > 0 : fout.write( output.separator() )
                fout.write( output.object( rt_name ) ) 
            fout.write( output.trail() ) 

        # output file 
        try :  

            if filename == "-" : 

                # write to stdout 
                _write_out( sys.stdout ) 

            else : 
                
                # write to a file 
                with open(filename,"w") as fout :
                    _write_out( fout )

        except IOError as e : 

            raise CommandError( "Failed to open the output file '%s' ! "
                    "REASON: %s" % ( filename , str(e) ) )
                            

#------------------------------------------------------------------------------
# output drivers 

class OutputBase: 
    """ base output driver class class """ 

    @classmethod 
    def lead(cls): return ""

    @classmethod 
    def object( cls, rt_name ) : return ""

    @classmethod 
    def trail(cls): return ""

    @classmethod
    def separator(cls) : return ""


class OutputBrief( OutputBase ):
    """ brief text output - RT name only """ 

    @classmethod 
    def object( cls, rt_name ) : return rt_name 

    @classmethod
    def separator(cls) : return "\n" 

    @classmethod 
    def trail(cls): return "\n"
        

class OutputDetailed( OutputBase ): 
    """ detailed text output """ 

    @classmethod
    def lead(cls) : return "\n" 

    @classmethod
    def trail(cls) : return "\n\n" 

    @classmethod
    def separator(cls) : return "\n\n" 

    @classmethod 
    def object( cls, rt_name ) : 

        rt = getRangeType( rt_name )

        out = []

        out.append("Range-Type: %s" % rt.name ) 
        out.append("\tType:\t\t%s" % rt.getDataTypeAsString())
        out.append("\tNr. of Bands:\t%d" % len(rt.bands))
        out.append("\tBands:")

        for band in rt.bands :
            out.append( "\t\t%s"%(band.identifier) ) 

        return "\n".join( out ) 


class OutputJSON( OutputBase ) : 
    """ JSON output """ 

    @classmethod 
    def lead(cls): 
        return "["

    @classmethod 
    def trail(cls):
        return "]\n"

    @classmethod
    def separator(cls) : return ",\n" 

    @classmethod 
    def object( cls, rt_name ) : 

        # get rangetype as dictionary  
        out = getRangeType(rt_name).asDict() 

        # dump the json 
        return json.dumps(out,indent=4,separators=(',',': '),sort_keys=True) 


