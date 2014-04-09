#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from eoxserver.resources.coverages import models
from eoxserver.core.decoders import InvalidParameterException
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.services.subset import Trim, Slice
from eoxserver.services.ows.wms.exceptions import LayerNotDefined

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------

def parse_bbox(string):
    try:
        bbox = map(float, string.split(","))
    except ValueError:
        raise InvalidParameterException("Invalid 'BBOX' parameter.", "bbox")

    try:
        minx, miny, maxx, maxy = bbox
    except ValueError:
        raise InvalidParameterException(
            "Wrong number of arguments for 'BBOX' parameter.", "bbox"
        )

    return bbox


def parse_time(string):
    items = string.split("/")

    if len(items) == 1:
        return Slice("t", parse_iso8601(items[0]))
    elif len(items) in (2, 3):
        # ignore resolution
        return Trim("t", parse_iso8601(items[0]), parse_iso8601(items[1]))

    raise InvalidParameterException("Invalid TIME parameter.", "time")


def int_or_str(string):
    try:
        return int(string)
    except ValueError:
        return string

#-------------------------------------------------------------------------------

def lookup_layers(layers, subsets, suffixes=None):
    """ Performs a layer lookup for the given layer names. Applies the given 
        subsets and looks up all layers with the given suffixes. Returns a 
        list of ``LayerSelection`` objects. 
    """

    suffixes = suffixes or (None,)
    logger.debug("Tested suffixes: %s"%str(suffixes))

    # ------------------------------------------------------------------------
    # local closures: 

    def _lookup_eoobject( layer_name ): 
        """ Search an EOObject matching the given layer name. """ 

        for suffix in suffixes:

            if not suffix: # suffix is None or an empty string 
                identifier = layer_name

            elif layer_name.endswith(suffix): # suffix matches the layer name
                identifier = layer_name[:-len(suffix)]

            else: # no match found 
                continue

            # get an EO Object matching the identifier 
            eo_objects = list(models.EOObject.objects.filter(identifier=identifier))

            # if a match is found get the object and terminate the search loop 
            if len(eo_objects) > 0 : 
                return eo_objects[0] , suffix 

        raise InvalidParameterException(
            "No such layer %s" % layer_name, "layers"
        )

    # ---------------------------------

    def _get_wms_view( eo_object ): 
        """ Get an EOObject used for the WMS view. If there is no WMS view 
            object the closure returns the input object. 
        """ 

        # check whether the layer has a wms_view meta-data item  
        try: 
            md_item = eo_object.metadata_items.get(semantic="wms_view") 
            return models.EOObject.objects.get(identifier=md_item.value)

        except models.MetadataItem.DoesNotExist : # no wms_view available 
            # use the existing eo_object
            return eo_object

        except models.EOObject.DoesNotExist : # wms_view is invalid 
            # use the existing eo_object 
            return eo_object

    # ---------------------------------

    def _get_alias( eo_object ):  
        """ Get an EOObject alias, i.e., an identifier of the EOObject
            the given EOOobject provides the WMS view to. 
        """ 
        try: 
            
            return eo_object.metadata_items.get(semantic="wms_alias").value

        except models.MetadataItem.DoesNotExist : # wms_view is invalid 
            # use the existing eo_object 
            return None 
        
    # ---------------------------------

    def _recursive_lookup( collection ): 
        """ Search recursively through the nested collections 
            and find the relevant EOObjects."""

        # get all objects held by this collection
        eo_objects = models.EOObject.objects\
            .filter( collections__in=[collection.pk] )\
            .exclude( pk__in=used_ids )\
            .order_by("begin_time", "end_time", "identifier")\
            .prefetch_related('metadata_items')

        # apply the subset filtering 
        eo_objects = subsets.filter( eo_objects )

        # iterate over the remaining EOObjects 
        for eo_object in eo_objects:

            used_ids.add( eo_object.pk )

            if models.iscoverage( eo_object ):
                selection.append( eo_object.cast(), _get_alias(eo_object) )

            elif models.iscollection( eo_object ):
                _recursive_lookup( eo_object )

            else:
                pass # TODO: Reporting of invalid EOObjects (?) 


    # ------------------------------------------------------------------------

    selections = []  

    # NOTE: The lookup is performed on a set of unique layer names. This has
    #       no effect on the rendering order of the layer as this is determined
    #       by the WMS request handled by the mapserver.

    for layer_name in set(layers):
    
        # get an EOObject and suffix matching the layer_name 
        eoo_src, suffix = _lookup_eoobject( layer_name )
    
        # get EOObject holding the WMS view 
        eoo_wms = _get_wms_view( eoo_src )

        # prepare the final EOObject(s) selection
        selection = LayerSelection( eoo_src, suffix ) 

        if models.iscoverage( eoo_wms ):
            # EOObject is a coverage 

            # append to selection if matches the subset
            if subsets.matches( eoo_wms ):
                selection.append( eoo_wms.cast(), eoo_src.identifier )
                
        elif models.iscollection( eoo_wms ):
            # EOObject is a collection (but not a coverage) 

            # recursively look-up the coverages 
            used_ids = set() 

            _recursive_lookup( eoo_wms )

        else : 
            pass # TODO: Reporting of invalid EOObjects (?) 

        selections.append( selection ) 

    return selections 

#-------------------------------------------------------------------------------

class LayerSelection(tuple): 
    """ helper class holding the selection of EOObject 
        to be used for rendering of a WMS layer
    """

    def __new__(cls, root, suffix ):
        """ Construct the object. Parameters:

                root    - requested EOObject (layer)
                suffix  - layer name suffix 
        """
            
        return super(LayerSelection,cls)\
                    .__new__(cls,(root,suffix,[]))

    @property 
    def root(self): 
        "The root EOObject corresponding the requested layer name."
        return self[0]

    @property
    def suffix(self): 
        "The layer name suffix of this layer selection."
        return self[1]

    @property
    def identifier(self): 
        "The layer base name (EOObject identifier) of this selection."
        return self.root.identifier 

    @property
    def layer_name(self):
        "The requested layer name of this layer selection." 
        return self.identifier + ( self.suffix or "" ) 

    @property 
    def coverages(self): 
        "The list of selected coveraged to be used for rendering of the layer."
        return self[2]

    def append(self, rendered, alias=None):
        """ Append a selected EOObjected needed by the layer.  
            In case the actual rendered object has an alias 
            (i.e., represents view for another object) this alias 
            can be passed as the second parameters. 
        """

        self[2].append( ( rendered, (alias or rendered.identifier) ) ) 
