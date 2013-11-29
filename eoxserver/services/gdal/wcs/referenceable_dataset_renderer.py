#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from os.path import splitext, abspath
from datetime import datetime
from uuid import uuid4

from eoxserver.core import Component, implements
from eoxserver.core.util.rect import Rect
from eoxserver.backends.access import connect
from eoxserver.contrib import gdal, osr
from eoxserver.contrib.vrt import VRTBuilder
from eoxserver.resources.coverages import models
from eoxserver.services.ows.version import Version
from eoxserver.services.subset import Subsets
from eoxserver.services.result import ResultFile, ResultBuffer
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder


class GDALReferenceableDatasetRenderer(Component):
    implements(WCSCoverageRendererInterface)

    versions = (Version(2, 0),)

    def supports(self, params):
        return (
            issubclass(params.coverage.real_type, models.ReferenceableDataset)
            and params.version in self.versions
        )


    def render(self, params):
        # get the requested coverage, data items and range type.
        coverage = params.coverage
        data_items = coverage.data_items.filter(semantic__startswith="bands")
        range_type = coverage.range_type

        subsets = Subsets(params.subsets)

        # GDAL source dataset. Either a single file dataset or a composed VRT 
        # dataset.
        src_ds = self.get_source_dataset(
            coverage, data_items, range_type
        )

        # retrieve area of interest of the source image according to given 
        # subsets
        src_rect = self.get_source_image_rect(src_ds, subsets)

        # deduct "native" format of the source image
        native_format = data_items[0].format if len(data_items) == 1 else None

        # get the requested image format, which defaults to the native format
        # if available
        format = params.format or native_format

        if not format:
            raise Exception("No format specified.")


        # perform subsetting either with or without rangesubsetting
        if params.rangesubset:
            subsetted_ds = self.perform_range_subset(
                src_ds, range_type, subset_bands, src_rect, 
            )

        else:
            subsetted_ds = self.perform_subset(
                src_ds, src_rect
            )

        # encode the processed dataset and save it to the filesystem
        out_ds, out_driver = self.encode(subsetted_ds, format)

        driver_metadata = out_driver.GetMetadata_Dict()
        mime_type = driver_metadata.get("DMD_MIMETYPE")

        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename_base = "%s_%s" % (coverage.identifier, time_stamp)

        result_set = [
            ResultFile(
                path, mime_type, filename_base + splitext(path)[1],
                ("cid:coverage/%s" % coverage.identifier) if i == 0 else None
            ) for i, path in enumerate(out_ds.GetFileList())
        ]

        if params.mediatype.startswith("multipart"):
            reference = result_set[0].identifier
            
            if subsets.has_x and subsets.has_y:
                footprint = GEOSGeometry(get_footprint_wkt(dst_path))
                encoder_subset = (
                    subsets.xy_srid, src_rect.size, extent, footprint
                )
            else:
                encoder_subset = None

            encoder = WCS20EOXMLEncoder()
            content = encoder.serialize(
                encoder.encode_referenceable_dataset(
                    coverage, range_type, reference, mime_type, encoder_subset
                )
            )
            result_set.insert(0, ResultBuffer(content, encoder.content_type))

        return result_set


    def get_source_dataset(self, coverage, data_items, range_type):
        if len(data_items) == 1:
            return gdal.OpenShared(abspath(connect(data_items[0])))
        else:
            vrt = VRTBuilder(
                coverage.size_x, coverage.size_y,
                vrt_filename=temp_vsimem_filename()
            )

            # sort in ascending order according to semantic
            data_items = sorted(data_items, key=(lambda d: d.semantic))

            gcps = []
            compound_index = 0
            for data_item in data_items:
                path = abspath(connect(data_item))

                # iterate over all bands of the data item
                for set_index, item_index in self._data_item_band_indices(data_item):
                    if set_index != compound_index + 1: 
                        raise ValueError
                    compound_index = set_index

                    band = range_type[set_index]
                    vrt.add_band(band.data_type)
                    vrt.add_simple_source(
                        set_index, path, item_index
                    )

            return vrt.dataset


    def get_source_image_rect(self, dataset, subsets):
        size_x, size_y = dataset.RasterXSize, dataset.RasterYSize
        image_rect = Rect(0, 0, size_x, size_y)

        if not subsets:
            subset_rect = image_rect

        # pixel subset
        elif subsets.xy_srid is None: # means "imageCRS"
            minx, miny, maxx, maxy = subsets.xy_bbox

            minx = minx if minx is not None else image_rect.offset_x
            miny = miny if miny is not None else image_rect.offset_y
            maxx = maxx if maxx is not None else image_rect.upper_x
            maxy = maxy if maxy is not None else image_rect.upper_y

            subset_rect = Rect(minx, miny, maxx-minx, maxy-miny)

        else:
            vrt = VRTBuilder(size_x, size_y)
            vrt.copy_gcps(dataset)

            # subset in geographical coordinates
            subset_rect = rect_from_subset(
                vrt.dataset, subsets.xy_srid, 
                subsets.minx, subsets.miny, subsets.maxx, subsets.maxy
            )

        # check whether or not the subsets intersect with the image
        if not image_rect.intersects(subset_rect):
            raise Exception("Subset outside coverage extent.") # TODO: correct exception

        # in case the input and output rects are the same, return None to 
        # indicate this
        #if image_rect == subset_rect:
        #    return None

        return image_rect & subset_rect


    def perform_range_subset(self, src_ds, range_type, subset_bands, 
                             subset_rect):

        vrt = VRTBuilder(src_ds.RasterXSize, src_ds.RasterYSize)
        dst_rect = Rect(0, 0, src_ds.RasterXSize, src_ds.RasterYSize)

        input_bands = list(range_type)
        for index, subset_band in enumerate(subset_bands, start=1):
            if isinstance(subset_band, int):
                if subset_band > 0:
                    subset_band = len(range_type) + subset_band
            else:
                subset_band = index_of(input_bands,
                    lambda band: (
                        band.name == subset_band 
                        or band.identifier == subset_band
                    )
                )
                if subset_band is None:
                    raise ValueError("Invalid range subset.")

            # prepare and add a simple source for the band
            input_band = input_bands[subset_band]
            vrt.add_band(input_band.data_type)
            vrt.add_simple_source(
                index, src_ds, subset_band, subset_rect, dst_rect
            )

        vrt.copy_metadata(src_ds)
        vrt.copy_gcps(src_ds, subset_rect)

        return vrt.dataset

    def perform_subset(self, src_ds, subset_rect):
        vrt = VRTBuilder(src_ds.RasterXSize, src_ds.RasterYSize)
        dst_rect = Rect(0, 0, src_ds.RasterXSize, src_ds.RasterYSize)

        for index in xrange(1, src_ds.RasterCount + 1):
            src_band = src_ds.GetRasterBand(index)
            vrt.add_band(src_band.DataType)
            vrt.add_simple_source(index, src_ds, index, subset_rect, dst_rect)

        vrt.copy_metadata(src_ds)
        vrt.copy_gcps(src_ds, subset_rect)

        return vrt.dataset

    def encode(self, dataset, format):
        #format, options = None
        options = {}
        options = [
            ("%s=%s" % key, value) for key, value in (options or {}).items()
        ]

        path = "/tmp/%s" % uuid4().hex
        out_driver = gdal.GetDriverByName("GTiff")
        return out_driver.CreateCopy(path, dataset, True, options), out_driver


def index_of(iterable, predicate, default=None, start=1):
    for i, item in enumerate(iterable, start):
        if predicate(item):
            return i
    return default


def temp_vsimem_filename():
    return "/vsimem/%s" % uuid4().hex