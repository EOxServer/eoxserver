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

#------------------------------------------------------------------------------

from eoxserver.core.system import System

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.rangetype import getAllRangeTypeNames
from eoxserver.resources.coverages.rangetype import isRangeTypeName
from eoxserver.resources.coverages.rangetype import getRangeTypeObject

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
    )

    args = "[<rt-id> [<rt-id> ...]]"

    help = (
    """
    Print either list of all rangetype indentifiers and their details.
    When the range-type identifiers are specified than only these rangetypes
    are selected.
    """ % ({"name": __name__.split(".")[-1]})
    )

    #--------------------------------------------------------------------------

    def handle(self, *args, **options):

        # Collect parameters

        self.verbosity = int(options.get('verbosity', 1))

        print_details = bool(options.get('details',False))

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


        if not print_details :

            # print plain list

            for rt in rt_list :
                print rt

        else :

            # print details

            for rt_name in rt_list :

                rt_obj = getRangeTypeObject( rt_name )

                print
                print "Range-Type:" , rt_obj.name
                print "\tType:\t\t%s" % rt_obj.getDataTypeAsString()
                print "\tNr. of Bands:\t%d" % len(rt_obj.bands)
                print "\tBands:"

                for band in rt_obj.bands :

                    print "\t\t%s"%(band.identifier)

            if 0 < len( rt_list ) : print

