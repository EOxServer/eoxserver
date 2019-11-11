#-------------------------------------------------------------------------------
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
from eoxserver.services.subset import Trim, Slice
from eoxserver.services.ows.wms.exceptions import LayerNotDefined
from eoxserver.services.ows.wms.parsing import (parse_bbox, parse_time, int_or_str)


logger = logging.getLogger(__name__)


def lookup_layers(layers, subsets, suffixes=None):
    """ Performs a layer lookup for the given layer names. Applies the given
        subsets and looks up all layers with the given suffixes. Returns a
        hierarchy of ``LayerSelection`` objects.
    """
    suffix_related_ids = {}
    root_group = LayerSelection(None)
    suffixes = suffixes or (None,)
    logger.debug(str(suffixes))

    for layer_name in layers:
        for suffix in suffixes:
            if not suffix:
                identifier = layer_name
            elif layer_name.endswith(suffix):
                identifier = layer_name[:-len(suffix)]
            else:
                continue

            # TODO: nasty, nasty bug... dunno where
            eo_objects = models.EOObject.objects.filter(
                identifier=identifier
            )
            if len(eo_objects):
                eo_object = eo_objects[0]
                break
        else:
            raise LayerNotDefined(layer_name)

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

                selection = LayerSelection()

                # append all retrived EO objects, either as a coverage of
                # the real type, or as a subgroup.
                for eo_object in eo_objects:
                    used_ids.add(eo_object.pk)

                    if models.iscoverage(eo_object):
                        selection.append(eo_object.cast(), eo_object.identifier)
                    elif models.iscollection(eo_object):
                        selection.extend(recursive_lookup(
                            eo_object, suffix, used_ids, subsets
                        ))
                    else:
                        pass

                return selection

            root_group.append(
                LayerSelection(
                    eo_object, suffix,
                    recursive_lookup(eo_object, suffix, used_ids, subsets)
                )
            )

        elif models.iscoverage(eo_object):
            # Add a layer selection for the coverage with the suffix
            selection = LayerSelection(None, suffix=suffix)
            if subsets.matches(eo_object):
                selection.append(eo_object.cast(), eo_object.identifier)
            else:
                selection.append(None, eo_object.identifier)

            root_group.append(selection)

    return root_group


class LayerSelection(list):
    """ Helper class for hierarchical layer selections.
    """
    def __init__(self, collection=None, suffix=None, iterable=None):
        self.collection = collection
        self.suffix = suffix
        if iterable:
            super(LayerSelection, self).__init__(iterable)

    def __contains__(self, eo_object):
        for item in self:
            try:
                if eo_object in item:
                    return True
            except TypeError:
                pass

            try:
                if eo_object == item[0]:
                    return True
            except IndexError:
                pass

        return False

    def append(self, eo_object_or_selection, name=None):
        if isinstance(eo_object_or_selection, LayerSelection):
            super(LayerSelection, self).append(eo_object_or_selection)
        else:
            super(LayerSelection, self).append((eo_object_or_selection, name))

    def walk(self, depth_first=True):
        """ Yields four-tuples (collections, coverage, name, suffix).
        """

        collection = (self.collection,) if self.collection else ()

        for item in self:
            try:
                for collections, eo_object, name, suffix in item.walk():
                    yield (
                        collection + collections,
                        eo_object, name,
                        suffix or self.suffix
                    )

            except AttributeError:
                yield collection, item[0], item[1], self.suffix

        if not self:
            yield collection, None, None, self.suffix
