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
    LayerFactory, GroupLayerMixIn, DataLayerMixIn
)

from eoxserver.contrib import mapserver as ms

#-------------------------------------------------------------------------------

class CoverageDataMaskedLayerFactory(LayerFactory,GroupLayerMixIn,DataLayerMixIn): 

    # layer creating method 
    def _polygon_masking_layer(self,name,group=None): 

        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_POLYGON

        layer.setMetaData("eoxs_geometry_reversed", "true")

        if group: 
            layer.setMetaData("wms_layer_group", group) 

        cls = ms.classObj(layer)
        style = ms.styleObj(cls)
        style.color.setRGB(0, 0, 0)

        return layer


    def generate(self): 

        def _get_bands(cov):  
            return cov.data_items.filter(semantic__startswith="bands")

        def _get_masks(cov):  
            return cov.data_items.filter(semantic__startswith="polygonmask")

        # create the group layers 
        for group in self.groups : 
            yield self._group_layer(group), None, () 

        # iterate over the coverages 
        for cov, group, cols in self.coverages : 

            layer_group = "/"+group if group else ""

            # band indices 
            indices = self._indeces( cov, self.options )
        
            # get the data items 
            data_items = _get_bands(cov)
            mask_items = _get_masks(cov)  

            # MP: Not clear why we are doing this.
            cov.cached_data_items = cov.data_items.all()
            
            #=================================================================
            # prepare mask layer(s)

            # multiple masks shall be grouped by a group layer
            if len(mask_items) > 1:
            #if True : 

                # TODO fix the multi-masks 

                # more than one mask, requires a mask group layer
                mask = "%s%s__mask__"%( cov.identifier , self.suffix ) 
                layer = self._group_layer(mask,layer_group)
                layer.setMetaData("eoxs_geometry_reversed", "true")
                yield layer, None, () 

                layer_subgroup= "%s/%s"%(layer_group,mask)

                # generate mask layers
                for i, mask_item in enumerate(mask_items):

                    name = "%s_%d"%( mask , i ) 
                    layer = self._polygon_masking_layer(name,layer_subgroup)
                    yield layer, cov, (mask_item,) 


            # single mask shall be used directly as a "group" layer 
            elif len(mask_items) == 1 :

                mask  = "%s%s__mask__"%( cov.identifier , self.suffix ) 
                layer = self._polygon_masking_layer(mask,layer_group)

                yield layer, cov, (mask_items[0],)


            # no mask at all 
            else: 

                mask = None

            #=================================================================
            # prepare data layers 

            if not extent_crosses_dateline(cov.extent,cov.srid):

                name  = "%s%s"%( cov.identifier , self.suffix ) 
                layer = self._data_layer( cov, name, cov.extent, layer_group, 
                                            mask=mask, indices=indices )
                yield layer, cov, data_items

            else : # image crosses the date-line 

                # create group layer 
                name  = "%s%s"%( cov.identifier , self.suffix ) 
                yield self._group_layer(cov.identifier,layer_group),None,() 

                layer_subgroup= "%s/%s%s"%(layer_group,name,self.suffix)

                # layer with the original extent 
                name   = "%s_1%s"%( cov.identifier , self.suffix )
                extent = cov.extent
                layer  = self._data_layer( cov, name, extent, layer_subgroup,
                                   wrapped=False, mask=mask, indices=indices )
                yield layer, cov, data_items
                   
                # TODO: check masking for date-line crossing products
                # create additional layer with +/-360dg latitude offset 
                name   = "%s_2%s"%( cov.identifier , self.suffix )
                extent = wrap_extent_around_dateline( cov.extent, cov.srid )
                layer  = self._data_layer( cov, name, extent, layer_subgroup,
                                   wrapped=True, mask=mask, indices=indices )
                yield layer, cov, data_items
