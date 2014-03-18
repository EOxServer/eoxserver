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

#from eoxserver.backends import models as backends
from eoxserver.resources.coverages.models import Coverage

class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier", dest="identifier", 
            action="store", default=None,
            help=("Coverage identifier.")
        ),
        make_option("-d", "--idx", "--index", dest="index",
            action="store", default=None,
            help=("Index of the data item to be removed.")
        ),
        make_option("-s", "--semantic", dest="semantic",
            action="store", default=None,
            help=("Semantic of the data item(s) to be removed.")
        ),
    )

    args = "-i <id> [-s <semantic>]|[-d <index>]"

    help = (
    """
    Remove one or more data items assigned to the Coverage of the given
    identifier.
    """ 
    )

    def handle(self, *args, **opt):

        #----------------------------------------------------------------------
        # check the inputs 

        # check required identifier 
        identifier = opt.get('identifier',None)
        if identifier is None : 
            raise CommandError("Missing the required coverage identifier!")

        # check required semantic or index 
        semantic = opt.get('semantic',None)
        index    = opt.get('index',None)

        if (semantic is None) and (index is None):
            raise CommandError("Index of semantic must be specified")

        # check index value 
        if index: 
            try:
                index = int(index) 
                if index < 1 : raise ValueError 
            except ValueError: 
                raise CommandError("Invalid index value '%s' !"%index)

        #----------------------------------------------------------------------
        # perform the action 
    
        # find the coverage 
        try:
            cov = Coverage.objects.get(identifier=identifier)
        except Coverage.DoesNotExist: 
            raise CommandError("Invalid coverage identifier: '%s' !"%(identifier)) 


        data_items = [] 

        if index is not None : 
            # list the data items 
            for i,di in enumerate( cov.data_items.all().order_by("id") ) : 
                if index == ( i + 1 ) : 
                    semantic = di.semantic
                    data_items.append(di)
                    break
            else:
                raise CommandError("Invalid index value '%s' !"%index)

        elif semantic is not None : 

            data_items = cov.data_items.filter(semantic=semantic)

            if len(data_items) == 0 : 
                raise CommandError("Invalid index semantic '%s' !"%semantic)
            
        for di in data_items:
            di.delete() 

        self.print_msg("%d item%s '%s' deleted from coverage '%s'."%(
            len(data_items),("s","")[len(data_items)==1],
            semantic, identifier
        ))

        #----------------------------------------------------------------------



