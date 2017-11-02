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

from os.path import join
from uuid import uuid4

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.core.util.iteratortools import pairwise_iterative
from eoxserver.contrib import mapserver as ms
from eoxserver.contrib import vsi, vrt, gdal, osr
from eoxserver.render.browse.objects import Browse, GeneratedBrowse
from eoxserver.render.map.objects import (
    CoverageLayer, MosaicLayer, BrowseLayer, OutlinedBrowseLayer,
    MaskLayer, MaskedBrowseLayer, OutlinesLayer,  # CoverageSetsLayer
)
from eoxserver.render.mapserver.config import (
    DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES,
)
from eoxserver.render.colors import BASE_COLORS, COLOR_SCALES, OFFSITE_COLORS
from eoxserver.resources.coverages import crss
from eoxserver.processing.gdal import reftools


class FilenameGenerator(object):
    """ Utility class to generate filenames after a certain pattern (template)
        and to keep a list for later cleanup.
    """
    def __init__(self, template):
        """ Create a new :class:`FilenameGenerator` from a given template
            :param template: the template string used to construct the filenames
                             from. Uses the ``.format()`` style language. Keys
                             are ``index``, ``uuid`` and ``extension``.
        """
        self._template = template
        self._filenames = []

    def generate(self, extension=None):
        """ Generate and store a new filename using the specified template. An
            optional ``extension`` can be passed, when used in the template.
        """
        filename = self._template.format(
            index=len(self._filenames),
            uuid=uuid4().hex,
            extension=extension,
        )
        self._filenames.append(filename)
        return filename

    @property
    def filenames(self):
        """ Get a list of all generated filenames.
        """
        return self._filenames


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
            assert len(bands) in (1, 3, 4)
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
                              style=None, range_=None):
        """ Creates a mapserver layer object for the given coverage
        """
        layer_obj = _create_raster_layer_obj(
            map_obj,
            coverage.extent if not coverage.grid.is_referenceable else None,
            coverage.grid.spatial_reference
        )

        field_locations = [
            (field, coverage.get_location_for_field(field))
            for field in fields
        ]

        # layer_obj.setProcessingKey("SCALE", "AUTO")
        layer_obj.setProcessingKey("CLOSE_CONNECTION", "CLOSE")

        # TODO: apply subsets in time/elevation dims

        num_locations = len(set(field_locations))
        if num_locations == 1:
            if not coverage.grid.is_referenceable:
                layer_obj.data = field_locations[0][1].path
            else:
                vrt_path = join("/vsimem", uuid4().hex)

                # TODO: calculate map resolution

                e = map_obj.extent

                resx = (e.maxx - e.minx) / map_obj.width
                resy = (e.maxy - e.miny) / map_obj.height

                srid = osr.SpatialReference(map_obj.getProjection()).srid

                reftools.create_rectified_vrt(
                    field_locations[0][1].path, vrt_path, order=1, max_error=10,
                    resolution=(resx, -resy), srid=srid
                )
                layer_obj.data = vrt_path

                layer_obj.setMetaData("eoxs_ref_data", vrt_path)

            layer_obj.setProcessingKey("BANDS", ",".join([
                str(coverage.get_band_index_for_field(field))
                for field in fields
            ]))

        elif num_locations > 1:
            layer_obj.data = _build_vrt(coverage.size, field_locations)

        # make a color-scaled layer
        if len(fields) == 1:
            field = fields[0]
            range_ = _get_range(field, range_)

            _create_raster_style(
                style or "blackwhite", layer_obj, range_[0], range_[1], [
                    nil_value[0] for nil_value in field.nil_values
                ]
            )
        elif len(fields) in (3, 4):
            for i, field in enumerate(fields, start=1):
                range_ = _get_range(field, range_)
                layer_obj.setProcessingKey("SCALE_%d" % i, "%s,%s" % range_)
                layer_obj.offsite = ms.colorObj(0, 0, 0)

        else:
            raise Exception("Too many bands specified")

        return layer_obj

    def destroy_coverage_layer(self, layer_obj):
        path = layer_obj.data
        if path.startswith("/vsimem"):
            vsi.remove(path)

        try:
            ref_data = layer_obj.getMetaData("eoxs_ref_data")
            if ref_data and ref_data.startswith("/vsimem"):
                vsi.remove(ref_data)
        except:
            pass


class CoverageLayerFactory(CoverageLayerFactoryMixIn, BaseMapServerLayerFactory):
    handled_layer_types = [CoverageLayer]

    def create(self, map_obj, layer):
        coverage = layer.coverage
        fields = self.get_fields(
            coverage.range_type, layer.bands, layer.wavelengths
        )
        return self.create_coverage_layer(
            map_obj, coverage, fields, layer.style, layer.range
        )

    def destroy(self, map_obj, layer, data):
        self.destroy_coverage_layer(data)


class MosaicLayerFactory(CoverageLayerFactoryMixIn, BaseMapServerLayerFactory):
    handled_layer_types = [MosaicLayer]

    def create(self, map_obj, layer):
        mosaic = layer.mosaic
        fields = self.get_fields(
            mosaic.range_type, layer.bands, layer.wavelengths
        )
        return [
            self.create_coverage_layer(
                map_obj, coverage, fields, layer.style, layer.range
            )
            for coverage in layer.coverages
        ]

    def destroy(self, map_obj, layer, data):
        for layer_obj in data:
            self.destroy_coverage_layer(layer_obj)

# TODO: combine BrowseLayerFactory with OutlinedBrowseLayerFactory, as they are
# very similar


class BrowseLayerFactory(CoverageLayerFactoryMixIn, BaseMapServerLayerFactory):
    handled_layer_types = [BrowseLayer]

    def create(self, map_obj, layer):
        filename_generator = FilenameGenerator('/vsimem/{uuid}.vrt')
        group_name = layer.name
        range_ = layer.range
        style = layer.style

        for browse in layer.browses:
            layer_obj = _create_raster_layer_obj(
                map_obj, browse.extent, browse.spatial_reference
            )
            layer_obj.group = group_name

            if isinstance(browse, GeneratedBrowse):
                fields = [
                    coverages[0].range_type.get_field(field)
                    for field, coverages in browse._fields_and_coverages
                ]

                layer_obj.data = _generate_browse(
                    browse._fields_and_coverages, filename_generator
                )

                if len(fields) == 1:
                    field = fields[0]
                    range_ = _get_range(field, range_)

                    _create_raster_style(
                        style or "blackwhite", layer_obj, range_[0], range_[1], [
                            nil_value[0] for nil_value in field.nil_values
                        ]
                    )

                else:
                    for i, field in enumerate(fields, start=1):
                        layer_obj.setProcessingKey("SCALE_%d" % i,
                            "%s,%s" % _get_range(field, range_)
                        )

            elif isinstance(browse, Browse):
                layer_obj.data = browse.filename

        return filename_generator

    def destroy(self, map_obj, layer, filename_generator):
        # cleanup temporary files
        for filename in filename_generator.filenames:
            vsi.unlink(filename)


class OutlinedBrowseLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [OutlinedBrowseLayer]

    def create(self, map_obj, layer):
        filename_generator = FilenameGenerator('/vsimem/{uuid}.vrt')
        group_name = layer.name
        range_ = layer.range
        style = layer.style

        raster_style = style if style and style in COLOR_SCALES else "blackwhite"
        vector_style = style if style and style in BASE_COLORS else "red"

        for browse in layer.browses:
            # create the browse layer itself
            browse_layer_obj = _create_raster_layer_obj(
                map_obj, browse.extent, browse.spatial_reference
            )
            browse_layer_obj.group = group_name

            if isinstance(browse, GeneratedBrowse):
                fields = [
                    coverages[0].range_type.get_field(field)
                    for field, coverages in browse._fields_and_coverages
                ]

                browse_layer_obj.data = _generate_browse(
                    browse._fields_and_coverages, filename_generator
                )

                if len(fields) == 1:
                    field = fields[0]
                    range_ = _get_range(field, range_)

                    _create_raster_style(
                        raster_style, browse_layer_obj, range_[0], range_[1], [
                            nil_value[0] for nil_value in field.nil_values
                        ]
                    )

                else:
                    for i, field in enumerate(fields, start=1):
                        browse_layer_obj.setProcessingKey("SCALE_%d" % i,
                            "%s,%s" % _get_range(field, range_)
                        )

            elif isinstance(browse, Browse):
                browse_layer_obj.data = browse.filename

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
        for mask in layer.masks:
            if mask.geometry:
                mask_geom = mask.geometry
            elif mask.filename:
                mask_geom = mask.load_geometry()
            else:
                continue

            shape_obj = ms.shapeObj.fromWKT(mask_geom.wkt)
            layer_obj.addFeature(shape_obj)

        layer_obj.insertClass(
            _create_geometry_class(layer.style or 'red', fill=True)
        )


class MaskedBrowseLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [MaskedBrowseLayer]

    def create(self, map_obj, layer):
        group_name = layer.name
        for masked_browse in layer.masked_browses:
            browse = masked_browse.browse
            mask = masked_browse.mask
            mask_name = 'mask__%d' % id(masked_browse)

            # create mapserver layers for the mask
            mask_layer_obj = _create_polygon_layer(map_obj)
            mask_layer_obj.status = ms.MS_OFF
            mask_layer_obj.insertClass(
                _create_geometry_class("black", "white", fill=True)
            )

            if mask.geometry:
                mask_geom = mask.geometry
            elif mask.filename:
                mask_geom = mask.load_geometry()
            else:
                mask_geom = None

            outline = browse.footprint
            if mask_geom:
                outline = outline - mask_geom

            shape_obj = ms.shapeObj.fromWKT(outline.wkt)
            mask_layer_obj.addFeature(shape_obj)

            mask_layer_obj.name = mask_name

            # set up the mapserver layers required for the browses
            browse_layer_obj = _create_raster_layer_obj(
                map_obj, browse.extent,
                browse.spatial_reference
            )
            browse_layer_obj.group = group_name
            browse_layer_obj.data = browse.filename
            browse_layer_obj.mask = mask_name


class OutlinesLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [OutlinesLayer]

    def create(self, map_obj, layer):
        layer_obj = _create_polygon_layer(map_obj)
        for footprint in layer.footprints:
            shape_obj = ms.shapeObj.fromWKT(footprint.wkt)
            layer_obj.addFeature(shape_obj)

        class_obj = _create_geometry_class(layer.style or 'red')
        layer_obj.insertClass(class_obj)


# ------------------------------------------------------------------------------
# utils
# ------------------------------------------------------------------------------


def _create_raster_layer_obj(map_obj, extent, sr, resample='AVERAGE'):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_RASTER
    layer_obj.status = ms.MS_ON

    layer_obj.offsite = ms.colorObj(0, 0, 0)

    if extent:
        layer_obj.setMetaData("wms_extent", "%f %f %f %f" % extent)
        layer_obj.setExtent(*extent)

        if sr.srid is not None:
            short_epsg = "EPSG:%d" % sr.srid
            layer_obj.setMetaData("ows_srs", short_epsg)
            layer_obj.setMetaData("wms_srs", short_epsg)

    layer_obj.setProjection(sr.proj)
    layer_obj.setProcessingKey('RESAMPLE', resample)

    return layer_obj


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


def _create_geometry_class(color_name, background_color_name=None, fill=False):
    cls_obj = ms.classObj()
    style_obj = ms.styleObj()

    try:
        color = ms.colorObj(*BASE_COLORS[color_name])
    except KeyError:
        raise  # TODO

    style_obj.outlinecolor = color

    if fill:
        style_obj.color = color

    if background_color_name:
        style_obj.backgroundcolor = ms.colorObj(
            *BASE_COLORS[background_color_name]
        )

    cls_obj.insertStyle(style_obj)
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


def _generate_browse(fields_and_coverages, generator):
    """ Produce a temporary VRT file describing how transformation of the
        coverages to browses.
    """
    band_filenames = []
    for field, coverages in fields_and_coverages:
        selected_filenames = []
        for coverage in coverages:
            orig_filename = coverage.get_location_for_field(field).path
            orig_band_index = coverage.get_band_index_for_field(field)

            # only select if band count for the dataset > 1
            ds = gdal.OpenShared(orig_filename)
            if ds.RasterCount == 1:
                selected_filename = orig_filename
            else:
                selected_filename = generator.generate()
                vrt.select_bands(
                    orig_filename, [orig_band_index], selected_filename
                )

            selected_filenames.append(selected_filename)

        if len(selected_filenames) == 1:
            band_filename = selected_filenames[0]
        else:
            band_filename = generator.generate()
            vrt.mosaic(selected_filenames, band_filename)

        band_filenames.append(band_filename)

    if len(band_filenames) == 1:
        return band_filenames[0]

    else:
        stacked_filename = generator.generate()
        vrt.stack_bands(band_filenames, stacked_filename)
        return stacked_filename


def _create_raster_style(name, layer, minvalue=0, maxvalue=255, nil_values=None):
    colors = COLOR_SCALES[name]

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
            style.rangeitem = ""
            cls.insertStyle(style)
            layer.insertClass(cls)

    # Create style for values below range
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
        cls.setExpression("([pixel] >= %s AND [pixel] < %s)" % (
            (minvalue + prev_perc * interval), (minvalue + next_perc * interval)
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

    # Create style for values above range
    cls = ms.classObj()
    cls.setExpression("([pixel] > %s)" % (maxvalue))
    cls.group = name
    style = ms.styleObj()
    style.color = ms.colorObj(*colors[-1][1])
    cls.insertStyle(style)
    layer.insertClass(cls)
    layer.classgroup = name


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
