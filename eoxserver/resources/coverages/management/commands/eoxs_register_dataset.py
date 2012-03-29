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
import datetime
from copy import copy
import traceback
from optparse import make_option

from osgeo import gdal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from eoxserver.core.system import System
from eoxserver.core.util.geotools import extentFromDataset
from eoxserver.core.util.timetools import getDateTime
from eoxserver.resources.coverages.geo import GeospatialMetadata
from eoxserver.resources.coverages.exceptions import MetadataException
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, StringFormatCallback
)
from eoxserver.resources.coverages.metadata import EOMetadata
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.contrib.gis.geos.polygon import Polygon


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--data-file', '--data-files',
                    '--collection', '--collections',
            dest='datafiles',
            action='callback', callback=_variable_args_cb,
            default=None,
            help=('Mandatory. One or more paths to a files '
                  'containing the image data. These paths can '
                  'either be local, ftp paths, or rasdaman '
                  'collection names.')
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
        ),
        make_option('--host',
            dest='host',
            default=None,
            help=("Mandatory when mode is not 'local'. Defines the "
                  "ftp/rasdaman host to locate the dataset.")
        ),
        make_option('--port',
            dest='port', type='int',
            default=None,
            help=("Optional. Defines the port for ftp/rasdaman host "
                  "connections.")
        ),
        make_option('--user',
            dest='user',
            default=None,
            help=("Optional. Defines the ftp/rasdaman user for the "
                  "ftp/rasdaman connection.")
        ),
        make_option('--password',
            dest='password',
            default=None,
            help=("Optional. Defines the ftp/rasdaman user password "
                  "for the ftp/rasdaman connection.")
        ),
        make_option('--database',
            dest='database',
            default=None,
            help=("Optional. Defines the rasdaman database containing "
                  "the data.")
        ),
        make_option('--oid', '--oids',
            dest='oids',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=("Optional. List of rasdaman oids for each dataset "
                  "to be inserted.")
        ),
        make_option('--default-srid',
            dest='default_srid',
            default=None,
            help=("Optional. Default SRID, needed if it cannot be " 
                  "determined automatically by GDAL.")
        ),
        make_option('--default-size',
            dest='default_size',
            default=None,
            help=("Optional. Default size, needed if it cannot " 
                  "be determined automatically by GDAL. "
                  "Format: <sizex>,<sizey>")
        ),
        make_option('--default-extent',
            dest='default_extent',
            default=None,
            help=("Optional. Default extent, needed if it cannot be determined " 
                  "automatically by GDAL. "
                  "Format: <minx>,<miny>,<maxx>,<maxy>")
        ),
        make_option('--default-begin-time',
            dest='default_begin_time',
            action="callback", callback=StringFormatCallback(getDateTime),
            default=None,
            help=("Optional. Default begin timestamp when no other EO-metadata " 
                  "is available. The format is ISO-8601.")
        ),
        make_option('--default-end-time',
            dest='default_end_time',
            action="callback", callback=StringFormatCallback(getDateTime),
            default=None,
            help=("Optional. Default end timestamp when no other EO-metadata " 
                  "is available. The format is ISO-8601.")
        ),
        make_option('--default-footprint',
            dest='default_footprint',
            action="callback", callback=StringFormatCallback(str),
            default=None,
            help=("Optional. The default footprint in WKT format when no other " 
                  "EO-metadata is available.")
        ),
        make_option('--visible',
            dest='visible',
            default=True,
            help=("Optional. Sets the visibility status of all datasets to the"
                  "given boolean value. Defaults to 'True'.")
        )
    )
    
    help = ('Registers one or more datasets from each data and '
            'meta-data file.')
    args = '--data-file DATAFILE --rangetype RANGETYPE'

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
        mode = options.get('mode', 'local')
        default_srid = options.get("default_srid")
        default_size = options.get("default_size")
        default_extent = options.get("default_extent")
        default_begin_time = options.get("default_begin_time")
        default_end_time = options.get("default_end_time")
        default_footprint = options.get("default_footprint")
        visible = options.get("visible", True)
        
        datasetseries_eoids = options.get('datasetseries_eoids', [])
        stitchedmosaic_eoids = options.get('stitchedmosaic_eoids', [])
        
        host = options.get("host")
        port = options.get("port")
        user = options.get("user")
        password = options.get("password")
        oids = options.get("oids")
        database = options.get("database")
        
        if mode in ('rasdaman', 'ftp') and host is None:
            raise CommandError(
                "The '--host' parameter is required when mode "
                "is 'ftp' or 'rasdaman'."
            )
        
        #=======================================================================
        # Setup default geo metadata
        #=======================================================================
        
        default_geo_metadata = None
        extent = None
        if ((default_size is None and default_extent is not None) or
            (default_size is not None and default_extent is None)):
            raise CommandError(
                "Use either both of '--default-size' and '--default-extent' "
                "or none."
            )
        elif default_size is not None and default_extent is not None:
            if default_srid is None:
                raise CommandError(
                    "When setting '--default-size' and '--default-extent' the "
                    "parameter '--default-srid' is mandatory."
                )
            
            sizes = [int(size) for size in default_size.split(",")]
            extent = [float(bound) for bound in default_extent.split(",")]
            
            if len(sizes) != 2: 
                raise CommandError("Wrong format for '--default-size' parameter.")
            if len(extent) != 4: 
                raise CommandError("Wrong format for '--default-extent' parameter.")
            
            default_geo_metadata = GeospatialMetadata(
                default_srid, sizes[0], sizes[1], extent
            )
        
        #=======================================================================
        # Setup default EO metadata
        #=======================================================================
        
        default_eo_metadata = None
        if (default_begin_time is not None or default_end_time is not None
            or default_footprint is not None):
            
            footprint = None
            if default_footprint is not None:
                footprint = GEOSGeometry(default_footprint)
            elif extent is not None:
                footprint = Polygon.from_bbox(tuple(extent))
            
            default_eo_metadata = EOMetadata(
                None, default_begin_time, default_end_time, footprint, None
            )
        
        #=======================================================================
        # Normalize metadata files and coverage id lists
        #=======================================================================
        
        if len(datafiles) > len(metadatafiles):
            if mode == "rasdaman":
                raise CommandError(
                    "All rasdaman datasets require local metadata. "
                    "Use the --metadata-files option."
                )
            
            for datafile in datafiles[len(metadatafiles):]:
                new_path = os.path.splitext(datafile)[0] + '.xml'
                if os.path.exists(new_path):
                    metadatafiles.append(new_path)
                else:
                    metadatafiles.append(datafile)
        
        if len(datafiles) > len(coverageids):
            if mode == "rasdaman":
                raise CommandError(
                    "All rasdaman datasets require an explicit ID. "
                    "Use the --coverage-id option."
                )
            
            coverageids.extend([
                os.path.basename(os.path.splitext(datafile)[0])
                for datafile in datafiles[len(coverageids):]
            ])
        
        
        if mode in ("ftp", "rasdaman"):
            self.print_msg(
                """Using %s-connection:
                    Host: %s
                    Port: %s
                    User: %s
                    Password: %s
                    %s
                """ % (
                    mode, host, port, user, password,
                    "Database: %s" % database
                    if mode == 'rasdaman' else "" 
                ), 2
            )
        
        rect_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_dataset"
            }
        )
        
        #=======================================================================
        # Execute creation and insertion
        #=======================================================================
        
        for df, mdf, cid in zip(datafiles, metadatafiles, coverageids):
            self.print_msg("Inserting coverage with ID '%s'." % cid, 2)
            
            args = {
                "obj_id": cid,
                "range_type_name": rangetype,
                "default_srid": default_srid,
                "container_ids": datasetseries_eoids + stitchedmosaic_eoids,
                "visible": visible
            }
            
            eo_metadata = None
            if default_eo_metadata is not None:
                eo_metadata = copy(default_eo_metadata)
                eo_metadata.eo_id = os.path.splitext(os.path.basename(df))[0]
            
            if mode == 'local':
                self.print_msg("\tFile: '%s'\n\tMeta-data: '%s'" % (df, mdf), 2)
                args.update({
                    "local_path": df,
                    "md_local_path": mdf,
                })
                if eo_metadata is not None and eo_metadata.footprint is None:                
                    ds = gdal.Open(df)
                    if ds is not None:
                        eo_metadata.footprint = Polygon.from_bbox(extentFromDataset(ds))
            
            elif mode == 'ftp':
                self.print_msg("\tFile: '%s'\n\tMeta-data: '%s'" % (df, mdf), 2)
                args.update({
                    "remote_path": df,
                    "md_remote_path": mdf,
                    
                    "ftp_host": host,
                    "ftp_port": port,
                    "ftp_user": user,
                    "ftp_passwd": password
                })
            elif mode == 'rasdaman':
                try:
                    oid = oids.pop(0)
                except IndexError:
                    oid = None
                
                self.print_msg(
                    "\tCollection: '%s'\n\tOID:%s\n\tMeta-data: '%s'" % (
                        df, oid, mdf
                    ), 2
                )
                
                args.update({
                    "collection": df,
                    "oid": oid,
                    "md_local_path": mdf,
                    
                    "ras_host": host,
                    "ras_port": port,
                    "ras_user": user,
                    "ras_passwd": password,
                    "ras_db": database
                })
            
            #===================================================================
            # Get the right manager
            #===================================================================
            mgr_to_use = rect_mgr
            
            geo_metadata = default_geo_metadata
            if geo_metadata is None:
                try:
                    # TODO: for rasdaman build identifiers
                    # for FTP not possible?
                    geo_metadata = GeospatialMetadata.readFromDataset(
                        gdal.Open(df),
                        default_srid
                    )
                except RuntimeError:
                    pass
            
            if geo_metadata is not None:
                args["geo_metadata"] = geo_metadata
                
                if geo_metadata.is_referenceable:
                    ref_mgr = System.getRegistry().findAndBind(
                        intf_id="resources.coverages.interfaces.Manager",
                        params={
                            "resources.coverages.interfaces.res_type": "eo.ref_dataset"
                        }
                    )
                    mgr_to_use = ref_mgr
                    self.print_msg("\t'%s' is referenceable." % df, 2)
            
            if eo_metadata is not None:
                # we cannot check at this point whether or not the file exists 
                # on FTP. So we assume it does.
                if mode != "ftp" and not os.path.exists(mdf):
                    if eo_metadata.footprint is None:
                        raise CommandError("Default footprint could not be determined.")
                    if eo_metadata.begin_time is None:
                        eo_metadata.begin_time = datetime.datetime.utcnow()
                    if eo_metadata.end_time is None:
                        eo_metadata.end_time = datetime.datetime.utcnow()
                
                args["eo_metadata"] = eo_metadata
                
            try:
                with transaction.commit_on_success():
                    mgr_to_use.create(**args)
            except MetadataException, e: #TODO here
                self.print_msg(
                    "ERROR: registration of dataset failed, message was '%s'" % str(e),
                    1, error=True
                )
                if options.get("traceback", False):
                    self.print_msg(traceback.format_exc())
        
        self.print_msg("Successfully inserted %d dataset%s." % (
                len(datafiles), "s" if len(datafiles) > 1 else ""
            )
        )
