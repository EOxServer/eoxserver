
from itertools import chain

from eoxserver.core import Component, env, implements
from eoxserver.core.decoders import kvp, typelist, InvalidParameterException
from eoxserver.resources.coverages import models
from eoxserver.services.component import MapServerComponent
from eoxserver.services.subset import Subsets, Trim, Slice
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, OWSGetServiceHandlerInterface
)

class WMS13GetMapHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)


    service = "WMS"
    versions = ("1.3.0", "1.3")
    request = "GetMap"

    def handle(self, request):
        ms_component = MapServerComponent(env)
        decoder = WMS13GetMapDecoder(request.GET)

        bbox = decoder.bbox
        time = decoder.time
        crs = decoder.crs
        layers = decoder.layers

        if len(layers) == 0:
            raise "No layers specified"

        # TODO: if crs has not swapped axes
        minx, miny, maxx, maxy = bbox

        subsets = Subsets((
            Trim("x", minx, maxx, crs),
            Trim("y", miny, maxy, crs),
        ))
        if time: subsets.append(time)
        
        suffixes = set(map(lambda s: s.suffix, ms_component.layer_factories))
        suffix_related_ids = {}

        root_group = LayerGroup(None)

        for layer_name in layers:
            for suffix in chain((None,), suffixes):
                if not suffix:
                    identifier = layer_name
                else:
                    identifier = layer_name[:-len(suffix)]

                
                # TODO: nasty, nasty bug... dunno where
                eo_objects = models.EOObject.objects.filter(
                    identifier=identifier
                )
                if len(eo_objects):
                    eo_object = eo_objects[0]
                    break
            else:
                raise InvalidParameterException(
                    "No such layer %s" % layer_name, "layers"
                )

            if models.iscollection(eo_object):
                # recursively iterate over all sub-collections and collect all
                # coverages

                used_ids = suffix_related_ids.setdefault(suffix, set())

                def recursive_lookup(collection, suffix, used_ids, subsets):
                    # get all EO objects related to this collection, excluding 
                    # those already searched
                    eo_objects = models.EOObject.objects.filter(
                        collections__in=[collection.pk]
                    ).exclude(
                        pk__in=used_ids
                    ).order_by("begin_time", "end_time")
                    # apply subsets
                    eo_objects = subsets.filter(eo_objects)

                    group = LayerGroup(collection.identifier)

                    # append all retrived EO objects, either as a coverage of 
                    # the real type, or as a subgroup.
                    for eo_object in eo_objects:
                        used_ids.add(eo_object.pk)

                        if models.iscoverage(eo_object):
                            group.append((eo_object.cast(), suffix))
                        elif models.iscollection(eo_object):
                            group.append(recursive_lookup(
                                eo_object, suffix, used_ids, subsets
                            ))
                        else: 
                            raise "Type '%s' is neither a collection, nor a coverage."

                    return group

                root_group.append(
                    recursive_lookup(eo_object, suffix, used_ids, subsets)
                )

            elif models.iscoverage(eo_object):
                # TODO: suffix
                root_group.append((eo_object.cast(), suffix))

        # TODO: make this dependant on the plugin
        from eoxserver.services.ows.wms.renderer import WMSMapRenderer
        renderer = WMSMapRenderer()
        return renderer.render(
            root_group, request.GET.items(), 
            time=decoder.time, bands=decoder.dim_bands
        )


class LayerGroup(list):
    def __init__(self, name, iterable=None):
        self.name = name
        if iterable:
            super(LayerGroup, self).__init__(iterable)


    def __contains__(self, eo_object):
        for item in self:
            if eo_object == item:
                return True
            try:
                if eo_object in item:
                    return True
            except TypeError:
                pass


    def walk(self, breadth_first=True):
        for item in self:
            try:
                for names, suffix, eo_object in item.walk():
                    yield (self.name,) + names, suffix, eo_object
            except AttributeError:
                yield (self.name,), item[1], item[0]


def parse_bbox(string):
    try:
        return map(float, string.split(","))
    except ValueError:
        raise InvalidParameterException("Invalid BBOX parameter.", "bbox")


def parse_time(string):
    pass # TODO: implement


class WMS13GetMapDecoder(kvp.Decoder):
    layers = kvp.Parameter(type=typelist(str, ","), num=1)
    styles = kvp.Parameter(num="?")
    bbox   = kvp.Parameter(type=parse_bbox, num=1)
    time   = kvp.Parameter(type=parse_time, num="?")
    crs    = kvp.Parameter(num=1)
    width  = kvp.Parameter(num=1)
    height = kvp.Parameter(num=1)
    format = kvp.Parameter(num=1)
    dim_bands = kvp.Parameter(num="?")


