#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

import logging
import traceback
from urlparse import urlparse
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from eoxserver.core.system import System
from eoxserver.backends.local import LocalPath
from eoxserver.backends.ftp import RemotePath
from eoxserver.resources.coverages.models import LocalDataPackage,\
    RemoteDataPackage
from eoxserver.resources.coverages.exceptions import NoSuchCoverageException


logger = logging.getLogger(__name__)

def _variable_args_cb(option, opt_str, value, parser):
    """ Helper function for optparse module. Allows
        variable number of option values when used
        as a callback.
    """
    args = []
    for arg in parser.rargs:
        if not arg.startswith('-'):
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)
    
    
class StringFormatCallback(object):
    """ Small helper class to supply a variable number of arguments to a 
    callback function and store the resulting value in the `dest` field of the 
    parser. 
    """
    
    def __init__(self, callback):
        self.callback = callback
        
    def __call__(self, option, opt_str, value, parser):
        args = []
        for arg in parser.rargs:
            if not arg.startswith('-'):
                args.append(arg)
            else:
                del parser.rargs[:len(args)]
                break
        
        setattr(parser.values, option.dest, self.callback(" ".join(args)))
        

class CommandOutputMixIn(object):
    def print_msg(self, msg, level=0, error=False):
        verbosity = getattr(self, "verbosity", 1)
        traceback = getattr(self, "traceback", False)
        
        if verbosity > level:
            if error and traceback:
                self.stderr.write(traceback.format_exc() + "\n") 
            self.stderr.write(msg)
            self.stderr.write("\n")
        
        if level == 0 and error:
            logger.critical(msg)
        elif level == 1 and error:
            logger.error(msg)
        elif level in (0, 1, 2) and not error:
            logger.info(msg)
        elif level > 2:
            logger.debug(msg)


class DatasetManagementCommand(BaseCommand, CommandOutputMixIn):
    """ Base class for dataset management commands involving datasets and 
    dataset series.
    """
    
    option_list = BaseCommand.option_list + (
        make_option("--dataset", "--datasets", dest="dataset_ids", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Optional. One or more IDs of Datasets (either the Coverage "
                  "ID or the EO-ID).")
        ),
        make_option("--dataset-series", dest="datasetseries_ids", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Optional. One or more EO-IDs referencing Dataset Series.")
        ),
        make_option("--mode", dest="mode", default="id",
            choices=("id", "filename"),
            help=("Optional. This parameter defines how the datasets are " 
                  "identified.")
        )
    )
    
    def handle(self, *args, **options):
        System.init()
        
        self.verbosity = options["verbosity"]
        mode = options["mode"]
        
        if ((options["dataset_ids"] is None 
             or options["datasetseries_ids"] is None) and
            len(args) < 2):
            raise CommandError("Not enough arguments given.")
        
        dataset_ids = options["dataset_ids"] or args[:-1]
        datasetseries_ids = options["datasetseries_ids"] or args[-1:]
        
        # TODO: make arbitrary insertions possible, like data sources, etc.
        
        if mode == "filename":
            files = dataset_ids
            dataset_ids = []
            
            for path in files:
                dataset_ids.extend(self.get_dataset_ids_for_path(path))
        
        with transaction.commit_on_success():
            try:
                self.manage_datasets(dataset_ids, datasetseries_ids)
            except NoSuchCoverageException, e:
                raise CommandError("No coverage with ID '%s' registered" % e.msg)


    def manage_datasets(self, dataset_ids, datasetseries_ids):
        """ Main method for dataset handling.
        """
        raise NotImplementedError()
    
    def manage(self, params):
        """ Main method of dataset handling.
        """
        pass

    def get_dataset_ids_for_path(self, path):
        """ Returns the coverage IDs of all coverages that are referencing this
        exact path.
        """
        
        url = urlparse(path, "file")
        
        if url.scheme == "file":
            datapackages = LocalDataPackage.objects.filter(
                data_location__path=path
            )
        elif url.scheme == "ftp":
            datapackages = RemoteDataPackage.objects.filter(
                data_location__path=path,
                data_location__storage__host=url.hostname,
                data_location__storage__port=url.port,
                data_location__storage__user=url.username,
                data_location__storage__passwd=url.password
            )
        elif url.scheme == "rasdaman":
            raise NotImplementedError()
        else:
            raise CommandError("Unknown location type '%s'." % url.scheme)
        
        result = []
        
        for record in datapackages:
            datapackage = System.getRegistry().getFromFactory(
                factory_id="resources.coverages.data.DataPackageFactory",
                params={
                    "record": record
                }
            )
        
            result.extend([coverage.getCoverageId() for coverage in datapackage.getCoverages()])
        
        if len(result) == 0:
            raise CommandError("No coverage with path '%s' found." % path)
        
        return result
