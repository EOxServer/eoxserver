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
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

from os.path import join
from uuid import uuid4
try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.core.util.iteratortools import pairwise_iterative
from eoxserver.contrib import mapserver as ms
from eoxserver.contrib import vsi, vrt, gdal, osr
from eoxserver.render.browse.objects import (
    Browse, GeneratedBrowse, BROWSE_MODE_GRAYSCALE
)
from eoxserver.render.browse.generate import (
    generate_browse, FilenameGenerator
)
from eoxserver.render.map.objects import (
    CoverageLayer, CoveragesLayer, MosaicLayer, OutlinedCoveragesLayer,
    BrowseLayer, OutlinedBrowseLayer,
    MaskLayer, MaskedBrowseLayer, OutlinesLayer
)
from eoxserver.render.mapserver.config import (
    DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES,
)
from eoxserver.render.colors import BASE_COLORS, COLOR_SCALES, OFFSITE_COLORS
from eoxserver.resources.coverages import crss
from eoxserver.resources.coverages.dateline import (
    extent_crosses_dateline, wrap_extent_around_dateline
)
from eoxserver.processing.gdal import reftools

import logging
logger = logging.getLogger(__name__)


class BaseMapServerLayerFactory(object):
    handled_layer_types = []

    @classmethod
    def supports(self, layer_type):
        return layer_type in self.handled_layer_types

    def create(self, map_obj, layer):
        pass

    def destroy(self, map_obj, layer, data):
        pass


class CoverageLayerFactoryMixIn(object):
    """ Base class for factories dealing with coverages.
    """
    def get_fields(self, fields, bands, wavelengths):
        """ Get the field subset for the given bands/wavelengths selection
        """
        if bands:
            assert len(bands) in (1, 3, 4)
            try:
                fields = [
                    next(field for field in fields if field.identifier == band)
                    for band in bands
                ]
            except StopIteration:
                raise Exception('Invalid bands specified.')
        elif wavelengths:
            assert len(wavelengths) in (1, 3, 4)
            try:
                fields = [
                    next(
                        field
                        for field in fields if field.wavelength == wavelength
                    )
                    for wavelength in wavelengths
                ]
            except StopIteration:
                raise Exception('Invalid wavelengths specified.')
        else:
            # when fields is not 1 (single band grayscale), 3 (RGB) or 4 (RGBA)
            # then use the first band by default
            if len(fields) not in (1, 3, 4):
                return fields[:1]

        return fields

    def create_coverage_layer(self, map_obj, coverage, fields,
                              style=None, ranges=None):
        """ Creates a mapserver layer object for the given coverage
        """
        filename_generator = FilenameGenerator(
            '/vsimem/{uuid}.{extension}', 'vrt'
        )

        field_locations = [
            (field, coverage.get_location_for_field(field))
            for field in fields
        ]
        locations = [
            location
            for _, location in field_locations
        ]

        # TODO: apply subsets in time/elevation dims
        num_locations = len(set(locations))
        if num_locations == 1:
            if not coverage.grid.is_referenceable:
                location = field_locations[0][1]
                data = location.path
                ms.set_env(map_obj, location.env, True)
            else:
                vrt_path = filename_generator.generate()
                e = map_obj.extent
                resx = (e.maxx - e.minx) / map_obj.width
                resy = (e.maxy - e.miny) / map_obj.height

                wkt = osr.SpatialReference(map_obj.getProjection()).wkt

                # TODO: env?
                reftools.create_rectified_vrt(
                    field_locations[0][1].path, vrt_path,
                    order=1, max_error=10,
                    resolution=(resx, -resy), srid_or_wkt=wkt
                )
                data = vrt_path

        elif num_locations > 1:
            paths_set = set(
                field_location[1].path for field_location in field_locations
            )
            if len(paths_set) == 1:
                location = field_locations[0][1]
                data = location.path
                ms.set_env(map_obj, location.env, True)

            else:
                # TODO
                _build_vrt(coverage.size, field_locations)

        if not coverage.grid.is_referenceable:
            extent = coverage.extent
            sr = coverage.grid.spatial_reference
        else:
            map_extent = map_obj.extent
            extent = (
                map_extent.minx, map_extent.miny,
                map_extent.maxx, map_extent.maxy
            )
            sr = osr.SpatialReference(map_obj.getProjection())

        layer_objs = _create_raster_layer_objs(
            map_obj, extent, sr, data, filename_generator
        )

        for i, layer_obj in enumerate(layer_objs):
            layer_obj.name = '%s__%d' % (coverage.identifier, i)
            layer_obj.setProcessingKey("CLOSE_CONNECTION", "CLOSE")

        if num_locations == 1:
            for layer_obj in layer_objs:
                layer_obj.setProcessingKey("BANDS", ",".join([
                    str(coverage.get_band_index_for_field(field))
                    for field in fields
                ]))
        elif num_locations > 1:
            for layer_obj in layer_objs:
                if len(field_locations) == 3:
                    layer_obj.setProcessingKey("BANDS", "1,2,3")
                else:
                    layer_obj.setProcessingKey("BANDS", "1")

        # make a color-scaled layer
        if len(fields) == 1:
            field = fields[0]
            if ranges:
                range_ = ranges[0]
            else:
                range_ = _get_range(field)

            for layer_obj in layer_objs:
                _create_raster_style(
                    style or "blackwhite", layer_obj, range_[0], range_[1], [
                        nil_value[0] for nil_value in field.nil_values
                    ]
                )
        elif len(fields) in (3, 4):
            for i, field in enumerate(fields, start=1):
                if ranges:
                    if len(ranges) == 1:
                        range_ = ranges[0]
                    else:
                        range_ = ranges[i - 1]
                else:
                    range_ = _get_range(field)

                for layer_obj in layer_objs:
                    layer_obj.setProcessingKey(
                        "SCALE_%d" % i,
                        "%s,%s" % range_
                    )
                    layer_obj.offsite = ms.colorObj(0, 0, 0)

        else:
            raise Exception("Too many bands specified")

        return filename_generator

    def destroy_coverage_layer(self, filename_generator):
        for filename in filename_generator.filenames:
            vsi.unlink(filename)


class CoverageLayerFactory(CoverageLayerFactoryMixIn,
                           BaseMapServerLayerFactory):
    handled_layer_types = [CoverageLayer, CoveragesLayer]

    def create(self, map_obj, layer):
        if isinstance(layer, CoverageLayer):
            coverages = [layer.coverage]
        else:
            coverages = layer.coverages

        coverage_layers = []
        for coverage in reversed(coverages):
            fields = self.get_fields(
                coverage.range_type, layer.bands, layer.wavelengths
            )
            coverage_layers.append(
                self.create_coverage_layer(
                    map_obj, coverage, fields, layer.style, layer.ranges
                )
            )

        return coverage_layers

    def destroy(self, map_obj, layer, data):
        for coverage_layer in data:
            self.destroy_coverage_layer(coverage_layer)


class OutlinedCoverageLayerFactory(CoverageLayerFactoryMixIn,
                                   BaseMapServerLayerFactory):
    handled_layer_types = [OutlinedCoveragesLayer]

    def create(self, map_obj, layer):
        coverages = layer.coverages
        style = layer.style

        raster_style = (
            style if style and style in COLOR_SCALES else "blackwhite"
        )
        vector_style = (
            style if style and style in BASE_COLORS else "red"
        )

        coverage_layers = []

        for coverage in reversed(coverages):
            fields = self.get_fields(
                coverage.range_type, layer.bands, layer.wavelengths
            )
            coverage_layers.append(
                self.create_coverage_layer(
                    map_obj, coverage, fields, raster_style, layer.ranges
                )
            )

            # create the outlines layer
            outlines_layer_obj = _create_polygon_layer(map_obj)
            shape_obj = ms.shapeObj.fromWKT(coverage.footprint.wkt)
            outlines_layer_obj.addFeature(shape_obj)

            class_obj = _create_geometry_class(vector_style)
            outlines_layer_obj.insertClass(class_obj)

        return coverage_layers

    def destroy(self, map_obj, layer, data):
        for coverage_layer in data:
            self.destroy_coverage_layer(coverage_layer)


class MosaicLayerFactory(CoverageLayerFactoryMixIn, BaseMapServerLayerFactory):
    handled_layer_types = [MosaicLayer]

    def create(self, map_obj, layer):
        mosaic = layer.mosaic
        fields = self.get_fields(
            mosaic.range_type, layer.bands, layer.wavelengths
        )
        return [
            self.create_coverage_layer(
                map_obj, coverage, fields, layer.style, layer.ranges
            )
            for coverage in reversed(layer.coverages)
        ]

    def destroy(self, map_obj, layer, data):
        for item in data:
            self.destroy_coverage_layer(item)

# TODO: combine BrowseLayerFactory with OutlinedBrowseLayerFactory, as they are
# very similar


class BrowseLayerMixIn(object):
    def make_browse_layer_generator(self, map_obj, browses, map_,
                                    filename_generator, group_name, ranges,
                                    style):
        for browse in browses:
            if isinstance(browse, GeneratedBrowse):
                creation_info, filename_generator, reset_info = \
                    generate_browse(
                        browse.band_expressions,
                        browse.fields_and_coverages,
                        map_.width, map_.height,
                        map_.bbox,
                        map_.crs,
                        filename_generator,
                        browse.variables,
                    )
                layer_objs = _create_raster_layer_objs(
                    map_obj, browse.extent, browse.spatial_reference,
                    creation_info.filename, filename_generator
                )

                for layer_obj in layer_objs:
                    layer_obj.data = creation_info.filename
                    if creation_info.env:
                        ms.set_env(map_obj, creation_info.env, True)

                    if creation_info.bands:
                        layer_obj.setProcessingKey('BANDS', ','.join(
                            str(band) for band in creation_info.bands
                        ))

                    if reset_info:
                        sr = osr.SpatialReference(map_.crs)
                        extent = map_.bbox
                        layer_obj.setMetaData(
                            "wms_extent",
                            "%f %f %f %f" % extent
                        )
                        layer_obj.setExtent(*extent)

                        if sr.srid is not None:
                            short_epsg = "EPSG:%d" % sr.srid
                            layer_obj.setMetaData("ows_srs", short_epsg)
                            layer_obj.setMetaData("wms_srs", short_epsg)
                        layer_obj.setProjection(sr.proj)

                if browse.mode == BROWSE_MODE_GRAYSCALE:
                    field = browse.field_list[0]
                    if ranges:
                        browse_range = ranges[0]
                    elif browse.ranges[0] != (None, None):
                        browse_range = browse.ranges[0]
                    else:
                        browse_range = _get_range(field)

                    for layer_obj in layer_objs:
                        _create_raster_style(
                            style or "blackwhite", layer_obj,
                            browse_range[0], browse_range[1],
                            browse.nodata_values
                        )

                else:
                    browse_iter = enumerate(
                        zip(browse.field_list, browse.ranges), start=1
                    )
                    for i, (field, field_range) in browse_iter:
                        if ranges:
                            if len(ranges) == 1:
                                range_ = ranges[0]
                            else:
                                range_ = ranges[i - 1]
                        elif field_range != (None, None):
                            range_ = field_range
                        else:
                            range_ = _get_range(field)

                        for layer_obj in layer_objs:
                            layer_obj.setProcessingKey(
                                "SCALE_%d" % i,
                                "%s,%s" % tuple(range_)
                            )

            elif isinstance(browse, Browse):
                layer_objs = _create_raster_layer_objs(
                    map_obj, browse.extent, browse.spatial_reference,
                    browse.filename, filename_generator
                )
                for layer_obj in layer_objs:
                    layer_obj.data = browse.filename
                ms.set_env(map_obj, browse.env, True)
            elif browse is None:
                # TODO: figure out why and deal with it?
                continue
            else:
                raise TypeError(
                    'Type %s is not supported', type(browse).__name__
                )

            for layer_obj in layer_objs:
                layer_obj.group = group_name

            yield browse, layer_objs


class BrowseLayerFactory(CoverageLayerFactoryMixIn, BrowseLayerMixIn,
                         BaseMapServerLayerFactory):
    handled_layer_types = [BrowseLayer]

    def create(self, map_obj, layer):
        filename_generator = FilenameGenerator(
            '/vsimem/{uuid}.{extension}', 'vrt'
        )
        group_name = layer.name
        ranges = layer.ranges
        style = layer.style

        generator = self.make_browse_layer_generator(
            map_obj, reversed(layer.browses), layer.map, filename_generator,
            group_name, ranges, style
        )

        for _ in generator:
            pass

        return filename_generator

    def destroy(self, map_obj, layer, filename_generator):
        # cleanup temporary files
        for filename in filename_generator.filenames:
            vsi.unlink(filename)


class OutlinedBrowseLayerFactory(BrowseLayerMixIn, BaseMapServerLayerFactory):
    handled_layer_types = [OutlinedBrowseLayer]

    def create(self, map_obj, layer):
        filename_generator = FilenameGenerator('/vsimem/{uuid}.vrt')
        group_name = layer.name
        ranges = layer.ranges
        style = layer.style

        raster_style = (
            style if style and style in COLOR_SCALES else "blackwhite"
        )
        vector_style = (
            style if style and style in BASE_COLORS else "red"
        )

        generator = self.make_browse_layer_generator(
            map_obj, reversed(layer.browses), layer.map, filename_generator,
            group_name, ranges, raster_style
        )

        for browse, _ in generator:
            # create the outlines layer
            outlines_layer_obj = _create_polygon_layer(map_obj)
            shape_obj = ms.shapeObj.fromWKT(browse.footprint.wkt)
            outlines_layer_obj.addFeature(shape_obj)

            class_obj = _create_geometry_class(vector_style)
            outlines_layer_obj.insertClass(class_obj)

        return filename_generator

    def destroy(self, map_obj, layer, filename_generator):
        # cleanup temporary files
        for filename in filename_generator.filenames:
            vsi.unlink(filename)


class MaskLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [MaskLayer]

    def create(self, map_obj, layer):
        layer_obj = _create_polygon_layer(map_obj)
        for mask in reversed(layer.masks):
            if mask.geometry:
                mask_geom = mask.geometry
            elif mask.filename:
                mask_geom = mask.load_geometry()
            else:
                continue

            shape_obj = ms.shapeObj.fromWKT(mask_geom.wkt)
            layer_obj.addFeature(shape_obj)

        layer_obj.insertClass(
            _create_geometry_class(layer.style or 'red', fill_opacity=1.0)
        )


class MaskedBrowseLayerFactory(BrowseLayerMixIn, BaseMapServerLayerFactory):
    handled_layer_types = [MaskedBrowseLayer]

    def create(self, map_obj, layer):
        filename_generator = FilenameGenerator('/vsimem/{uuid}.vrt')
        group_name = layer.name

        browses, masks = zip(*[
            [masked_browse.browse, masked_browse.mask]
            for masked_browse in reversed(layer.masked_browses)
        ]) if len(layer.masked_browses) > 0 else ([], [])

        generator = self.make_browse_layer_generator(
            map_obj, browses, layer.map, filename_generator,
            group_name, None, None
        )

        for browse_and_layer_objs, mask in zip(generator, masks):
            browse, browse_layer_objs = browse_and_layer_objs

            mask_name = 'mask__%d' % id(mask)

            # create mapserver layers for the mask
            mask_layer_obj = _create_polygon_layer(map_obj)
            mask_layer_obj.status = ms.MS_OFF
            mask_layer_obj.insertClass(
                _create_geometry_class("black", "white", fill_opacity=1.0)
            )

            if mask.geometry:
                mask_geom = mask.geometry
            elif mask.filename:
                mask_geom = mask.load_geometry()
            else:
                mask_geom = None

            # the current logic:
            # when dealing with validity masks:
            #  - when geometry is available, use it as a mask
            #  - when not, the browse shall be hidden
            # when dealing with 'normal' masks:
            #  - use footprint/image bounds and cutout geometry

            # TODO: currently it is assumed that all geometries
            # are in EPSG:4326 which is not necessarily the case.
            # Reprojection is required.

            outline = browse.footprint
            if mask_geom:
                if mask.validity:
                    outline = mask_geom
                else:
                    outline = outline - mask_geom
            elif mask.validity:
                outline = None

            if outline:
                shape_obj = ms.shapeObj.fromWKT(outline.wkt)
                mask_layer_obj.addFeature(shape_obj)

            mask_layer_obj.name = mask_name

            # set up the mapserver layers required for the browses
            for browse_layer_obj in browse_layer_objs:
                browse_layer_obj.mask = mask_name

        return filename_generator

    def destroy(self, map_obj, layer, filename_generator):
        # cleanup temporary files
        for filename in filename_generator.filenames:
            vsi.unlink(filename)


class OutlinesLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [OutlinesLayer]

    def create(self, map_obj, layer):
        layer_obj = _create_polygon_layer(map_obj)
        footprint_masks = list(
            izip_longest(layer.footprints, layer.masks or [])
        )
        for footprint, mask in reversed(footprint_masks):
            if mask:
                if mask.geometry:
                    mask_geom = mask.geometry
                elif mask.filename:
                    mask_geom = mask.load_geometry()

                if mask.validity:
                    footprint = footprint.intersection(mask_geom)
                else:
                    footprint = footprint.difference(mask_geom)

            shape_obj = ms.shapeObj.fromWKT(footprint.wkt)
            layer_obj.addFeature(shape_obj)

        class_obj = _create_geometry_class(
            layer.style or 'red', fill_opacity=layer.fill
        )
        layer_obj.insertClass(class_obj)


# ------------------------------------------------------------------------------
# utils
# ------------------------------------------------------------------------------


def _create_raster_layer_objs(map_obj, extent, sr, data, filename_generator,
                              resample=None):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_RASTER
    layer_obj.status = ms.MS_ON

    layer_obj.data = data

    layer_obj.offsite = ms.colorObj(0, 0, 0)

    if extent:
        layer_obj.setMetaData("wms_extent", "%f %f %f %f" % extent)
        layer_obj.setExtent(*extent)

        if sr.srid is not None:
            short_epsg = "EPSG:%d" % sr.srid
            layer_obj.setMetaData("ows_srs", short_epsg)
            layer_obj.setMetaData("wms_srs", short_epsg)

    layer_obj.setProjection(sr.proj)

    if resample:
        layer_obj.setProcessingKey('RESAMPLE', resample)

    if extent and sr.srid and extent_crosses_dateline(extent, sr.srid):
        wrapped_extent = wrap_extent_around_dateline(extent, sr.srid)

        wrapped_layer_obj = ms.layerObj(map_obj)
        wrapped_layer_obj.type = ms.MS_LAYER_RASTER
        wrapped_layer_obj.status = ms.MS_ON

        wrapped_data = filename_generator.generate()
        vrt.with_extent(data, wrapped_extent, wrapped_data)
        wrapped_layer_obj.data = wrapped_data

        wrapped_layer_obj.offsite = ms.colorObj(0, 0, 0)

        wrapped_layer_obj.setMetaData("ows_srs", short_epsg)
        wrapped_layer_obj.setMetaData("wms_srs", short_epsg)
        wrapped_layer_obj.setProjection(sr.proj)

        wrapped_layer_obj.setExtent(*wrapped_extent)
        wrapped_layer_obj.setMetaData(
            "wms_extent", "%f %f %f %f" % wrapped_extent
        )
        return [layer_obj, wrapped_layer_obj]
    else:
        return [layer_obj]


def _create_polygon_layer(map_obj):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_POLYGON
    layer_obj.status = ms.MS_ON

    layer_obj.offsite = ms.colorObj(0, 0, 0)

    srid = 4326
    layer_obj.setProjection(crss.asProj4Str(srid))
    layer_obj.setMetaData("ows_srs", crss.asShortCode(srid))
    layer_obj.setMetaData("wms_srs", crss.asShortCode(srid))

    layer_obj.dump = True

    return layer_obj


def _create_geometry_class(color_name, background_color_name=None,
                           fill_opacity=None):
    cls_obj = ms.classObj()
    outline_style_obj = ms.styleObj()

    try:
        color = ms.colorObj(*BASE_COLORS[color_name])
    except KeyError:
        raise  # TODO

    outline_style_obj.outlinecolor = color
    cls_obj.insertStyle(outline_style_obj)

    if fill_opacity is not None:
        fill_style_obj = ms.styleObj()
        fill_style_obj.color = ms.colorObj(
            color.red, color.green, color.blue, int(255 * fill_opacity)
        )
        cls_obj.insertStyle(fill_style_obj)

    if background_color_name:
        outline_style_obj.backgroundcolor = ms.colorObj(
            *BASE_COLORS[background_color_name]
        )

    cls_obj.group = color_name
    return cls_obj


def _build_vrt(size, field_locations):
    path = join("/vsimem", uuid4().hex)
    size_x, size_y = size[:2]

    vrt_builder = vrt.VRTBuilder(size_x, size_y, vrt_filename=path)

    current = 1
    for field, location in field_locations:
        start = location.start_field
        end = location.end_field
        num = end - start + 1
        dst_band_indices = range(current, current + num)
        src_band_indices = range(1, num + 1)

        current += num

        for src_index, dst_index in zip(src_band_indices, dst_band_indices):
            vrt_builder.add_band(field.data_type)
            vrt_builder.add_simple_source(
                dst_index, location.path, src_index
            )

    del vrt_builder

    return path


def _create_raster_style(name, layer, minvalue=0, maxvalue=255,
                         nil_values=None):
    colors = COLOR_SCALES[name]

    if nil_values and all(v is not None for v in nil_values):
        nil_values = [float(nil_value) for nil_value in nil_values]
    else:
        nil_values = []

    if nil_values:
        offsite = ms.colorObj(*OFFSITE_COLORS.get(name, (0, 0, 0)))
        layer.offsite = offsite

        for nil_value in nil_values:
            cls = ms.classObj()
            cls.setExpression("([pixel] = %s)" % nil_value)
            cls.group = name

            style = ms.styleObj()
            style.color = offsite
            style.opacity = 0
            cls.insertStyle(style)
            layer.insertClass(cls)

    low_nil_values = [
        nil_value for nil_value in nil_values
        if nil_value <= minvalue
    ]
    high_nil_values = [
        nil_value for nil_value in nil_values
        if nil_value >= maxvalue
    ]

    # Create style for values below range, but make sure to not collide
    # with nil-values
    if low_nil_values:
        low_nil = max(low_nil_values)
        cls = ms.classObj()
        cls.setExpression(
            "([pixel] < %s AND [pixel] > %s)" % (minvalue, low_nil)
        )
        cls.group = name
        style = ms.styleObj()
        style.color = ms.colorObj(*colors[0][1])
        cls.insertStyle(style)
        layer.insertClass(cls)
    else:
        cls = ms.classObj()
        cls.setExpression("([pixel] <= %s)" % (minvalue))
        cls.group = name
        style = ms.styleObj()
        style.color = ms.colorObj(*colors[0][1])
        cls.insertStyle(style)
        layer.insertClass(cls)

    interval = (maxvalue - minvalue)
    for prev_item, next_item in pairwise_iterative(colors):
        prev_perc, prev_color = prev_item
        next_perc, next_color = next_item

        cls = ms.classObj()
        cls.setExpression("([pixel] > %s AND [pixel] < %s)" % (
            (minvalue + prev_perc * interval),
            (minvalue + next_perc * interval)
        ))
        cls.group = name

        style = ms.styleObj()
        style.mincolor = ms.colorObj(*prev_color)
        style.maxcolor = ms.colorObj(*next_color)
        style.minvalue = minvalue + prev_perc * interval
        style.maxvalue = minvalue + next_perc * interval
        style.rangeitem = ""
        cls.insertStyle(style)
        layer.insertClass(cls)

    # Create style for values above range, but make sure to not collide with
    # nil-values
    if high_nil_values:
        high_nil = min(high_nil_values)
        cls = ms.classObj()
        cls.setExpression(
            "([pixel] > %s AND [pixel] < %s)" % (maxvalue, high_nil)
        )
        cls.group = name
        style = ms.styleObj()
        style.color = ms.colorObj(*colors[0][1])
        cls.insertStyle(style)
        layer.insertClass(cls)
    else:
        cls = ms.classObj()
        cls.setExpression("([pixel] > %s)" % (maxvalue))
        cls.group = name
        style = ms.styleObj()
        style.color = ms.colorObj(*colors[-1][1])
        cls.insertStyle(style)
        layer.insertClass(cls)


def _get_range(field, range_=None):
    """ Gets the numeric range of a field
    """
    if range_:
        return tuple(range_)
    elif len(field.allowed_values) == 1:
        return field.allowed_values[0]
    elif field.data_type_range:
        return field.data_type_range
    return gdal.GDT_NUMERIC_LIMITS.get(field.data_type) or (0, 255)

# ------------------------------------------------------------------------------
# Layer factories
# ------------------------------------------------------------------------------


LAYER_FACTORIES = None


def _setup_factories():
    global LAYER_FACTORIES

    specifiers = getattr(
        settings, 'EOXS_MAPSERVER_LAYER_FACTORIES',
        DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES
    )
    LAYER_FACTORIES = [
        import_string(specifier)
        for specifier in specifiers
    ]


def get_layer_factories():
    if LAYER_FACTORIES is None:
        _setup_factories()
    return LAYER_FACTORIES
