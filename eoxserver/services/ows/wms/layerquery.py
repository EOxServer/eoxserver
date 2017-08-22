# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from django.db.models import Q

from eoxserver.render.map.objects import (
    Map, CoverageLayer, OutlinesLayer, BrowseLayer, MaskLayer, MaskedBrowseLayer
)
from eoxserver.render.coverage.objects import Coverage as RenderCoverage
from eoxserver.render.browse.objects import (
    Browse, Mask, MaskedBrowse
)
from eoxserver.resources.coverages import models
from eoxserver.services.ecql import parse, to_filter, get_field_mapping_for_model
from eoxserver.services import filters


class NoSuchLayer(Exception):
    pass


class NoSuchPrefix(NoSuchLayer):
    pass


class LayerQuery(object):
    """
    """

    SUFFIX_SEPARATOR = "__"

    def create_map(self, layers, styles, bbox, crs, width, height, format,
                   bgcolor=None,
                   transparent=True, time=None,
                   range=None,
                   bands=None, wavelengths=None,
                   elevation=None, cql=None):

        if not styles:
            styles = [None] * len(layers)

        assert len(layers) == len(styles)

        filters_expressions = (
            filters.bbox(
                filters.attribute('footprint'),
                bbox[0], bbox[1], bbox[2], bbox[3], crs) &
            Q()
        )

        if cql:
            mapping, mapping_choices = get_field_mapping_for_model(
                models.Product
            )
            filters_expressions = filters_expressions & to_filter(parse(cql), )

        return Map(
            layers=[
                self.lookup_layer(
                    self.split_layer_suffix_name(layer)[0],
                    self.split_layer_suffix_name(layer)[1], style,
                    filters_expressions, time, range, bands, wavelengths, elevation
                ) for (layer, style) in zip(layers, styles)
            ],
            width=width, height=height, format=format, bbox=bbox, crs=crs,
            bgcolor=bgcolor,
            transparent=transparent, time=time, elevation=elevation
        )

    def lookup_layer(self, layer_name, suffix, style, filters_expressions,
                     time, range, bands, wavelengths, elevation):
        """ Lookup the layer from the registered objects.
        """
        full_name = '%s%s%s' % (layer_name, self.SUFFIX_SEPARATOR, suffix)

        try:
            eo_object = models.EOObject.objects.select_subclasses(
                models.Collection, models.Product, models.Coverage
            ).get(
                identifier=layer_name
            )
        except models.EOObject.DoesNotExist:
            raise NoSuchLayer('Layer %r does not exist' % layer_name)

        if isinstance(eo_object, models.Coverage):
            if suffix not in ('', 'bands'):
                raise NoSuchLayer('Invalid layer suffix %r' % suffix)
            return CoverageLayer(
                full_name, style,
                RenderCoverage.from_model(eo_object),
                bands, wavelengths, time, elevation, range
            )

        elif isinstance(eo_object, (models.Collection, models.Product)):
            if suffix == '':
                return BrowseLayer(
                    name=full_name, style=style,
                    browses=[
                        Browse.from_model(product, browse)
                        for product, browse in self.iter_products_browses(
                            eo_object, filters_expressions, suffix, style
                        )
                        if browse
                    ]
                )

            elif suffix == 'outlines':
                return OutlinesLayer(
                    name=full_name, style=style,
                    footprints=[
                        product.footprint for product in self.iter_products(
                            eo_object, filters_expressions
                        )
                    ]
                )

            elif suffix.startswith('masked_'):
                post_suffix = suffix[len('masked_'):]
                mask_type = self.get_mask_type(eo_object, post_suffix)

                if not mask_type:
                    raise NoSuchLayer('No such mask type %r' % post_suffix)
                return MaskedBrowseLayer(
                    name=full_name, style=style,
                    masked_browses=[
                        MaskedBrowse.from_models(product, browse, mask)
                        for product, browse, mask in
                        self.iter_products_browses_masks(
                            eo_object, filters_expressions, post_suffix
                        )
                    ]
                )

            else:
                # either browse type or mask type
                browse_type = self.get_browse_type(eo_object, suffix)
                if browse_type:
                    return BrowseLayer(
                        name=full_name, style=style,
                        browses=[
                            Browse.from_model(product, browse) if browse

                            # TODO: generate browse on the fly

                            else Browse.generate(product, browse_type)
                            for product, browse in self.iter_products_browses(
                                eo_object, filters_expressions, suffix, style
                            )
                        ]
                    )

                mask_type = self.get_mask_type(eo_object, suffix)
                if mask_type:
                    return MaskLayer(
                        name=full_name, style=style,
                        masks=[
                            Mask.from_model(mask_model)
                            for _, mask_model in self.iter_products_masks(
                                eo_object, filters_expressions, suffix
                            )
                        ]
                    )

                raise NoSuchLayer('Invalid layer suffix %r' % suffix)

    def split_layer_suffix_name(self, layer_name):
        return layer_name.partition(self.SUFFIX_SEPARATOR)[::2]

    def get_browse_type(self, eo_object, name):
        if isinstance(eo_object, models.Product):
            filter_ = dict(product_type__products=eo_object)
        else:
            filter_ = dict(
                product_type__allowed_collection_types__collections=eo_object
            )

        return models.BrowseType.objects.filter(name=name, **filter_).first()

    def get_mask_type(self, eo_object, name):
        if isinstance(eo_object, models.Product):
            filter_ = dict(product_type__products=eo_object)
        else:
            filter_ = dict(
                product_type__allowed_collection_types__collections=eo_object
            )

        return models.MaskType.objects.filter(name=name, **filter_).first()

    #
    # iteration methods
    #

    def iter_products(self, eo_object, filters_expressions):
        if isinstance(eo_object, models.Collection):
            base_filter = dict(collections=eo_object)
        else:
            base_filter = dict(product=eo_object)

        return models.Product.objects.filter(filters_expressions, **base_filter)

    def iter_products_browses(self, eo_object, filters_expressions,
                              name=None, style=None):
        products = self.iter_products(
            eo_object, filters_expressions
        ).prefetch_related('browses')

        for product in products:
            browses = product.browses
            if name:
                browses = browses.filter(browse_type__name=name)
            else:
                browses = browses.filter(browse_type__isnull=True)

            # if style:
            #     browses = browses.filter(style=style)
            # else:
            #     browses = browses.filter(style__isnull=True)

            yield (product, browses.first())

    def iter_products_masks(self, eo_object, filters_expressions, name=None):
        products = self.iter_products(
            eo_object, filters_expressions
        ).prefetch_related('masks')

        for product in products:
            masks = product.masks
            if name:
                mask = masks.filter(mask_type__name=name).first()
            else:
                mask = masks.filter(mask_type__isnull=True).first()

            yield (product, mask)

    def iter_products_browses_masks(self, eo_object, filters_expressions,
                                    name=None):
        products = self.iter_products(
            eo_object, filters_expressions
        ).prefetch_related('masks', 'browses')

        for product in products:
            if name:
                mask = product.masks.filter(mask_type__name=name).first()
            else:
                mask = product.masks.filter(mask_type__isnull=True).first()

            browse = product.browses.filter(browse_type__isnull=True).first()

            yield (product, browse, mask)
