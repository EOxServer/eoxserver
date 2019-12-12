#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

from os.path import splitext
try:
    from itertools import chain, izip
except ImportError :
    from itertools import chain
    izip = zip
import numpy
import logging

from django.contrib.gis.geos import (
    GEOSGeometry, MultiPolygon, Polygon, LinearRing
)

from eoxserver.contrib import gdal, ogr, osr
from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.processing.preprocessing.util import (
    create_mem, create_mem_copy, copy_projection, cleanup_temp
)

from eoxserver.processing.preprocessing.optimization import (
    BandSelectionOptimization, ColorIndexOptimization, NoDataValueOptimization,
    OverviewOptimization, ReprojectionOptimization, AlphaBandOptimization
)


logger = logging.getLogger(__name__)


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


class NativeMetadataFormatEncoder(XMLEncoder):
    """
    Encodes EO Coverage metadata
    """

    def encodeMetadata(self, eoid, begin_time, end_time, polygon):
        return self._makeElement("", "Metadata", [
            ("", "EOID", eoid),
            ("", "BeginTime", begin_time),
            ("", "EndTime", end_time),
            ("", "Footprint", [
                ("", "Polygon", [
                    ("", "Exterior", self._posListToString(polygon[0]))
                ] + [
                    tuple("", "Interior", self._posListToString(interior))
                    for interior in polygon[1:]
                ])
            ])
        ])

    def _posListToString(self, ring):
        return " ".join(map(str, ring))

# enum for bandmode
RGB, RGBA, ORIG_BANDS = range(3)

#===============================================================================
# Pre-Processors
#===============================================================================


class PreProcessor(object):
    """
    """

    force = False

    def __init__(self, format_selection, overviews=True, crs=None, bands=None,
                 bandmode=RGB, footprint_alpha=False,
                 color_index=False, palette_file=None, no_data_value=None,
                 overview_resampling=None, overview_levels=None,
                 overview_minsize=None, radiometric_interval_min=None,
                 radiometric_interval_max=None, simplification_factor=None,
                 temporary_directory=None):

        self.format_selection = format_selection
        self.overviews = overviews
        self.overview_resampling = overview_resampling
        self.overview_levels = overview_levels
        self.overview_minsize = overview_minsize

        self.crs = crs

        self.bands = bands
        self.bandmode = bandmode
        self.footprint_alpha = footprint_alpha
        self.color_index = color_index
        self.palette_file = palette_file
        self.no_data_value = no_data_value
        self.radiometric_interval_min = radiometric_interval_min
        self.radiometric_interval_max = radiometric_interval_max

        if simplification_factor is not None:
            self.simplification_factor = simplification_factor
        else:
            # default 2 * resolution == 2 pixels
            self.simplification_factor = 2

        self.temporary_directory = temporary_directory

    def process(self, input_filename, output_filename,
                geo_reference=None, generate_metadata=True):

        # open the dataset and create an In-Memory Dataset as copy
        # to perform optimizations
        ds = create_mem_copy(gdal.Open(input_filename))

        gt = ds.GetGeoTransform()
        footprint_wkt = None

        if not geo_reference:
            if gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                # TODO: maybe use a better check
                raise ValueError("No geospatial reference for unreferenced "
                                 "dataset given.")
        else:
            logger.debug("Applying geo reference '%s'."
                         % type(geo_reference).__name__)
            ds, footprint_wkt = geo_reference.apply(ds)

        # apply optimizations
        for optimization in self.get_optimizations(ds):
            logger.debug("Applying optimization '%s'."
                         % type(optimization).__name__)

            try:
                new_ds = optimization(ds)

                if new_ds is not ds:
                    # cleanup afterwards
                    cleanup_temp(ds)
                    ds = new_ds
            except:
                cleanup_temp(ds)
                raise

        # generate the footprint from the dataset
        if not footprint_wkt:
            logger.debug("Generating footprint.")
            footprint_wkt = self._generate_footprint_wkt(ds)
        # check that footprint is inside of extent of generated image
        # regenerate otherwise
        else:
            tmp_extent = getExtentFromRectifiedDS(ds)
            tmp_bbox = Polygon.from_bbox((tmp_extent[0], tmp_extent[1],
                                          tmp_extent[2], tmp_extent[3]))
            tmp_footprint = GEOSGeometry(footprint_wkt)
            if not tmp_bbox.contains(tmp_footprint):
                footprint_wkt = tmp_footprint.intersection(tmp_bbox).wkt

        if self.footprint_alpha:
            logger.debug("Applying optimization 'AlphaBandOptimization'.")
            opt = AlphaBandOptimization()
            opt(ds, footprint_wkt)

        output_filename = self.generate_filename(output_filename)

        logger.debug("Writing file to disc using options: %s."
                     % ", ".join(self.format_selection.creation_options))

        logger.debug("Metadata tags to be written: %s"
                     % ", ".join(ds.GetMetadata_List("") or []))

        # save the file to the disc
        driver = gdal.GetDriverByName(self.format_selection.driver_name)
        ds = driver.CreateCopy(output_filename, ds,
                               options=self.format_selection.creation_options)

        for optimization in self.get_post_optimizations(ds):
            logger.debug("Applying post-optimization '%s'."
                         % type(optimization).__name__)
            optimization(ds)

        # generate metadata if requested
        footprint = None
        if generate_metadata:
            normalized_space = Polygon.from_bbox((-180, -90, 180, 90))
            non_normalized_space = Polygon.from_bbox((180, -90, 360, 90))

            footprint = GEOSGeometry(footprint_wkt)
            #.intersection(normalized_space)
            outer = non_normalized_space.intersection(footprint)

            if len(outer):
                footprint = MultiPolygon(
                    *map(lambda p:
                        Polygon(*map(lambda ls:
                            LinearRing(*map(lambda point:
                                (point[0] - 360, point[1]), ls.coords
                            )), tuple(p)
                        )), (outer,)
                    )
                ).union(normalized_space.intersection(footprint))
            else:
                if isinstance(footprint, Polygon):
                    footprint = MultiPolygon(footprint)

            logger.info("Calculated Footprint: '%s'" % footprint.wkt)

            # use the provided footprint
            #geom = OGRGeometry(footprint_wkt)
            #exterior = []
            #for x, y in geom.exterior_ring.tuple:
            #    exterior.append(y); exterior.append(x)

            #polygon = [exterior]
        num_bands = ds.RasterCount

        # finally close the dataset and write it to the disc
        ds = None

        return PreProcessResult(output_filename, footprint, num_bands)

    def generate_filename(self, filename):
        """ Adjust the filename with the correct extension. """
        base_filename, _ = splitext(filename)
        return base_filename + self.format_selection.extension

    def _generate_footprint_wkt(self, ds):
        """ Generate a footprint from a raster, using black/no-data as exclusion
        """

        # create an empty boolean array initialized as 'False' to store where
        # values exist as a mask array.
        nodata_map = numpy.zeros((ds.RasterYSize, ds.RasterXSize),
                                 dtype=numpy.bool)

        for idx in range(1, ds.RasterCount + 1):
            band = ds.GetRasterBand(idx)
            raster_data = band.ReadAsArray()
            nodata = band.GetNoDataValue()

            if nodata is None:
                nodata = 0

            # apply the output to the map
            nodata_map |= (raster_data != nodata)

        # create a temporary in-memory dataset and write the nodata mask
        # into its single band
        tmp_ds = create_mem(ds.RasterXSize + 2, ds.RasterYSize + 2, 1,
                            gdal.GDT_Byte)
        copy_projection(ds, tmp_ds)
        tmp_band = tmp_ds.GetRasterBand(1)
        tmp_band.WriteArray(nodata_map.astype(numpy.uint8))

        # create an OGR in memory layer to hold the created polygon
        sr = osr.SpatialReference()
        sr.ImportFromWkt(ds.GetProjectionRef())
        ogr_ds = ogr.GetDriverByName('Memory').CreateDataSource('out')
        layer = ogr_ds.CreateLayer('poly', sr.sr, ogr.wkbPolygon)
        fd = ogr.FieldDefn('DN', ogr.OFTInteger)
        layer.CreateField(fd)

        # polygonize the mask band and store the result in the OGR layer
        gdal.Polygonize(tmp_band, tmp_band, layer, 0)

        if layer.GetFeatureCount() > 1:
            # if there is more than one polygon, compute the minimum
            # bounding polygon
            geometry = ogr.Geometry(ogr.wkbPolygon)
            while True:
                feature = layer.GetNextFeature()
                if not feature:
                    break
                geometry = geometry.Union(feature.GetGeometryRef())

            # TODO: improve this for a better minimum bounding polygon
            geometry = geometry.ConvexHull()

        elif layer.GetFeatureCount() < 1:
            # there was an error during polygonization
            raise RuntimeError("Error during polygonization. No feature "
                               "obtained.")
        else:
            # obtain geometry from the first (and only) layer
            feature = layer.GetNextFeature()
            geometry = feature.GetGeometryRef()

        if geometry.GetGeometryType() != ogr.wkbPolygon:
            raise RuntimeError("Error during polygonization. Wrong geometry "
                               "type: %s" % ogr.GeometryTypeToName(
                                    geometry.GetGeometryType()))

        # check if reprojection to latlon is necessary
        if not sr.IsGeographic():
            dst_sr = osr.SpatialReference()
            dst_sr.ImportFromEPSG(4326)
            try:
                geometry.TransformTo(dst_sr.sr)
            except RuntimeError:
                geometry.Transform(osr.CoordinateTransformation(sr.sr, dst_sr.sr))
        
        gt = ds.GetGeoTransform()
        resolution = min(abs(gt[1]), abs(gt[5]))

        simplification_value = self.simplification_factor * resolution

        # simplify the polygon. the tolerance value is *really* vague
        try:
            # SimplifyPreserveTopology() available since OGR 1.9.0
            geometry = geometry.SimplifyPreserveTopology(simplification_value)
        except AttributeError:
            # use GeoDjango bindings if OGR is too old
            geometry = ogr.CreateGeometryFromWkt(
                GEOSGeometry(geometry.ExportToWkt()).simplify(
                    simplification_value, True
                ).wkt
            )

        return geometry.ExportToWkt()


class WMSPreProcessor(PreProcessor):
    """

        >>> prep = WMSPreProcessor(...)
        >>> prep.process(input_filename, output_filename, generate_metadata)
    """

    def get_optimizations(self, ds):
        if self.no_data_value is not None:
            yield NoDataValueOptimization(self.no_data_value)

        if self.crs:
            yield ReprojectionOptimization(self.crs, self.temporary_directory)

        if self.bandmode not in (RGB, RGBA, ORIG_BANDS):
            raise ValueError

        if self.radiometric_interval_min is not None:
            rad_min = self.radiometric_interval_min
        else:
            rad_min = "min"
        if self.radiometric_interval_max is not None:
            rad_max = self.radiometric_interval_max
        else:
            rad_max = "max"

        # if RGB is requested, use the given bands or the first 3 bands as RGB
        if self.bandmode == RGB:
            if self.bands and len(self.bands) != 3:
                raise ValueError("Wrong number of bands given. Expected 3, got "
                                 "%d." % len(self.bands))

            if ds.RasterCount == 1:
                yield BandSelectionOptimization(
                    self.bands or [(1, rad_min, rad_max),
                                   (1, rad_min, rad_max),
                                   (1, rad_min, rad_max)],
                    temporary_directory=self.temporary_directory)
            else:
                yield BandSelectionOptimization(
                    self.bands or [(1, rad_min, rad_max),
                                   (2, rad_min, rad_max),
                                   (3, rad_min, rad_max)],
                    temporary_directory=self.temporary_directory)

        # if RGBA is requested, use the given bands or the first 4 bands as RGBA
        elif self.bandmode == RGBA:
            if self.bands and len(self.bands) != 4:
                raise ValueError("Wrong number of bands given. Expected 4, got "
                                 "%d." % len(self.bands))
            if ds.RasterCount == 1:
                yield BandSelectionOptimization(
                    self.bands or [(1, rad_min, rad_max),
                                   (1, rad_min, rad_max),
                                   (1, rad_min, rad_max),
                                   (0, 0, 0)],
                    temporary_directory=self.temporary_directory)
            else:
                yield BandSelectionOptimization(
                    self.bands or [(1, rad_min, rad_max),
                                   (2, rad_min, rad_max),
                                   (3, rad_min, rad_max),
                                   (4, rad_min, rad_max)],
                    temporary_directory=self.temporary_directory)

        # when band mode is set to original bands, don't use this optimization
        elif self.bandmode == ORIG_BANDS:
            if self.bands:
                raise ValueError("Bandmode is set to 'original', but bands are "
                                 "given.")

        else:
            raise ValueError("Illegal bandmode given.")

        if self.color_index:
            yield ColorIndexOptimization(
                self.palette_file, self.temporary_directory
            )

    def get_post_optimizations(self, ds):
        if self.overviews:
            yield OverviewOptimization(self.overview_resampling,
                                       self.overview_levels,
                                       self.overview_minsize)


#===============================================================================
# PreProcess result
#===============================================================================

class PreProcessResult(object):
    """ Result storage for preprocessed datasets. """
    def __init__(self, output_filename, footprint, num_bands):
        self.output_filename = output_filename
        self._footprint = footprint
        self.num_bands = num_bands

    @property
    def footprint_raw(self):
        pass  # TODO: return as a list of tuples

    @property
    def footprint_wkt(self):
        """ Returns the stored footprint as WKT."""
        return self.footprint_geom.wkt

    @property
    def footprint_geom(self):
        """ Returns the polygon as a GEOSGeometry. """
        #return Polygon([LinearRing([
        #    Point(x, y) for y, x in pairwise(ring)
        #]) for ring in self._footprint][0])
        return self._footprint
