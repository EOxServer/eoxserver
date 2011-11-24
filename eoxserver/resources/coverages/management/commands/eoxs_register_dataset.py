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

import os.path
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from eoxserver.core.system import System

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

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--data-file', '--data-files',
            dest='datafiles',
            action='callback', callback=_variable_args_cb,
            default=None,
            help=('Mandatory. One or more paths to a local files '
                  'containing the image data.')
        ),
        make_option('-m', '--metadata-file', '--metadata-files',
            dest='metadatafiles',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more paths to a local files '
                  'containing the image meta data. Defaults to '
                  'the same path as the data file with the '
                  '".xml" extension.')
        ),
        make_option('-r', '--rangetype',
            dest='rangetype',
            help=('Mandatory identifier of the rangetype used in '
                  'the dataset.')
        ),
        make_option('--dataset-series',
            dest='datasetseries_eoids',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more eo ids of a dataset '
                  'series in which the created datasets shall be '
                  'added.')
        ),
        make_option('--stitched-mosaic',
            dest='stitchedmosaic_eoids',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more eo ids of a rectified '
                  'stitched mosaic in which the dataset shall '
                  'be added.')
        ),
        make_option('-i', '--coverage-id', '--coverage-ids',
            dest='coverageids',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more coverage identifier for '
                  'each dataset that shall be added. Defaults to '
                  'the base filename without extension.')
        ),
        make_option('--mode',
            dest='mode',
            choices=['local', 'ftp', 'rasdaman'],
            default='local',
            help=("Optional. Defines the location of the datasets "
                  "to be registered. Can be 'local', 'ftp', or " 
                  "'rasdaman'. Defaults to 'local'.")
        )
    )
    
    help = ('Registers one or more datasets from each a data and '
            'meta-data file.')
    args = '--data-file DATAFILE --rangetype RANGETYPE'

    def print_msg(self, msg, level=0):
        if self.verbosity > level:
            self.stdout.write(msg)
            self.stdout.write("\n")

    def handle(self, *args, **options):
        System.init()
        
        #=======================================================================
        # Collect parameters
        #=======================================================================
        
        self.verbosity = int(options.get('verbosity', 1))
        
        datafiles = options.get('datafiles')
        if datafiles is None:
            raise CommandError(
                "Mandatory parameter --data-file is not present."
            )
        elif len(datafiles) == 0:
            raise CommandError(
                "At least one data-file must be specified."
            )
        
        rangetype = options.get('rangetype')
        if rangetype is None:
            raise CommandError(
                "Mandatory parameter --rangetype is not present."
            )
        
        metadatafiles = options.get('metadatafiles')
        coverageids = options.get('coverageids')
        
        containers = []
        
        # check if insertion into a dataset series is requested.
        # if yes, get the correct wrapper
        datasetseries_eoids = options.get('datasetseries_eoids', [])
        for eoid in datasetseries_eoids:
            dataset_series = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.DatasetSeriesFactory",
                {"obj_id": eoid}
            )
            if dataset_series is None:
                raise CommandError(
                    "Invalid dataset series EO-ID '%s'." % eoid
                )
            containers.append(dataset_series)
        
        stitchedmosaic_eoids = options.get('stitchedmosaic_eoids', [])
        for eoid in stitchedmosaic_eoids:
            stitched_mosaic = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": eoid}
            )
            if stitched_mosaic is None:
                raise CommandError(
                    "Invalid rectified stitched mosaic with coverage ID '%s'." % eoid
                )
            elif stitched_mosaic.getType() != "eo.rect_stitched_mosaic":
                raise CommandError(
                    "Coverage with ID '%s' is not a rectified stitched mosaic." % eoid
                )
            containers.append(stitched_mosaic)
        
        # get the right coverage manager
        mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_dataset"
            }
        )
        
        #=======================================================================
        # Normalize metadata files and coverage id lists
        #=======================================================================
        
        if len(datafiles) > len(metadatafiles):
            metadatafiles.extend([
                os.path.splitext(datafile)[0] + '.xml'
                for datafile in datafiles[len(metadatafiles):]
            ])
        
        if len(datafiles) > len(coverageids):
            coverageids.extend([
                os.path.basename(os.path.splitext(datafile)[0])
                for datafile in datafiles[len(coverageids):]
            ])
        
        #=======================================================================
        # Execute creation and insertion
        #=======================================================================
        
        for df, mdf, cid in zip(datafiles, metadatafiles, coverageids):
            self.print_msg("Inserting coverage with ID '%s'." % cid, 2)
            self.print_msg("\tFile: '%s'\n\tMeta-data: '%s'" % (df, mdf), 2)
            
            # TODO use mode option to allow also ftp and rasdaman
            
            wrapper = mgr.create(
                cid,
                local_path=df,
                md_local_path=mdf,
                range_type_name=rangetype
            )
            
            # add the dataset to the dataset series or mosaic, if requested
            for container in containers:
                container.addCoverage("eo.rect_dataset", wrapper.getModel().pk)
                ctype = (
                    "dataset series" 
                    if container.getType() == "eo.dataset_series"
                    else "rectified stitched mosaic"
                )
                self.print_msg("Added dataset '%s' to %s '%s'." % (
                        wrapper.getCoverageId(), ctype, container.getEOID()
                    ), 2
                )
        
        self.print_msg("Successfully inserted %d dataset%s." % (
                len(datafiles), "s" if len(datafiles) > 1 else ""
            )
        )
