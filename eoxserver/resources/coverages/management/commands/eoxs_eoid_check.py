#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError, BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry

from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb
)

from eoxserver.resources.coverages.models import ( EOObject,
    Coverage, Collection, RectifiedDataset, ReferenceableDataset,
    RectifiedStitchedMosaic, DatasetSeries,
    EO_OBJECT_TYPE_REGISTRY ) 

# label to type dictionary 

LABEL2TYPE= {
    "EOObject":EOObject,
    "Coverage":Coverage,
    "Collection":Collection,
    "RectifiedDataset":RectifiedDataset,
    "ReferenceableDataset":ReferenceableDataset,
    "RectifiedStitchedMosaic":RectifiedStitchedMosaic,
    "DatasetSeries":DatasetSeries,
} 

class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier", dest="identifier",
            action="store", default=None,
            help=("Queried identifier.")
        ),
        make_option("-f","--filter","--type-filter", dest="eotype", 
            action="store", default="EOObject",
            help=("Optional. Restrict the listed identifiers to given type.")
        ),
    )

    args = "[-f <type>] -i <id>"

    help = (
    """
    Check whether an identifier is used by the existing 
    EOObjects or its subtypes. The existence is indicated 
    by the returned exit-code. 
    
    The allowed types are: %s
    """ % ("|".join(LABEL2TYPE))
    )

    def handle(self, *args, **opt):

        #----------------------------------------------------------------------
        # check the inputs 

        # check required identifier 
        identifier = opt.get('identifier',None)
        if identifier is None : 
            raise CommandError("Missing the mandatory dataset identifier!")

        eotype = LABEL2TYPE.get(opt.get('eotype',"EOObject"),None)

        if eotype is None : 
            raise CommandError("Invalid type: '%s'"%(opt.get('eotype')) )

        #----------------------------------------------------------------------
        # perform the action 
   
        try :  

            eoobj = eotype.objects.get(identifier=identifier)
            eoobj_type = EO_OBJECT_TYPE_REGISTRY[eoobj.real_content_type]

            # format a user-friendly type name 
            if ( eoobj_type == eotype ) :
                type_name = eotype.__name__
            else : 
                type_name = "%s(%s)"%(eoobj_type.__name__,eotype.__name__) 

            self.print_msg( "There is a %s matching the identifier: '%s'" % ( 
                type_name, identifier ) )  

        except eotype.DoesNotExist : 
            self.print_msg( "There is no %s matching the identifier: '%s'" % ( 
                eotype.__name__, identifier ) )  
            
            #TODO: Find a better way how to pass the return code.
            sys.exit(1) 

        #----------------------------------------------------------------------


