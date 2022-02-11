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

from django.db.models import Case, Value, When, IntegerField, BooleanField
from django.conf import settings

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config, enum
from eoxserver.core.util.timetools import isoformat
from eoxserver.render.map.objects import (
    CoverageLayer, CoveragesLayer, OutlinedCoveragesLayer, MosaicLayer,
    OutlinesLayer, BrowseLayer, OutlinedBrowseLayer,
    MaskLayer, MaskedBrowseLayer,
    LayerDescription,
)
from eoxserver.render.coverage.objects import Coverage as RenderCoverage
from eoxserver.render.coverage.objects import Mosaic as RenderMosaic
from eoxserver.render.browse.objects import (
    Browse, GeneratedBrowse, Mask, MaskedBrowse
)
from eoxserver.resources.coverages import models


class UnsupportedObject(Exception):
    pass


class NoSuchLayer(Exception):
    code = 'LayerNotDefined'
    locator = 'layer'


class NoSuchPrefix(NoSuchLayer):
    code = 'LayerNotDefined'
    locator = 'layer'


DEFAULT_EOXS_LAYER_SUFFIX_SEPARATOR = '__'


class LayerMapper(object):
    """ Default layer mapper.
    """

    def __init__(self, supported_layer_types, suffix_separator=None):
        self.supported_layer_types = supported_layer_types
        if suffix_separator is None:
            suffix_separator = getattr(
                settings, 'EOXS_LAYER_SUFFIX_SEPARATOR',
                DEFAULT_EOXS_LAYER_SUFFIX_SEPARATOR
            )
        self.suffix_separator = suffix_separator

    def get_layer_description(self, eo_object, raster_styles, geometry_styles):
        if isinstance(eo_object, models.Coverage):
            coverage = RenderCoverage.from_model(eo_object)
            return LayerDescription.from_coverage(coverage, raster_styles)
        elif isinstance(eo_object, models.Mosaic):
            coverage = RenderCoverage.from_model(eo_object)
            return LayerDescription.from_mosaic(coverage, raster_styles)
        elif isinstance(eo_object, (models.Product, models.Collection)):
            dimensions = {}
            if eo_object.begin_time and eo_object.end_time:
                dimensions["time"] = {
                    'min': isoformat(eo_object.begin_time),
                    'max': isoformat(eo_object.end_time),
                    'step': 'PT1S',
                    'default': isoformat(eo_object.end_time),
                    'units': 'ISO8601'
                }

            if getattr(eo_object, "product_type", None):
                browse_type_qs = eo_object.product_type.browse_types.all()
                mask_type_qs = eo_object.product_type.mask_types.all()
            elif getattr(eo_object, "collection_type", None):
                browse_type_qs = models.BrowseType.objects.filter(
                    product_type__allowed_collection_types__collections=eo_object
                )
                mask_type_qs = models.MaskType.objects.filter(
                    product_type__allowed_collection_types__collections=eo_object
                )
            else:
                browse_type_qs = models.BrowseType.objects.none()
                mask_type_qs = models.MaskType.objects.none()

            browse_types_name_and_is_gray = browse_type_qs.annotate(
                is_gray=Case(
                    When(green_expression__isnull=True, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ).values_list('name', 'is_gray').distinct()
            mask_type_names = mask_type_qs.values_list(
                'name', flat=True
            ).distinct()

            sub_layers = [
                LayerDescription(
                    "%s%soutlines" % (
                        eo_object.identifier, self.suffix_separator
                    ),
                    styles=geometry_styles,
                    queryable=True,
                    dimensions=dimensions,
                ),
                LayerDescription(
                    "%s%soutlined" % (
                        eo_object.identifier, self.suffix_separator
                    ),
                    styles=geometry_styles,
                    queryable=True,
                    dimensions=dimensions,
                )
            ]
            for name, is_gray in browse_types_name_and_is_gray:
                sub_layers.append(
                    LayerDescription(
                        "%s%s%s" % (
                            eo_object.identifier, self.suffix_separator,
                            name
                        ) if name else eo_object.identifier,
                        styles=raster_styles if is_gray else [],
                        dimensions=dimensions,
                    )
                )

            for mask_type_name in mask_type_names:
                sub_layers.append(
                    LayerDescription(
                        "%s%s%s" % (
                            eo_object.identifier, self.suffix_separator,
                            mask_type_name
                        ),
                        styles=geometry_styles,
                        dimensions=dimensions,
                    )
                )
                sub_layers.append(
                    LayerDescription(
                        "%s%smasked_%s" % (
                            eo_object.identifier, self.suffix_separator,
                            mask_type_name,
                        ),
                        dimensions=dimensions,
                    )
                )

            return LayerDescription(
                name=eo_object.identifier,
                bbox=eo_object.footprint.extent if eo_object.footprint else None,
                dimensions=dimensions,
                sub_layers=sub_layers
            )

        raise UnsupportedObject(
            "Object %r cannot be mapped to a layer." % eo_object
        )

    def lookup_layer(self, layer_name, suffix, style, filters_expressions,
                     sort_by, time, ranges, bands, wavelengths, elevation,
                     zoom, variables):
        """ Lookup the layer from the registered objects.
        """
        reader = LayerMapperConfigReader(get_eoxserver_config())
        limit_products = (
            reader.limit_products if reader.limit_mode == 'hide' else None
        )
        min_render_zoom = reader.min_render_zoom
        full_name = '%s%s%s' % (layer_name, self.suffix_separator, suffix)

        try:
            eo_object = models.EOObject.objects.select_subclasses(
                models.Collection, models.Product, models.Coverage,
                models.Mosaic
            ).get(
                identifier=layer_name
            )
        except models.EOObject.DoesNotExist:
            raise NoSuchLayer('Layer %r does not exist' % layer_name)

        if isinstance(eo_object, models.Coverage):
            if suffix in ('', 'bands'):
                return CoverageLayer(
                    full_name, style,
                    RenderCoverage.from_model(eo_object),
                    bands, wavelengths, time, elevation, ranges
                )

            elif suffix == 'outlines':
                return OutlinesLayer(
                    name=full_name, style=style, fill=None,
                    footprints=[eo_object.footprint]
                )

            # TODO: masked coverages, when using the coverages product

            else:
                raise NoSuchLayer('Invalid layer suffix %r' % suffix)

        # TODO: deprecated
        elif isinstance(eo_object, models.Mosaic):
            if suffix == 'outlines':
                return OutlinesLayer(
                    name=full_name, style=style, fill=None,
                    footprints=[
                        coverage.footprint
                        for coverage in self.iter_coverages(
                            eo_object, filters_expressions, sort_by
                        )
                    ]
                )
            else:
                return MosaicLayer(
                    full_name, style,
                    RenderMosaic.from_model(eo_object), [
                        RenderCoverage.from_model(coverage)
                        for coverage in self.iter_coverages(
                            eo_object, filters_expressions, sort_by
                        )
                    ], bands, wavelengths, time, elevation, ranges
                )

        elif isinstance(eo_object, (models.Collection, models.Product)):
            if suffix == '' or suffix == 'outlined' or suffix == 'bands':
                browses = []
                product_browses = self.iter_products_browses(
                    eo_object, filters_expressions, sort_by, None, style,
                    limit=limit_products
                )

                has_products = False
                for product, browse, _ in product_browses:
                    # When bands/wavelengths are specifically requested, make a
                    # generated browse
                    if bands or wavelengths:
                        browse = _generate_browse_from_bands(
                            product, bands, wavelengths, ranges
                        )
                        if browse:
                            browses.append(browse)
                            has_products = True

                    # When available use the default browse
                    elif browse:
                        browses.append(Browse.from_model(product, browse))
                        has_products = True

                    # As fallback use the default browse type (with empty name)
                    # to generate a browse from the specified bands
                    else:
                        browse_type = product.product_type.browse_types.filter(
                            name=''
                        ).first()
                        if browse_type:
                            browse = _generate_browse_from_browse_type(
                                product, browse_type, variables
                            )
                            if browse:
                                browses.append(browse)
                                has_products = True

                if not has_products:
                    coverages = self.iter_coverages(
                        eo_object, filters_expressions, sort_by
                    )

                    if suffix == '':
                        return CoveragesLayer(
                            full_name, style, [
                                RenderCoverage.from_model(coverage)
                                for coverage in coverages
                            ],
                            bands, wavelengths, time, elevation, ranges
                        )
                    else:
                        return OutlinedCoveragesLayer(
                            full_name, style, [
                                RenderCoverage.from_model(coverage)
                                for coverage in coverages
                            ],
                            bands, wavelengths, time, elevation, ranges
                        )

                # detect whether we are below the zoom limit
                if min_render_zoom is None or zoom >= min_render_zoom:
                    # either return the simple browse layer or the outlined one
                    if suffix == '':
                        return BrowseLayer(
                            name=full_name, style=style,
                            browses=browses, ranges=ranges
                        )
                    else:
                        return OutlinedBrowseLayer(
                            name=full_name, style=style,
                            browses=browses, ranges=ranges
                        )

                # render outlines when we are below the zoom limit
                else:
                    return OutlinesLayer(
                        name=full_name, style=reader.color,
                        fill=reader.fill_opacity,
                        footprints=[
                            product.footprint for product in self.iter_products(
                                eo_object, filters_expressions, sort_by,
                                limit=limit_products
                            )
                        ]
                    )

            elif suffix == 'outlines':
                return OutlinesLayer(
                    name=full_name, style=style, fill=None,
                    footprints=[
                        product.footprint for product in self.iter_products(
                            eo_object, filters_expressions, sort_by,
                            limit=limit_products
                        )
                    ]
                )

            elif suffix.startswith('outlines_masked_'):
                post_suffix = suffix[len('outlines_masked_'):]

                product_browses_mask = self.iter_products_browses_masks(
                    eo_object, filters_expressions, sort_by, post_suffix,
                    limit=limit_products
                )
                footprints = []
                masks = []
                for product, browse, mask, mask_type in product_browses_mask:
                    footprints.append(product.footprint)
                    masks.append(Mask.from_model(mask, mask_type))

                return OutlinesLayer(
                    name=full_name, style=style, fill=None,
                    footprints=footprints,
                    masks=masks,
                )

            elif suffix.startswith('masked_'):
                post_suffix = suffix[len('masked_'):]
                mask_type = self.get_mask_type(eo_object, post_suffix)

                if not mask_type:
                    raise NoSuchLayer('No such mask type %r' % post_suffix)

                masked_browses = []

                product_browses_mask = self.iter_products_browses_masks(
                    eo_object, filters_expressions, sort_by, post_suffix,
                    limit=limit_products
                )
                for product, browse, mask, mask_type in product_browses_mask:
                    # When bands/wavelengths are specifically requested, make a
                    # generated browse
                    if bands or wavelengths:
                        masked_browses.append(
                            MaskedBrowse(
                                browse=_generate_browse_from_bands(
                                    product, bands, wavelengths, ranges
                                ),
                                mask=Mask.from_model(mask, mask_type)
                            )
                        )

                    # When available use the default browse
                    elif browse:
                        masked_browses.append(
                            MaskedBrowse.from_models(
                                product, browse, mask, mask_type
                            )
                        )

                    # As fallback use the default browse type (with empty name)
                    # to generate a browse from the specified bands
                    else:
                        browse_type = product.product_type.browse_types.filter(
                            name=''
                        ).first()
                        if browse_type:
                            masked_browses.append(
                                MaskedBrowse(
                                    browse=_generate_browse_from_browse_type(
                                        product, browse_type, variables
                                    ),
                                    mask=Mask.from_model(mask, mask_type)
                                )
                            )

                return MaskedBrowseLayer(
                    name=full_name, style=style,
                    masked_browses=masked_browses
                )

            else:
                # either browse type or mask type
                browse_type = self.get_browse_type(eo_object, suffix)
                if browse_type:
                    browses = []

                    product_browses = self.iter_products_browses(
                        eo_object, filters_expressions, sort_by, suffix,
                        style, limit=limit_products
                    )

                    for product, browse, browse_type in product_browses:
                        # check if a browse is already available for that
                        # browse type.
                        if browse:
                            browses.append(Browse.from_model(product, browse))

                        # if no browse is available for that browse type,
                        # generate a new browse with the instructions of that
                        # browse type
                        else:
                            browse = _generate_browse_from_browse_type(
                                product, browse_type, variables
                            )
                            if browse:
                                browses.append(browse)

                    return BrowseLayer(
                        name=full_name, style=style, ranges=ranges,
                        browses=browses
                    )

                mask_type = self.get_mask_type(eo_object, suffix)
                if mask_type:
                    return MaskLayer(
                        name=full_name, style=style,
                        masks=[
                            Mask.from_model(mask_model, mask_type)
                            for _, mask_model in self.iter_products_masks(
                                eo_object, filters_expressions, sort_by, suffix,
                                limit=limit_products
                            )
                        ]
                    )

                raise NoSuchLayer('Invalid layer suffix %r' % suffix)

    def split_layer_suffix_name(self, layer_name):
        return layer_name.partition(self.suffix_separator)[::2]

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

    def iter_coverages(self, eo_object, filters_expressions, sort_by=None):
        if isinstance(eo_object, models.Mosaic):
            base_filter = dict(mosaics=eo_object)
        elif isinstance(eo_object, models.Collection):
            base_filter = dict(collections=eo_object)
        elif isinstance(eo_object, models.Product):
            base_filter = dict(parent_product=eo_object)

        qs = models.Coverage.objects.filter(filters_expressions, **base_filter)
        if sort_by:
            qs = qs.order_by('%s%s' % (
                '-' if sort_by[1] == 'DESC' else '',
                sort_by[0]
            ))
        else:
            qs = qs.order_by(
                '-begin_time', '-end_time', 'identifier'
            )

        return qs

    def iter_products(self, eo_object, filters_expressions, sort_by=None,
                      limit=None):
        if isinstance(eo_object, models.Collection):
            base_filter = dict(collections=eo_object)
        else:
            base_filter = dict(pk=eo_object.pk)

        qs = models.Product.objects.filter(filters_expressions, **base_filter)
        if limit is not None:
            qs = qs[:limit]

        if sort_by:
            qs = qs.order_by('%s%s' % (
                '-' if sort_by[1] == 'DESC' else '',
                sort_by[0]
            ))
        else:
            qs = qs.order_by(
                '-begin_time', '-end_time', 'identifier'
            )

        return qs

    def iter_products_browses(self, eo_object, filters_expressions, sort_by,
                              name=None, style=None, limit=None):
        products = self.iter_products(
            eo_object, filters_expressions, sort_by, limit
        ).prefetch_related('browses')

        for product in products:
            browses = product.browses
            if name:
                browses = browses.filter(browse_type__name=name)
                browse = browses.first()
                if browse:
                    browse_type = browse.browse_type
                else:
                    browse_type = models.BrowseType.objects.get(
                        name=name, product_type=product.product_type
                    )
            else:
                browses = browses.filter(browse_type__isnull=True)
                browse_type = None

            # if style:
            #     browses = browses.filter(style=style)
            # else:
            #     browses = browses.filter(style__isnull=True)

            yield (product, browses.first(), browse_type)

    def iter_products_masks(self, eo_object, filters_expressions, sort_by,
                            name=None, limit=None):
        products = self.iter_products(
            eo_object, filters_expressions, sort_by, limit
        ).prefetch_related('masks')

        for product in products:
            masks = product.masks
            if name:
                mask = masks.filter(mask_type__name=name).first()
            else:
                mask = masks.filter(mask_type__isnull=True).first()

            yield (product, mask)

    def iter_products_browses_masks(self, eo_object, filters_expressions,
                                    sort_by, name=None, limit=None):
        products = self.iter_products(
            eo_object, filters_expressions, sort_by, limit
        ).prefetch_related('masks', 'browses')

        for product in products:
            if name:
                mask = product.masks.filter(mask_type__name=name).first()
                mask_type = models.MaskType.objects.filter(
                    product_type=product.product_type, name=name
                ).first()
            else:
                mask = product.masks.filter(mask_type__isnull=True).first()
                mask_type = None

            browse = product.browses.filter(browse_type__isnull=True).first()

            yield (product, browse, mask, mask_type)


class LayerMapperConfigReader(config.Reader):
    section = "services.ows.wms"
    limit_products = config.Option(type=int)
    limit_mode = config.Option(type=enum('hide', 'outlines'), default='hide')
    min_render_zoom = config.Option(type=int)
    fill_opacity = config.Option(type=float)
    color = config.Option(type=str, default='grey')


def _generate_browse_from_browse_type(product, browse_type, variables):
    if not browse_type.red_or_grey_expression:
        return None

    from eoxserver.render.browse.generate import extract_fields

    band_expressions = []
    ranges = []
    nodata_values = []
    field_names = []
    red_bands = extract_fields(browse_type.red_or_grey_expression)
    band_expressions.append(browse_type.red_or_grey_expression)
    ranges.append((
        browse_type.red_or_grey_range_min,
        browse_type.red_or_grey_range_max,
    ))
    nodata_values.append(browse_type.red_or_grey_nodata_value)
    field_names.extend(red_bands)

    if browse_type.green_expression and browse_type.blue_expression:
        green_bands = extract_fields(browse_type.green_expression)
        blue_bands = extract_fields(browse_type.blue_expression)
        band_expressions.append(browse_type.green_expression)
        ranges.append((
            browse_type.green_range_min,
            browse_type.green_range_max,
        ))
        nodata_values.append(browse_type.green_nodata_value)
        band_expressions.append(browse_type.blue_expression)
        ranges.append((
            browse_type.blue_range_min,
            browse_type.blue_range_max,
        ))
        nodata_values.append(browse_type.blue_nodata_value)
        field_names.extend(green_bands)
        field_names.extend(blue_bands)

        if browse_type.alpha_expression:
            alpha_bands = extract_fields(browse_type.alpha_expression)
            band_expressions.append(browse_type.alpha_expression)
            ranges.append((
                browse_type.alpha_range_min,
                browse_type.alpha_range_max,
            ))
            nodata_values.append(browse_type.alpha_nodata_value)
            field_names.extend(alpha_bands)

    coverages, fields_and_coverages = _lookup_coverages(product, field_names)

    # only return a browse instance if coverages were found
    if coverages:
        return GeneratedBrowse.from_coverage_models(
            band_expressions,
            ranges,
            nodata_values,
            fields_and_coverages,
            product,
            variables,
        )
    return None


def _generate_browse_from_bands(product, bands, wavelengths, ranges):
    assert len(bands or wavelengths or []) in (1, 3, 4)
    if bands:
        coverages, fields_and_coverages = _lookup_coverages(product, bands)
    # TODO: implement with wavelengths
    # elif wavelengths:
    #     fields_and_coverages = [
    #         (
    #             [product.coverages.filter(
    #                 coverage_type__field_types__wavelength=wavelength
    #             ).first().name],
    #             product.coverages.filter(
    #                 coverage_type__field_types__wavelength=wavelength
    #             )
    #         )
    #         for wavelength in wavelengths
    #     ]
    # only return a browse instance if coverages were found
    if coverages:
        return GeneratedBrowse.from_coverage_models(
            bands,
            ranges or [(None, None)] * len(bands),
            [None] * len(bands),
            fields_and_coverages,
            product
        )
    return None


def _lookup_coverages(product, field_names):
    # make a query of all coverages in that product for the given fields
    coverages = product.coverages.filter(
        coverage_type__field_types__identifier__in=field_names
    )

    # annotate the coverages with booleans indicating whether or not they
    # have a certain field
    coverages = coverages.annotate(**{
        'has_%s' % field_name: Case(
            When(
                coverage_type__field_types__identifier=field_name,
                then=Value(1)
            ),
            default=Value(0),
            output_field=IntegerField()
        )
        for field_name in field_names
    })

    # evaluate the queryset
    coverages = list(coverages)

    # make a dictionary for all field mapping to their respective coverages
    fields_and_coverages = {
        field_name: [
            coverage
            for coverage in coverages
            if getattr(coverage, 'has_%s' % field_name)
        ]
        for field_name in field_names
    }
    return coverages, fields_and_coverages
