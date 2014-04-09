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

from eoxserver.resources.coverages.dateline import (
    extent_crosses_dateline, wrap_extent_around_dateline
)

from eoxserver.services.mapserver.wms.layers.base import (
    LayerFactory, GroupLayerMixIn, DataLayerMixIn,
    PolygonMaskingLayerMixIn,
)

import random 

#-------------------------------------------------------------------------------

class CoverageDataLayerFactory(LayerFactory,GroupLayerMixIn,DataLayerMixIn,
                                     PolygonMaskingLayerMixIn): 
    """ basic data layer factory """ 


    def _mask_geom( self, cov ):
        return None 


    def generate(self): 

        def _get_bands(cov):  
            return cov.data_items.filter(semantic__startswith="bands")

        group = self.group if self.is_groupped else None 

        # create the group layer 
        if group: 
            yield self._group_layer(group), None, () 

        # iterate over the coverages 
        for cov, cov_name in self.coverages : 

            layer_group = "/"+group if group else ""

            # NOTE: In order to assure proper rendering of the nested layers
            #       a unique name has to be assigned to each of them. They
            #       will never be addressed by their true name.
            #       The top-level coverages must preserve their true identity
            #       though because they are requested in the WMS query. 
            base_name = cov_name if not group else \
                        "%s_%s_%08x"%(group,cov_name,random.randrange(16**8))

            # band indices 
            indices = self._indeces( cov, self.options )
        
            # get the data items 
            data_items = _get_bands(cov)

            #=================================================================
            # prepare mask layer(s)

            # get mask geometry 
            mask_geom = self._mask_geom( cov )

            if mask_geom and (not mask_geom.empty ) : 
                
                # prepare the mask polygon layer 

                mask_name  = "%s%s__mask__"%( base_name , self.suffix ) 
                layer = self._polygon_masking_layer(cov,mask_name,
                                            mask_geom,layer_group)

                yield layer, None, None

            else : 

                mask_name = None 

            #=================================================================
            # prepare data layers 

            if not extent_crosses_dateline(cov.extent,cov.srid):

                name  = "%s%s"%( base_name , self.suffix ) 
                layer = self._data_layer( cov, name, cov.extent, layer_group, 
                                            mask=mask_name, indices=indices )
                yield layer, cov, data_items

            else : # image crosses the date-line 

                # create group layer 
                name  = "%s%s"%( base_name , self.suffix ) 
                yield self._group_layer(cov.identifier,layer_group),None,() 

                layer_subgroup= "%s/%s%s"%(layer_group,name,self.suffix)

                # layer with the original extent 
                name   = "%s_1%s"%( base_name , self.suffix )
                extent = cov.extent
                layer  = self._data_layer( cov, name, extent, layer_subgroup,
                            wrapped=False, mask=mask_name, indices=indices )
                yield layer, cov, data_items
                   
                # TODO: check masking for date-line crossing products
                # create additional layer with +/-360dg latitude offset 
                name   = "%s_2%s"%( base_name , self.suffix )
                extent = wrap_extent_around_dateline( cov.extent, cov.srid )
                layer  = self._data_layer( cov, name, extent, layer_subgroup,
                            wrapped=True, mask=mask_name, indices=indices )
                yield layer, cov, data_items
