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
from eoxserver.resources.coverages.models import (
    ReferenceableDataset, RectifiedDataset, EOObject
)


class Command(CommandOutputMixIn, BaseCommand):

    args = "<identifier> [<identifier> ...]"
    
    help = (
    """ Deregister a Dataset.  
    """ % ({"name": __name__.split(".")[-1]}))


    @transaction.commit_on_success
    def handle(self, *args, **opt):
        # check required identifier 
        if not args: 
            raise CommandError("Missing the mandatory dataset identifier(s)!")

        for identifier in args:
            self.print_msg("Deleting Dataset: '%s'" % (identifier))
            try:
                # locate coverage an check the type 
                dataset = EOObject.objects.get(identifier=identifier).cast()

                if dataset.real_type not in (RectifiedDataset, ReferenceableDataset): 
                    raise EOObject.DoesNotExist
                # final removal
                dataset.delete()

            except EOObject.DoesNotExist: 
                raise CommandError(
                    "There is no dataset matching the givent identifier: '%s'"
                    % identifier
                )

            except Exception, e:
                # print stack trace if required 
                if opt.get("traceback", False):
                    self.print_msg(traceback.format_exc())

                raise CommandError(
                    "Dataset deregistration failed! REASON=%s" % e
                )

        self.print_msg("Dataset deregistered sucessfully.") 
