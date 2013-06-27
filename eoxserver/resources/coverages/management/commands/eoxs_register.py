#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#          Daniel Santillan <daniel.santillan@eox.at>
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

#import os.path
#from copy import copy
#import traceback
#from optparse import make_option

from django.core.management.base import CommandError

from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb
)

from eoxserver.backends import models as backends
from eoxserver.resources.coverages import models
from django_extensions.management.commands.runscript import vararg_callback


from django.core.management.base import BaseCommand as BaseDjangoCommand
from django.core.management.base import handle_default_options



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
from argparse import ArgumentParser

def make_option(*args, **kwargs):
    return args, kwargs

class BaseCommand(BaseDjangoCommand):
    arg_list = (
        make_option('-v', '--verbosity', action='store', dest='verbosity', default='1', choices=['0', '1', '2', '3'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--settings',
            help='The Python path to a settings module, e.g. "myproject.settings.main". If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment variable will be used.'),
        make_option('--pythonpath',
            help='A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".'),
        make_option('--traceback', action='store_true',
            help='Print traceback on exception'),
    )
    description = None
    epilog = None
    add_help = True
    prog = None
    usage = None

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command.

        """
        parser = self.create_parser(argv[0], argv[1])
        self.arguments = parser.parse_args(argv[2:])
        handle_default_options(self.arguments)
        options = vars(self.arguments)
        self.execute(**options)

    def get_usage(self, subcommand):
        """
        Return a brief description of how to use this command, by
        default from the attribute ``self.help``.

        """
        return self.usage or '%(prog)s {subcommand} [options]'.format(subcommand=subcommand)

    def create_parser(self, prog_name, subcommand):
        """
        Create and return the ``ArgumentParser`` which will be used to
        parse the arguments to this command.

        """        
        parser = ArgumentParser(
            description=self.description,
            epilog=self.epilog,
            add_help=self.add_help,
            prog=self.prog,
            usage=self.get_usage(subcommand),
        )
        parser.add_argument('--version', action='version', version=self.get_version())
        self.add_arguments(parser)
        return parser
    
    def add_arguments(self, parser):
        for args, kwargs in self.arg_list:
            parser.add_argument(*args, **kwargs)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def verifyDefinition(self, data):
    
    storage_types = ['FTP', 'WCS', 'WMS']
    package_types = ['ZIP', 'TAR']
    file_types = ['tif', 'gif', 'jpg']
    isPackage = True
    
    data_information = []
    
    if (data[0].split(':')[0] in storage_types):
        #data_information.append(data[0].split(':'))
        cnt = 1
    elif(data[0].split(':')[0] in package_types):
        cnt = 0
        
    while isPackage:
        if (data[cnt].split(':')[0] not in package_types):
            isPackage = False
        cnt+=1
    if (data[cnt-1].split('.')[-1] in file_types):
        return True
    return False


class Command(CommandOutputMixIn, BaseCommand):
    arg_list = BaseCommand.arg_list + (
        make_option('-d',
            dest='datafiles',
            #action='callback', callback=_variable_args_cb,
            action="append",
            default=[],
            nargs="+",
            help=('Mandatory. One input data specification.'
                  'The data specification can define an'
                  'additional attribute  depending on the data:'
                  'FTP    FTP:url'
                  'ZIP    ZIP:filepath'
                  )
        ),
        make_option('-m', '--metadata-file', '--metadata-files',
            dest='metadatafiles',
            action='append',
            default=[],
            help=("Optional. One or more EO meta-data specifications."
                  "By default, the mata-data is either retrieved directly "
                  "form the input data or from the accompaninig XML file "
                  "(having the same location and basename as the data files "
                  "but '.xml' extension instead of the original one)." 
                  "The external XML file overides the metada stored" 
                  "directly in the datafile." )
        ),
    )
    
    help = (
        """
        Registers a dataset from a data files/packages and optional meta-data file.
        
        Examples:
        Using shell expansion of filenames and automatic metadata retrieval:
            python manage.py %(name)s \\ 
                --data-files data/meris/mosaic_MER_FRS_1P_RGB_reduced/data.tif \\
        
        Manual selection of data/metadata files:
            python manage.py %(name)s \\
                --data-files 1.tif 2.tif 3.tif \\
                --metadata-files 1.xml 2.xml 3.xml \\
                
        Manual selection of data/metadata files:
            python manage.py %(name)s \\
                -d ZIP:path/file.zip 1.tif 
                -d ZIP:path/file.zip 2.tif \\
                -d ZIP:path/file.zip 3.tif \\
                -m 1.xml
                -m 2.xml 
                -m 3.xml \\
    """ % ({"name": __name__.split(".")[-1]})
    )
    args = '--data-file <file-name> --range-type <range-type>'
    
    #--------------------------------------------------------------------------

    def _error( self , ds , msg ): 
        self.print_err( "Failed to register dataset '%s'!"
                        " Reason: %s"%( ds, msg ) ) 
    #--------------------------------------------------------------------------
            
        
    def handle(self, *args, **opt):
    
        src_data = opt.get('datafiles',[])
        src_meta = opt.get('metadatafiles',[])
        
        if not src_data : 
            raise CommandError( "Missing specification of the data to be "
                "registered!")
            
        for data in src_data:
            if(not verifyDefinition(self, data)):
                print 'ERROR!!'
            
        for metadata in src_meta:
            if(not verifyDefinition(self, metadata)):
                print 'ERROR!!'
            
    
        # TODO: for each data/metadata item
            # for each path item
                # parse "type" and "path"
                # check if it refers to storage/package/file
    
    
    
    
    
    
    
            
    #backends.
    
    
    
    
    
    
    
    
    
    
    
    