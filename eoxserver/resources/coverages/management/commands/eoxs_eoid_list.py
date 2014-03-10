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
        make_option("-i", "--identifier", dest="identifiers", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Optional list of identifiers.")
        ),
        make_option("-f","--filter","--type-filter", dest="eotype", 
            action="store", default="EOObject",
            help=("Optional. Restrict the listed identifiers to given type.")
        ),
    )

    args = "[-f <type>] [-i <id> [<id> ...]]"

    help = (
    """
    Print either list of all or selected EOObject identifiers
    and their types. 

    The commands prints list of <id> <type> pairs. 
    
    The allowed types are: %s
    """ % ("|".join(LABEL2TYPE))
    )

    def handle(self, *args, **opt):

        #----------------------------------------------------------------------
        # check the inputs 

        # check required identifier 
        identifiers = opt.get('identifiers',None)

        eotype = LABEL2TYPE.get(opt.get('eotype',"EOObject"),None)

        if eotype is None : 
            raise CommandError("Invalid type: '%s'"%(opt.get('eotype')) )

        #----------------------------------------------------------------------
        # perform the action 
    
        def print_record( eoobj ):   
            eotype = EO_OBJECT_TYPE_REGISTRY[eoobj.real_content_type]
            print "%s\t%s"%( eoobj.identifier, eotype.__name__ ) 

        # construct djnago query-set 
        if identifiers is None : 
            qset = eotype.objects.all()

        elif len(identifiers) == 1 :
            qset = eotype.objects.filter(identifier=identifiers[0])

        elif len(identifiers) > 1 :
            qset = eotype.objects.filter(identifier__contains=identifiers)

        else : # len(identifiers) < 1
            qset = [] 

        # print the selection
        for eoobj in qset : 
            print_record( eoobj )

        #----------------------------------------------------------------------

