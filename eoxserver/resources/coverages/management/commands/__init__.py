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
from optparse import make_option, OptionValueError

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from eoxserver.core.system import System
from eoxserver.backends.local import LocalPath
from eoxserver.backends.ftp import RemotePath
from eoxserver.resources.coverages.models import LocalDataPackage,\
    RemoteDataPackage
from eoxserver.resources.coverages.exceptions import NoSuchCoverageException

from django.contrib.gis.geos.geometry import GEOSGeometry

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import CoverageIdManager
from eoxserver.resources.coverages.managers import getDatasetSeriesManager

#-------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------

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
       
        try : 
            setattr(parser.values, option.dest, self.callback(" ".join(args)))
        except ValueError as e : 
            raise OptionValueError( e.message ) 
        

class CommandOutputMixIn(object):

    def print_err(self, msg ):
    
        # single level for all errors 
        # errors ALWAYS printed 
        # errors ALWAYS logged  

        logger.error(msg) 

        self.stderr.write("ERROR: %s\n"%msg)


    def print_wrn(self, msg ): 

        verbl = max(0,getattr(self, "verbosity", 1)) 

        # single level for all warnings 
        # print of warnings suppressed in silent mode 
        # warnings ALWAYS logged  

        logger.warning(msg) 

        if 0 < verbl : 
            self.stderr.write("WARNING: %s\n"%msg)


    def print_msg(self, msg, level=1):

        # three basic level of info messages 
        # level == 0 - always printed even in the silent mode - not recommended
        # level == 1 - normal info suppressed in silent mode
        # level >= 2 - debuging message (additional levels allowed) 
        # messages ALWAYS logged (as either info or debug)
    
        level = max(0,level) 
        verbl = max(0,getattr(self, "verbosity", 1)) 

        if level >= 2 : # everything with level 2 or higher is DEBUG 

            prefix = "DEBUG"
            logger.debug(msg)

        else : # levels 0 (silent) and 1 (default-verbose)

            prefix = "INFO"
            logger.info(msg)

        if ( level <= verbl ) : 
            self.stdout.write("%s: %s\n"%(prefix,msg)) 

#-------------------------------------------------------------------------------

def get_dataset_ids_for_path(self, path):
    "Return IDs of all datasets that are referencing the given path." 
    
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
        raise CommandError("No dataset matching the given path found. PATH='%s'" % path)
    
    return result

#-------------------------------------------------------------------------------
# parsers - auxiliary subroutines

# footprint parser 

def _footprint( src ) : 
    try: 
        return GEOSGeometry( src )
    except ValueError : 
        raise ValueError("Invalid 'footprint' specification '%s' !"%src ) 
       
# size parser 

def _size( src ) : 

    print "SRC-SIZE:" , src 

    try: 
        tmp = tuple([ int(v) for v in src.split(",") ])
        print "TMP" , tmp , len(tmp) 
        if len(tmp) != 2 : raise ValueError 
        if ( tmp[0] < 0 ) or ( tmp[1] < 0 ) : raise ValueError 
        return tmp 
    except ValueError : 
        raise ValueError("Invalid 'size' specification '%s' !"%src)


# extent parser 

def _extent( src ) : 

    try: 
        tmp = tuple([ float(v) for v in src.split(",") ])
        if len(tmp) != 4 : raise ValueError 
        return tmp 
    except ValueError : 
        raise ValueError("Invalid 'extent' specification '%s' !"%src)

#-------------------------------------------------------------------------------

class ManageDatasetSeriesCommand(BaseCommand, CommandOutputMixIn):
    """Base class for dataset series content mangement commands.""" 

    args = ("-d DS1 [DS2 [...]] -s DSS1 [DSS2 [...]]")
    
    option_list = BaseCommand.option_list + (
        make_option("-d","--dataset", "--datasets", dest="dataset_ids", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Optional. One or more IDs of Datasets (either the Coverage "
                  "ID or the EO-ID).")
        ),
        make_option("-s","--dataset-series", dest="datasetseries_ids", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Optional. One or more EO-IDs referencing Dataset Series.")
        ),
#        make_option("-m","--mode", dest="mode", default="id",
#            choices=("id", "filename"),
#            help=("Optional. This parameter defines how the datasets are " 
#                  "identified.")
#        )
    )
    
    def handle(self, *args, **options):

        System.init()

        id_manager  = CoverageIdManager()
        dss_manager = getDatasetSeriesManager() 
        
        self.verbosity = options["verbosity"]
        #mode = options["mode"]
        
        if ((options["dataset_ids"] is None 
             or options["datasetseries_ids"] is None) and
            len(args) < 2):
            raise CommandError("Not enough arguments given.")
        
        # MP: WARNING Non-documented args semantics!
        dataset_ids = options["dataset_ids"] or args[:-1]
        datasetseries_ids = options["datasetseries_ids"] or args[-1:]
        
        # TODO: make arbitrary insertions possible, like data sources, etc.

        # MP: The filename to ID conversion should be done elsewehere
        # do not create another egg-laying cow-monster!
        #
        #if mode == "filename":
        #    files = dataset_ids
        #    dataset_ids = []
            
        #    for path in files:
        #        dataset_ids.extend(self.get_dataset_ids_for_path(path))
        
        # check the ids - report the non-existing ones!

        def check_ds_id( id ) : 
            if id_manager.getType(id) in ( "RectifiedDataset" , 
                "ReferenceableDataset" ) : 
                return True 
            else:
                self.print_err( "Invalid dataset ID excluded from the input"
                    " list! ID='%s'" % ( id ) ) 
                return False 

        def check_dss_id( id ) : 
            if id_manager.getType(id) == "DatasetSeries" : 
                return True 
            else:
                self.print_err( "Invalid dataset series ID excluded from the input"
                    " list! ID='%s'" % ( id ) ) 
                return False 
        
        dataset_ids = filter( check_ds_id , dataset_ids ) 
        datasetseries_ids = filter( check_dss_id , datasetseries_ids ) 

        # stop if one of the lists is empty 
        if (len(dataset_ids)<1) or (len(datasetseries_ids)<1) : return 

        # otherwise perform the action 
        with transaction.commit_on_success():
            try:
                self.manage_series(dss_manager,dataset_ids,datasetseries_ids)
            except NoSuchCoverageException, e:
                raise CommandError("No coverage with ID '%s' registered" % e.msg)


    def manage_series(self, manager, dataset_ids, datasetseries_ids):
        """ Main method for dataset handling."""
        # to be implemented by the derived classes
        raise NotImplementedError()
    
#-------------------------------------------------------------------------------
