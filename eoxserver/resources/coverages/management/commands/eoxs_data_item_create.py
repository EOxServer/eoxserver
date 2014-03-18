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

from eoxserver.backends import models as backends
from eoxserver.resources.coverages.models import Coverage

class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier", dest="identifier", 
            action="store", default=None,
            help=("Coverage identifier.")
        ),
        make_option("-s", "--semantic", dest="semantic",
            action="store", default=None,
            help=("Data item's semantic.")
        ),
        make_option("-l", "--location", dest="location",
            action="store", default=None,
            help=("Data item's location.")
        ),
        make_option("-f", "--format", dest="format",
            action="store", default=None,
            help=("Optional data item's format.")
        ),
    )

    args = "-i <id> -s <semantic> -l <location> [-f <format>]"

    help = (
    """
    Assign new data item to a Coverage of the given identifier.
    """ 
    )

    def handle(self, *args, **opt):

        #----------------------------------------------------------------------
        # check the inputs 

        # check required identifier 
        identifier = opt.get('identifier',None)
        if identifier is None : 
            raise CommandError("Missing the required coverage identifier!")

        # check required semantic
        semantic = opt.get('semantic',None)
        if semantic is None : 
            raise CommandError("Missing the data item's semantic!")

        # check required location 
        location = opt.get('location',None)
        if location is None : 
            raise CommandError("Missing the required coverage location!")

        # check optional format 
        format = opt.get('format',None)
        #if format is None : 
        #    raise CommandError("Missing the required coverage format!")

        #TODO: strage and package handling 
        storage = None
        package = None  

        #----------------------------------------------------------------------
        # perform the action 
    
        # find the coverage 
        try:
            cov = Coverage.objects.get(identifier=identifier)
        except Coverage.DoesNotExist: 
            raise CommandError("Invalid coverage identifier: '%s' !"%(identifier)) 

        data_item = backends.DataItem(
            location=location, format=(format or ""), semantic=semantic, 
            storage=storage, package=package,
        )
        data_item.dataset = cov
        data_item.full_clean()
        data_item.save()

        self.print_msg("Data item '%s' created for coverage '%s'."%(semantic,identifier))
        #----------------------------------------------------------------------


