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

from eoxserver.resources.coverages.models import ReferenceableDataset 
from eoxserver.resources.coverages.models import RectifiedDataset 
from eoxserver.resources.coverages.models import EOObject
from eoxserver.resources.coverages.models import EO_OBJECT_TYPE_REGISTRY 


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier", "--dataset-series-id", 
            dest="identifier", action="store", default=None,
            help=("Dataset identifier.")
        ),
    )

    #args = "<identifier>"
    
    help = (
    """ Deregister an existing Dataset.  
    """ % ({"name": __name__.split(".")[-1]}))


    @transaction.commit_on_success
    def handle(self, *args, **opt):

        #----------------------------------------------------------------------
        # check the inputs 

        # check required identifier 
        identifier = opt.get('identifier',None)
        if identifier is None : 
            raise CommandError("Missing the mandatory dataset identifier!")

        #----------------------------------------------------------------------
        # perform the action 
    
        self.print_msg("Deleting Dataset: '%s'"%(identifier))

        try: 

            # locate coverage an check the type 
            eoobj  = EOObject.objects.get(identifier=identifier) 
            eotype = EO_OBJECT_TYPE_REGISTRY[eoobj.real_content_type]

            if eotype not in ( RectifiedDataset, ReferenceableDataset ) : 
                raise EOObject.DoesNotExist ; 
                
            dataset = eotype.objects.get(identifier=identifier)

            # final removal 
            dataset.delete()

        #except CommandError : raise 

        except EOObject.DoesNotExist : 
            raise CommandError("There is no dataset matching the givent"
                        " identifier: '%s'"%identifier)

        except Exception as e : 

            # print stack trace if required 
            if opt.get("traceback", False):
                self.print_msg(traceback.format_exc())

            raise CommandError("Dataset series removal failed! REASON=%s"%(e))



        #----------------------------------------------------------------------

        self.print_msg( "Dataset Series deleted sucessfully." ) 
