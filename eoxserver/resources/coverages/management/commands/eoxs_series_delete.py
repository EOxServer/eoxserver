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

from eoxserver.resources.coverages.models import DatasetSeries 
from eoxserver.resources.coverages.models import EOObject
from eoxserver.resources.coverages.models import EO_OBJECT_TYPE_REGISTRY 


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier", "--dataset-series-id", 
            dest="identifier", action="store", default=None,
            help=("Dataset series identifier.")
        ),
        make_option("-r", "--recursive-delete", 
            dest="recursive_delete",
            action="store_true",default=False,
            help=("Optional. Delete all sub-ordnate dataset series.")
        ),
        make_option("-u", "--unlink-children", 
            dest="unlink_children",
            action="store_true",default=False,
            help=("Optional. Unlink all sub-ordnate dataset series.")
        ),
    )

    #args = "<identifier>"
    
    help = (
    """ Delete an existing Dataset Series.

        By default the command refuses to deletete 
        dataset series contaning any sub-ordinate 
        eo-objects. If explicitely requested (-u), 
        the command unlinks the subordinate eo-object.
        The subordinate dataset-series can be either 
        unlinked (-u) or recursively deleted (-r). 
        Subordinate directories linked by another 
        series will not be removed.

    """ % ({"name": __name__.split(".")[-1]}))


    @transaction.commit_on_success
    def handle(self, *args, **opt):

        #----------------------------------------------------------------------
        # check the inputs 

        # check required identifier 
        identifier = opt.get('identifier',None)
        if identifier is None : 
            raise CommandError("Missing the mandatory dataset series identifier!")

        opt['unlink_children'] = bool( opt.get('unlink_children',False) ) 
        opt['recursive_delete'] = bool( opt.get('recursive_delete',False) ) 

        #----------------------------------------------------------------------
        # perform the action 
    
        self._delete_series( identifier, opt ) 

        #----------------------------------------------------------------------

        self.print_msg( "Dataset Series deleted sucessfully." ) 


    def _delete_series( self, identifier, opt, level=0, identifier0=None ) : 
        """ recoursive dataset series removal """ 

        padding = "".rjust(2*level,".")

        # trap circular dependencies which should not ever happen 
        if (level >0) and ( identifier == identifier0 ) :
            raise CommandError("Circular dependency! Integrity of the database"
                                  "seems to be broken!")

        self.print_msg("%sDeleting Dataset Series: '%s'"%(padding,identifier))

        try: 

            # find the series 
            series = DatasetSeries.objects.get(identifier=identifier) 

            # process subordinates 
            for child in series.eo_objects.all() :
                
                eotype   = EO_OBJECT_TYPE_REGISTRY[child.real_content_type]
                is_ds    = ( eotype == DatasetSeries ) 
                link_cnt = child.collections.all().count() 

                if is_ds and opt['recursive_delete'] : 

                    if link_cnt > 1 : 
                        
                        self.print_msg( "%sUnlinking: '%s' <-x- '%s' (%s)" %( 
                            padding,identifier,child.identifier,eotype.__name__))
                       
                        # let's leave django to the job
                        # series.insert( child ) 

                    else : 

                        self._delete_series( child.identifier, opt, level+1, identifier ) 

                elif opt['unlink_children'] : 

                    self.print_msg( "%sUnlinking: '%s' <-x- '%s' (%s)" %( 
                            padding,identifier,child.identifier,eotype.__name__))

                    # let's leave django to the job
                    # series.insert( child ) 

                else : 
                    
                    raise CommandError("An attempt to remove non-empty "
                        " DatasetSeries: '%s'"%(identifier) ) 

            # final removal 
            series.delete()

        except CommandError : raise 

        except DatasetSeries.DoesNotExist : 
            raise CommandError("There is no dataset series matching the givent"
                        " identifier: '%s'"%identifier)

        except Exception as e : 

            # print stack trace if required 
            if opt.get("traceback", False):
                self.print_msg(traceback.format_exc())

            raise CommandError("Dataset series removal failed! REASON=%s"%(e))

