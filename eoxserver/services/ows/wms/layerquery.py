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

from eoxserver.render.map.objects import (
    Map, CoverageLayer, OutlinesLayer, BrowseLayer, OutlinedBrowseLayer,
    MaskLayer, MaskedBrowseLayer,
    LayerDescription, RasterLayerDescription
)
from eoxserver.render.coverage.objects import Coverage as RenderCoverage
from eoxserver.render.browse.objects import (
    Browse, Mask, MaskedBrowse
)
from eoxserver.resources.coverages import models


class NoSuchLayer(Exception):
    pass


class NoSuchPrefix(NoSuchLayer):
    pass


class LayerQuery(object):
    """
    """

    SUFFIX_SEPARATOR = "__"

    def get_layer_description(self, eo_object, raster_styles, geometry_styles):
        if isinstance(eo_object, models.Coverage):
            coverage = RenderCoverage.from_model(eo_object)
            return RasterLayerDescription.from_coverage(coverage, raster_styles)
        elif isinstance(eo_object, (models.Product, models.Collection)):
            mask_types = []
            browse_types = []
            if getattr(eo_object, "product_type", None):
                browse_types = eo_object.product_type.browse_types.all()
                mask_types = eo_object.product_type.mask_types.all()
            elif getattr(eo_object, "collection_type", None):
                browse_types = models.BrowseType.objects.filter(
                    product_type__allowed_collection_types__collections=eo_object
                )
                mask_types = models.MaskType.objects.filter(
                    product_type__allowed_collection_types__collections=eo_object
                )

            sub_layers = [
                LayerDescription(
                    "%s%soutlines" % (
                        eo_object.identifier, self.SUFFIX_SEPARATOR
                    ),
                    styles=geometry_styles,
                    queryable=True
                ),
                LayerDescription(
                    "%s%soutlined" % (
                        eo_object.identifier, self.SUFFIX_SEPARATOR
                    ),
                    styles=geometry_styles,
                    queryable=True
                )
            ]
            for browse_type in browse_types:
                sub_layers.append(
                    RasterLayerDescription(
                        "%s%s%s" % (
                            eo_object.identifier, self.SUFFIX_SEPARATOR,
                            browse_type.name
                        ),
                        styles=geometry_styles
                    )
                )

            for mask_type in mask_types:
                sub_layers.append(
                    LayerDescription(
                        "%s%s%s" % (
                            eo_object.identifier, self.SUFFIX_SEPARATOR,
                            mask_type.name
                        ),
                        styles=geometry_styles
                    )
                )
                sub_layers.append(
                    LayerDescription(
                        "%s%smasked_%s" % (
                            eo_object.identifier, self.SUFFIX_SEPARATOR,
                            mask_type.name
                        ),
                        styles=geometry_styles
                    )
                )

            return LayerDescription(
                name=eo_object.identifier,
                bbox=eo_object.footprint.extent if eo_object.footprint else None,
                sub_layers=sub_layers
            )

    def lookup_layer(self, layer_name, suffix, style, filters_expressions,
                     sort_by, time, range, bands, wavelengths, elevation):
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
                            eo_object, filters_expressions, sort_by, None, style
                        )
                        if browse
                    ]
                )

            elif suffix == 'outlined':
                return OutlinedBrowseLayer(
                    name=full_name, style=style,
                    browses=[
                        Browse.from_model(product, browse)
                        for product, browse in self.iter_products_browses(
                            eo_object, filters_expressions, sort_by, None, style
                        )
                        if browse
                    ]
                )

            elif suffix == 'outlines':
                return OutlinesLayer(
                    name=full_name, style=style,
                    footprints=[
                        product.footprint for product in self.iter_products(
                            eo_object, filters_expressions, sort_by,
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
                            eo_object, filters_expressions, sort_by, post_suffix
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
                                eo_object, filters_expressions, sort_by, suffix,
                                style
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
                                eo_object, filters_expressions, sort_by, suffix
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

    def iter_products(self, eo_object, filters_expressions, sort_by=None):
        if isinstance(eo_object, models.Collection):
            base_filter = dict(collections=eo_object)
        else:
            base_filter = dict(product=eo_object)

        qs = models.Product.objects.filter(filters_expressions, **base_filter)

        if sort_by:
            qs = qs.order_by('%s%s' % (
                '-' if sort_by[1] == 'DESC' else '',
                sort_by[0]
            ))

        print qs

        return qs

    def iter_products_browses(self, eo_object, filters_expressions, sort_by,
                              name=None, style=None):
        products = self.iter_products(
            eo_object, filters_expressions, sort_by
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

    def iter_products_masks(self, eo_object, filters_expressions, sort_by,
                            name=None):
        products = self.iter_products(
            eo_object, filters_expressions, sort_by
        ).prefetch_related('masks')

        for product in products:
            masks = product.masks
            if name:
                mask = masks.filter(mask_type__name=name).first()
            else:
                mask = masks.filter(mask_type__isnull=True).first()

            yield (product, mask)

    def iter_products_browses_masks(self, eo_object, filters_expressions,
                                    sort_by, name=None):
        products = self.iter_products(
            eo_object, filters_expressions, sort_by
        ).prefetch_related('masks', 'browses')

        for product in products:
            if name:
                mask = product.masks.filter(mask_type__name=name).first()
            else:
                mask = product.masks.filter(mask_type__isnull=True).first()

            browse = product.browses.filter(browse_type__isnull=True).first()

            yield (product, browse, mask)
