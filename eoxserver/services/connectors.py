#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

"""
Connectors are used to configure the data sources for MapServer requests.
Because of the different nature of the data sources (files, tile indices,
rasdaman databases) they have to be set up differently. Connectors allow to
do this transparently.
"""

import os.path

from eoxserver.contrib import osr
from eoxserver.services.mapserver import MapServerDataConnectorInterface
from eoxserver.resources.coverages import crss  


class FileConnector(object):
    """
    The :class:`FileConnector` class is the most common connector. It
    configures a file as data source for the MapServer request.
    """
    REGISTRY_CONF = {
        "name": "Local File Connector",
        "impl_id": "services.connectors.LocalFileConnector", # TODO: change this to FileConnector
        "registry_values": {
            "services.mapserver.data_structure_type": "file",
        }
    }
    
    def configure(self, layer, eo_object, filter_exprs = None):
        """
        This method takes three arguments: ``layer`` is a MapServer
        :class:`layerObj` instance, ``eo_object`` a EO-WCS object (either
        a :class:`~.RectifiedDatasetWrapper` or
        :class:`~.RectifiedStitchedMosaicWrapper` instance) and the optional
        ``filter_exprs`` argument is currently not used.
        
        The method configures the MapServer layer by setting its ``data``
        property to the path. It invokes the
        :meth:`~.DataPackageWrapper.prepareData` method of the
        :class:`~.DataPackageWrapper` instance related to the object.
        
        The method also sets the projection on the layer.
        """
        data_package = eo_object.getData()
        data_package.prepareAccess()
        
        layer.data = data_package.getGDALDatasetIdentifier()

        # set layer's projection 
        layer.setProjection( crss.asProj4Str( eo_object.getSRID() ))
        
        return layer

FileConnectorImplementation = \
MapServerDataConnectorInterface.implement(FileConnector)

class TiledPackageConnector(object):
    """
    The :class:`TiledPackageConnector` class is intended for
    :class:`~.RectifiedStitchedMosaicWrapper` instances that store their
    data in tile indices.
    """
    REGISTRY_CONF = {
        "name": "Tiled Package Connector",
        "impl_id": "services.connectors.TiledPackageConnector",
        "registry_values": {
            "services.mapserver.data_structure_type": "index"
        }
    }
    
    def configure(self, layer, eo_object, filter_exprs = None):
        """
        This method takes three arguments: ``layer`` is a MapServer
        :class:`layerObj` instance, ``eo_object`` a 
        :class:`~.RectifiedStitchedMosaicWrapper` instance and the optional
        ``filter_exprs`` argument is currently not used.
        
        The method sets the ``tileindex`` property of the MapServer layer to
        point to the shape file where the paths of the tiles are stored.
        
        The method also sets the projection on the layer.
        """
        tile_index = eo_object.getData()
        path = tile_index.getShapeFilePath()
        
        layer.tileindex = os.path.abspath(path)
        layer.tileitem = "location"

        # set layer's projection 
        layer.setProjection( crss.asProj4Str( eo_object.getSRID() ))
        
        return layer

TiledPackageConnectorImplementation = \
MapServerDataConnectorInterface.implement(TiledPackageConnector)

class RasdamanArrayConnector(object):
    """
    The :class:`RasdamanArrayConnector` class is intended for
    :class:`~.RectifiedDatasetWrapper` instances that store their
    data in rasdaman arrays.
    """
    REGISTRY_CONF = {
        "name": "Rasdaman Array Connector",
        "impl_id": "services.connectors.RasdamanArrayConnector",
        "registry_values": {
            "services.mapserver.data_structure_type": "rasdaman_array"
        }
    }
    
    def configure(self, layer, eo_object, filter_exprs = None):
        """
        This method takes three arguments: ``layer`` is a MapServer
        :class:`layerObj` instance, ``eo_object`` a 
        :class:`~.RectifiedDatasetWrapper` instance and the optional
        ``filter_exprs`` argument is currently not used.
        
        The method sets the ``data`` property of the MapServer layer to the
        connection string to the rasdaman database array, see the `GDAL
        rasdaman format <http://http://www.gdal.org/frmt_rasdaman.html>`_
        page for details.
        
        Furthermore, the projection settings on the layer are configured
        according to the metadata in the EOxServer database. As the
        rasdaman arrays have pixel coordinates only, the parameters for
        conversion from pixel coordinates to the spatial reference system have
        to be set explicitly.
        """
        data_package = eo_object.getData()
        data_package.prepareAccess()
        
        layer.data = data_package.getGDALDatasetIdentifier()
        
        #---------------------------------------------------------------
        # define custom coordinate system
        #---------------------------------------------------------------
        
        srid = eo_object.getSRID()
        
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(srid)

        minx, miny, maxx, maxy = eo_object.getExtent()
        size_x, size_y = eo_object.getSize()
        
        false_northing = srs.GetProjParm("false_northing")
        false_easting = srs.GetProjParm("false_easting")
        x_0 = false_easting + minx
        y_0 = false_northing + miny
        to_unit = (maxx - minx) / float(size_x)
        
        if srs.IsProjected():
            
            proj_str = "+init=epsg:%d +x_0=%f +y_0=%f +to_meters=%f" %\
                (srid, x_0, y_0, to_unit)
        else:
            proj_str = "+init=epsg:%d +x_0=%f +y_0=%f +to_degrees=%f" %\
                (srid, x_0, y_0, to_unit)
            
        layer.setProjection(proj_str)
        
        return layer

RasdamanArrayConnectorImplementation = \
MapServerDataConnectorInterface.implement(RasdamanArrayConnector)
