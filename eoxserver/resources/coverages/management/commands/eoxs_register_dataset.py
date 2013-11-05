#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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
from copy import copy
import traceback
from optparse import make_option, OptionValueError

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.contrib.gis.geos.polygon import Polygon

from eoxserver.contrib import gdal
from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime
from eoxserver.resources.coverages.geo import ( 
    GeospatialMetadata, getExtentFromRectifiedDS, getExtentFromReferenceableDS
)
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, StringFormatCallback, 
    _footprint, _size, _extent,
)
from eoxserver.resources.coverages.metadata import EOMetadata

from eoxserver.processing.gdal import reftools as rt 

#------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import getRectifiedDatasetManager
from eoxserver.resources.coverages.managers import getReferenceableDatasetManager
from eoxserver.resources.coverages.managers import getRectifiedStitchedMosaicManager 
from eoxserver.resources.coverages.managers import getDatasetSeriesManager 

from eoxserver.resources.coverages.rangetype import isRangeTypeName

#------------------------------------------------------------------------------

def _extract_geo_md( fname, default_srid = None ) : 
    """
    Extract geo-meta-data from the source data file if possible.
    The ``default_srid`` parameter can be specified as an fallback
    when GDAL fails determine EPSG code of image or GCP projection.  
    """

    # TODO: for rasdaman build identifiers
    # TODO: FTP input 

    ds = gdal.Open(fname)

    if ds is None : return None 

    return GeospatialMetadata.readFromDataset(ds, default_srid)


#------------------------------------------------------------------------------

class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--data-file', '--data-files',
                    '--collection', '--collections',
            dest='datafiles',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Mandatory. One or more input data specifications.'
                  'The data specification can be either path to a local file, '
                  'FTP path, or rasdaman collection name.')
        ),
        make_option('-m', '--metadata-file', '--metadata-files',
            dest='metadatafiles',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=("Optional. One or more EO meta-data specifications."
                  "By default, the mata-data is either retrieved directly "
                  "form the input data or from the accompaninig XML file "
                  "(having the same location and basename as the data files "
                  "but '.xml' extension instead of the original one)." 
                  "The external XML file overides the metada stored" 
                  "directly in the datafile." )
        ),
        make_option('-r', '--range-type', '--rangetype',
            dest='rangetype',
            default=None,
            help=('Mandatory identifier of the range-type of all the datasets'
                  'being registered.' ) 
        ),
        make_option('--series','--dataset-series',
            dest='ids_series',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more ids of dataset series '
                   'to which the registerd dataset(s) shall be added.')
        ),
        make_option('--mosaic','--stitched-mosaic',
            dest='ids_mosaic',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more ids of rectified stitched mosaics '
                  'to which the registered dataset(s) shall be added.')
        ),
        make_option('-i', '--id' , '--ids', '--coverage-id', '--coverage-ids',
            dest='ids',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=('Optional. One or more identifiers for each dataset '
                  'that shall be added. The default name is derived either ' 
                  'from the EO metadata or from the data file base name.')
        ),
        make_option('-s','--source-type','--mode',
            dest='source_type',
            choices=['local', 'ftp', 'rasdaman'],
            default='local',
            help=("Optional. The source type of the datasets to be "
                  "registered. Currently 'local', 'ftp', or 'rasdaman' "
                  "backends are supported. Defaults to 'local'.")
        ),
        make_option('--host',
            dest='host',
            default=None,
            help=("Mandatory for non-local backends. The host address "
                  "where the remote datasets are located.")
        ),
        make_option('--port',
            dest='port', type='int',
            default=None,
            help=("Optional. Non-default port to access remote datasets.")
        ),
        make_option('--user',
            dest='user',
            default=None,
            help=("Optional. Username needed to access remote datasets.")
        ),
        make_option('--password',
            dest='password',
            default=None,
            help=("Optional. Plain text password needed to access remote "
                  "datasets.")
        ),
        make_option('--database','--rasdb',
            dest='rasdb',
            default=None,
            help=("Optional. Name of the rasdaman holding the registered "
                  "data.")
        ),
        make_option('--oid', '--oids',
            dest='oids',
            action='callback', callback=_variable_args_cb,
            default=[],
            help=("Optional. List of rasdaman oids for each dataset "
                  "to be inserted.")
        ),
        make_option('--srid', '--default-srid',
            dest='srid',
            default=None,
            help=("Optional. SRID (EPSG code) of the dataset if it cannot be "
                  "determined automatically.")
        ),
        make_option('--size', '--default-size',
            dest='size',
            action="callback", callback=StringFormatCallback(_size),
            default=None,
            help=("Optional. Dataset pixel size if it cannot be determined " 
                  "automatically. Format: <nrows>,<ncols>")
        ),
        make_option('--extent', '--default-extent',
            dest='extent',
            action="callback", callback=StringFormatCallback(_extent),
            default=None,
            help=("Optional. Dataset extent if it cannot be determined " 
                  "automatically. Format: <minx>,<miny>,<maxx>,<maxy>")
        ),
        make_option('--begin-time', '--default-begin-time',
            dest='begin_time',
            action="callback", callback=StringFormatCallback(getDateTime),

            default=None,
            help=("Optional. Acquisition begin timestamp if not available "
                  "from the EO metadata in ISO-8601 format.")
        ),
        make_option('--end-time', '--default-end-time',
            dest='end_time',
            action="callback", callback=StringFormatCallback(getDateTime),
            default=None,
            help=("Optional. Acquisition end timestamp if not available "
                  "from the EO metadata in ISO-8601 format.")
        ),
        make_option('--footprint', '--default-footprint',
            dest='footprint',
            action="callback", callback=StringFormatCallback(_footprint),
            default=None,
            help=("Optional. Footprint of the dataset if not available " 
                  "from the EO metadata in WKT format.")
        ),
        make_option('--visible',
            dest='visible',
            action="store_true",
            default=True,
            help=("Optional. It enables the visibility flag for all datasets "
                  "being registered. (Visibility enabled by default)")
        ),
        make_option('--invisible','--hidden',
            dest='visible',
            action="store_false",
            help=("Optional. It disables the visibility flag for all datasets "
                  "being registered. (Visibility enabled by default)")
        ),

        make_option('--ref','--referenceable', 
            dest='is_ref_ds',
            action="store_true",
            help=("Optional. It indicates that the created dataset is "
                  "a Referenceable dataset. (Relevanat only for manually "
                  "specified geo-meta-data. Ignored for automatically detected"
                  " local datasets)")
        ),
        make_option('--rect','--rectified', 
            dest='is_ref_ds',
            action="store_false",
            default=False,
            help=("Optional. Default. It indicates that the created dataset is"
                  " a Rectified dataset. (Relevanat only for manually "
                  "specified geo-meta-data. Ignored for automatically detected"
                  " local datasets)")
        ),

    )
    
    help = (
    """
    Registers one or more datasets from each data and meta-data file.
    
    Examples:
    Using shell expansion of filenames and automatic metadata retrieval:
        python manage.py %(name)s \\ 
            --data-files data/meris/mosaic_MER_FRS_1P_RGB_reduced/*.tif \\
            --range-type RGB --dataset-series MER_FRS_1P_RGB_reduced \\
            --stitched-mosaic mosaic_MER_FRS_1P_RGB_reduced -v3
    
    Manual selection of data/metadata files:
        python manage.py %(name)s \\
            --data-files 1.tif 2.tif 3.tif \\
            --metadata-files 1.xml 2.xml 3.xml \\
            --ids a b c --range-type RGB -v3
            
    Registering a rasdaman coverage:
        python manage.py %(name)s \\
            --source-type=rasdaman --host=some.host.com --port=8080 \\
            --user=db_user --password=secret \\
            --collection MER_FRS_1PNPDE..._reduced \\
            --srid=4326 --size=539,448 \\ 
            --extent=11.361066,32.201446,28.283846,46.252026 \\
            --begin-time "`date -u --iso-8601=seconds`" \\
            --end-time "`date -u --iso-8601=seconds`" \\
            --footprint "POLYGON ((11.3610659999999992 
                32.2014459999999971, 11.3610659999999992 
                46.2520260000000007, 28.2838460000000005 
                46.2520260000000007, 28.2838460000000005  
                32.2014459999999971, 11.3610659999999992 
                32.2014459999999971))" \\
            --id MER_FRS_1PNPDE..._reduced --range-type RGB -v3
    """ % ({"name": __name__.split(".")[-1]})
    )
    args = '--data-file <file-name> --range-type <range-type>'

    #--------------------------------------------------------------------------

    def _error( self , ds , msg ): 
        self.print_err( "Failed to register dataset '%s'!"
                        " Reason: %s"%( ds, msg ) ) 

    #--------------------------------------------------------------------------

    def handle(self, *args, **opt):

        System.init()

        # prepare dataset managers 
    
        dsMngr = { 
            "RectifiedDataset" : getRectifiedDatasetManager() ,
            "ReferenceableDataset" : getReferenceableDatasetManager() } 

        dsMngr_mosaic = getRectifiedStitchedMosaicManager() 
        dsMngr_series = getDatasetSeriesManager() 

        #-----------------------------------------------------------------------
        # extract some of the inputs 

        self.verbosity = int(opt.get('verbosity', 1))
        self.traceback = bool( opt.get("traceback", False) ) 

        src_data = opt.get('datafiles',[])
        src_meta = opt.get('metadatafiles',[])
        src_ids  = opt.get('ids',[])

        range_type = opt.get('rangetype',None)

        source_type = opt.get('source_type','local')

        visibility = opt.get("visible", True )

        ids_mosaic = list( set( opt["ids_mosaic"] ) ) 
        ids_series = list( set( opt["ids_series"] ) ) 

        ids_cont   = ids_mosaic + ids_series # merged containers 

        _has_explicit_md = any([ ( opt[i] is not None ) for i in
              ('size','extent','begin_time','end_time','footprint') ])

        # ... the rest of the options stays in the ``opt`` dictionary 

        #-----------------------------------------------------------------------
        # check the required inputs 

        if not src_data : 
            raise CommandError( "Missing specification of the data to be "
                "registered!") 

        if not range_type :
            raise CommandError( "Missing the mandatory range type"
                " specification." ) 

        if src_meta and ( len(src_meta) != len(src_data) ) : 
            raise CommandError( "The number of metadata files does not match"
                " the number of input data items!" ) 

        if src_ids and ( len(src_ids) != len(src_data) ) :
            raise CommandError( "The number of IDs does not match "
                " the number of input data items!" ) 

        if source_type == "rasdaman" : 

            if opt['oids'] and ( len(opt['oids']) != len(src_data) ) : 
                raise CommandError("The number of Rasdaman OIDs does not match"
                    " the number of input data items!" ) 

            if ( len(src_data) > len(src_ids) ) : 
                raise CommandError("Rasdaman datasets require explicite "
                    "specification of coverage/EO-IDs !")

            if ( len(src_data) > len(src_meta) ) and \
                ( ( len(src_data) > 1 ) or ( not _has_explicit_md ) ) : 
                raise CommandError("Rasdaman datasets require explicite "
                    "specification of metadata stored in files or passed "
                    "as commandline arguments!")
        else: 

            if opt['oids'] : 
                raise CommandError( "The Rasdaman OIDs are not expected to be"
                    " provided for %s data source!"%source_type ) 
          
            if opt['rasdb'] : 
                raise CommandError( "The Rasdaman DB is not expected to be"
                    " provided for %s data source!"%source_type ) 

        if source_type != "local" : 

            if not opt['host'] : 
                raise CommandError( "The host must be specified for non-local"
                    " data sources!" ) 

            if (opt['port'] is not None) and \
                        ((opt['port']<1) or (opt['port']>65535)) : 
                raise CommandError("Invalid port number! port=%d"%opt['port']) 

        #-----------------------------------------------------------------------
        # check that metadata specified via the CLI 
        # note that these can be set for one DS only 

        if ( 1 < len(src_data) ) and _has_explicit_md : 
            raise CommandError( "Specification of meta-data via the CLI is "
                    "allowed for single dataset only!" )  

        if ( opt["size"] is None ) != ( opt["extent"] is None ) : 
            raise CommandError( "Both 'size' and 'extent' metadata must be "
                    "specified but only one of them is actually provided!" ) 

        if ( opt["extent"] is not None ) and ( opt["srid"] is None ) : 
            raise CommandError( "The 'extent' metadata require SRID to be "
                    "specified!" )

        if ( opt["begin_time"] is None ) != ( opt["end_time"] is None ) :
            raise CommandError( "Both 'begin_time' and 'end_time' metadata "
                "must be specified but only one of them is actually provided!") 

        #-----------------------------------------------------------------------
        # handle the user specified geo-meta-data 

        if ( opt["extent"] is not None ) : 

            geo_metadata = GeospatialMetadata( opt["srid"], opt["size"][0],
                opt["size"][1], opt["extent"] , opt["is_ref_ds"] )

        else : 

            geo_metadata = None 

        #-----------------------------------------------------------------------
        # handle the user specified EO-meta-data 

        if (opt['begin_time'] is not None) and (opt['end_time'] is not None): 

            footprint = opt['footprint']
    
            # try to extract the missing footprint 
            if footprint is None : 

                # try to extract missing geo-metadata for local file  
                if source_type == "local" : 

                    # read the geo-metada if not given manually 
                    if geo_metadata is None : 

                        geo_metadata = _extract_geo_md(src_data[0],opt["srid"])

                    # if some geo-metadata are given we try to get the FP
                    if geo_metadata is not None : 
                    
                        # referenceable DS - trying to extract FP from GCPs 
                        if geo_metadata.is_referenceable : 
 
                            rt_prm = rt.suggest_transformer(src_data[0]) 
                            fp_wkt = rt.get_footprint_wkt(src_data[0],**rt_prm)
                            footprint = GEOSGeometry( fp_wkt ) 

                        # for referenceable DSs we extract footprint from extent 
                        else : 
                        
                            footprint = Polygon.from_bbox(geo_metadata.extent) 

                else : # remote data 
                
                    # we rely on the manually given extent for rectified DSs
                    if ( geo_metadata is not None ) and \
                            ( not geo_metadata.is_referenceable ) : 

                        footprint = Polygon.from_bbox( geo_metadata.extent ) 


            # raise an error if the footprint extraction failed
            if footprint is None : 

                raise CommandError( "Cannot extract 'footprint' from the "
                    "dataset. It must be set explicitely via CLI!" ) 

            # create EOMetadata object 
        
            eo_metadata = EOMetadata( src_ids[0], opt["begin_time"], 
                            opt["end_time"], opt["footprint"], None )   

        else : 

            eo_metadata = None 

        #-----------------------------------------------------------------------
        # create the automatic IDs, filenames, and OIDs   

        def __make_id( src ) : 
            return os.path.splitext( os.path.basename( src ) )[0] 

        def __make_md( src ) : 
            fname = "%s.xml"%os.path.splitext( src )[0]
            if not os.path.exists( fname ) : 
                fname = src 
            return fname 

        if not src_ids : 
            src_ids = [ __make_id(fn) for fn in src_data ] 

        if not src_meta : 
            src_meta = [ __make_md(fn) for fn in src_data ] 

        if ( source_type == "rasdaman" ) and not opt['oids'] : 
            opt['oids'] = [ None for i in xrange(len(src_data)) ]

        #-----------------------------------------------------------------------
        # verify the identifiers agaist the DB 

        # range-type 

        if not isRangeTypeName( range_type ) : 
            raise CommandError( "Invalid range-type identifier '%s' !" \
                        % range_type )

        # check rectified stitched mosaics 

        for mosaic in ids_mosaic : 
            if not dsMngr_mosaic.check_id( mosaic ) :
                raise CommandError( "Invalid Rectified Stitched Mosaic "
                        "identifier '%s' !" % mosaic )

        # check datasets series 

        for series in ids_series : 
            if not dsMngr_series.check_id( series ) :
                raise CommandError( "Invalid Dataset Series identifier " 
                        "'%s' !" % series )

        #-----------------------------------------------------------------------
        # debug print 

        self.print_msg("Range type:  %s"%(range_type),2)
        self.print_msg("Visibility:  %s"%(["HIDDEN","VISIBLE"][visibility]),2)
        self.print_msg("Data IDs:    %s"%(" ".join(src_ids)),2)
        self.print_msg("Source data: %s"%(" ".join(src_data)),2)
        self.print_msg("Metadata:    %s"%(" ".join(src_meta)),2)
        self.print_msg("Mosaics:     %s"%(" ".join(ids_mosaic)),2)
        self.print_msg("Series:      %s"%(" ".join(ids_series)),2)

        if source_type == "rasdaman" : 
            self.print_msg("Rasd. OIDs:  %s"%(" ".join(opt["oids"])),2)
            self.print_msg("Rasd. DB:    %s"%( opt["rasdb"] ),2)

        self.print_msg("Source type: %s"%(source_type),2)

        if source_type != "local" : 
            self.print_msg("- host:    %s"%(opt["host"]),2)
            self.print_msg("- port:    %s"%(opt["port"]),2)
            self.print_msg("- user:    %s"%(opt["user"]),2)
            self.print_msg("- passwd:  %s"%(opt["password"]),2)

        self.print_msg("CLI metadata:",2) 
            
        for i in ('srid','size','extent','begin_time','end_time','footprint'):
            self.print_msg("- %-8s\t%s" % ( "%s:"%i , opt[i] ) , 2 ) 

        #-----------------------------------------------------------------------
        # register the idividual datasets 

        success_count = 0 # count successfull actions 

        for df, mdf, cid in zip( src_data, src_meta, src_ids ) :

            self.print_msg( "Registering dataset: '%s'" % cid ) 
            
            # store geo-metadata in a local variable 
            _geo_metadata = geo_metadata

            # commmon parameters 

            prm = {} 

            prm["obj_id"]           = cid
            prm["range_type_name"]  = range_type
            prm["default_srid"]     = opt["srid"]
            prm["container_ids"]    = ids_cont
            prm["visible"]          = opt["visible"] 

            # source specific parameters 

            if source_type == "local" :

                prm["local_path"]     = df 
                prm["md_local_path"]  = mdf 

                # try to extract geo-metadata
                # NOTE: The geo-metadata can be extracted from local data only!
                if _geo_metadata is None : 
                    try:
                        _geo_metadata = _extract_geo_md( df, opt["srid"] )
                    except Exception as e:
                        # print stack trace if required 
                        if self.traceback : 
                            self.print_msg(traceback.format_exc())

                        self._error( cid, "%s: %s"%(type(e).__name__, str(e)) )

                        continue # continue by next dataset 
            
            elif source_type == "ftp" :

                prm["remote_path"]    = df
                prm["md_remote_path"] = mdf
                prm["ftp_host"]       = opt["host"]
                prm["ftp_port"]       = opt["port"]
                prm["ftp_user"]       = opt["user"]
                prm["ftp_passwd"]     = opt["password"]

            elif source_type == "rasdaman" :

                prm["collection"]     = df,
                prm["md_local_path"]  = mdf,
                prm["oid"]            = opt["oids"].pop(0)  
                prm["ras_host"]       = opt["host"]
                prm["ras_port"]       = opt["port"]
                prm["ras_user"]       = opt["user"]
                prm["ras_passwd"]     = opt["password"]
                prm["ras_db"]         = opt["rasdb"]

            #-------------------------------------------------------------------
            # insert metadata if available 

            if eo_metadata is not None:
                prm["eo_metadata"] = eo_metadata

            if _geo_metadata is not None:
                prm["geo_metadata"] = _geo_metadata

            #-------------------------------------------------------------------
            # select dataset manager  

            # TODO: Fix the ReferenceableDataset selection! 
            # What will happen in case of rectified DS and _geo_metadata being None

            # unless changed we assume rectified DS 
            dsType = "RectifiedDataset"
            
            if (_geo_metadata is not None) and _geo_metadata.is_referenceable :

                # the DS is refereanceable  
                dsType = "ReferenceableDataset"

            #-------------------------------------------------------------------
            # perform the actual dataset registration 
                
            try:

                with transaction.commit_on_success():
                    self.print_msg( "Creating new dataset ...",2) 
                    dsMngr[dsType].create( **prm ) 

            except Exception as e: 

                # print stack trace if required 
                if self.traceback : 
                    self.print_msg(traceback.format_exc())

                self._error( cid, "%s: %s"%(type(e).__name__, str(e)) )

                continue # continue by next dataset 

            success_count += 1 #increment the success counter  
            self.print_msg( "Dataset successfully registered.",2) 


        #-----------------------------------------------------------------------
        # print the final info 
        
        count = len(src_data) 
        error_count = count - success_count

        if ( error_count > 0 ) : 
            self.print_msg( "Failed to register %d dataset%s." % (
                error_count , ("","s")[error_count!=1] ) , 1 )  

        if ( success_count > 0 ) : 
            self.print_msg( "Successfully registered %d of %s dataset%s." % (
                success_count , count , ("","s")[count!=1] ) , 1 )
        else : 
            self.print_msg( "No dataset registered." ) 

        if ( error_count > 0 ) : 
            raise CommandError("Not all datasets could be registered.")
