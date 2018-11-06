#-------------------------------------------------------------------------------
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


from os.path import join
from datetime import datetime
from uuid import uuid4
import logging

from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config
from eoxserver.core.util.rect import Rect
from eoxserver.contrib import vsi, vrt, gdal
from eoxserver.contrib.vrt import VRTBuilder
from eoxserver.services.ows.version import Version
from eoxserver.services.result import ResultFile, ResultBuffer
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.exceptions import (
    RenderException, OperationNotSupportedException
)
from eoxserver.processing.gdal import reftools


logger = logging.getLogger(__name__)


def get_subdataset_path(ds, identifier):
    for path, _ in ds.GetSubDatasets():
        if path.endswith(identifier):
            return path
    raise KeyError(identifier)


class GDALReferenceableDatasetRenderer(object):

    versions = (Version(2, 1),)

    def supports(self, params):
        return (
            params.version in self.versions and
            params.coverage.grid.is_referenceable
        )

    def render(self, params):
        # get the requested coverage, data items and range type.
        coverage = params.coverage
        data_items = coverage.arraydata_locations
        range_type = coverage.range_type

        subsets = params.subsets

        # GDAL source dataset. Either a single file dataset or a composed VRT
        # dataset.
        src_ds = self.get_source_dataset(
            coverage, data_items, range_type
        )

        # retrieve area of interest of the source image according to given
        # subsets
        src_rect, dst_rect = self.get_source_and_dest_rect(src_ds, subsets)

        # deduct "native" format of the source image
        native_format = data_items[0].format if len(data_items) == 1 else None

        # get the requested image format, which defaults to the native format
        # if available
        frmt = params.format or native_format

        if not frmt:
            raise RenderException("No format specified.", "format")

        # if params.scalefactor is not None or params.scales:
        #     raise RenderException(
        #         "ReferenceableDataset cannot be scaled.",
        #         "scalefactor" if params.scalefactor is not None else "scale"
        #     )

        # apply scaling
        scale_x = 1
        scale_y = 1
        if params.scalefactor:
            scale_x = params.scalefactor
            scale_y = params.scalefactor

        elif params.scales:
            scale_x_obj = next((s for s in params.scales if s.axis == "x"), None)
            scale_y_obj = next((s for s in params.scales if s.axis == "y"), None)

            if hasattr(scale_x_obj, 'scale'):
                scale_x = getattr(scale_x_obj, 'scale')
            if hasattr(scale_x_obj, 'size'):
                s_x = getattr(scale_x_obj, 'size')
                scale_x = float(s_x) / dst_rect.size_x

            if hasattr(scale_y_obj, 'scale'):
                scale_y = getattr(scale_y_obj, 'scale')
            if hasattr(scale_y_obj, 'size'):
                s_y = getattr(scale_y_obj, 'size')
                scale_y = float(s_y) / dst_rect.size_y

            # TODO: scaleextent

        if scale_x != 1 or scale_y != 1:
            dst_rect = Rect(
                dst_rect.offset_x * scale_x,
                dst_rect.offset_y * scale_y,
                int(round(dst_rect.size_x * scale_x)),
                int(round(dst_rect.size_y * scale_y)),
            )

        # check that we are within the configured max-size
        maxsize = WCSConfigReader(get_eoxserver_config()).maxsize
        if maxsize is not None:
            if maxsize < dst_rect.size_x or maxsize < dst_rect.size_y:
                raise RenderException(
                    "Requested image size %dpx x %dpx exceeds the allowed "
                    "limit maxsize=%dpx." % (
                        dst_rect.size_x, dst_rect.size_y, maxsize
                    ), "size"
                )

        # perform subsetting either with or without rangesubsetting
        subsetted_ds = self.perform_subset(
            src_ds, range_type, src_rect, dst_rect, params.rangesubset
        )

        # encode the processed dataset and save it to the filesystem
        out_ds, out_driver = self.encode(
            subsetted_ds, frmt, getattr(params, "encoding_params", {})
        )

        driver_metadata = out_driver.GetMetadata_Dict()
        mime_type = driver_metadata.get("DMD_MIMETYPE")
        extension = driver_metadata.get("DMD_EXTENSION")

        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename_base = "%s_%s" % (coverage.identifier, time_stamp)

        result_set = [
            ResultFile(
                path, mime_type, "%s.%s" % (filename_base, extension),
                ("cid:coverage/%s" % coverage.identifier) if i == 0 else None
            ) for i, path in enumerate(out_ds.GetFileList())
        ]

        if params.mediatype and params.mediatype.startswith("multipart"):
            reference = "cid:coverage/%s" % result_set[0].filename

            if subsets.has_x and subsets.has_y:
                footprint = GEOSGeometry(reftools.get_footprint_wkt(out_ds))
                if not subsets.srid:
                    extent = footprint.extent
                else:
                    extent = subsets.xy_bbox
                encoder_subset = (
                    subsets.srid, src_rect.size, extent, footprint
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

        # cleanup tmp dataset
        try:
            src_path = src_ds.GetFileList()[0]
            del src_ds
            if src_path.startswith('/vsimem'):
                vsi.unlink(src_path)
        except IndexError:
            pass

        return result_set

    def get_source_dataset(self, coverage, arraydata_locations, range_type):
        if len(arraydata_locations) == 1:
            ds = gdal.OpenShared(arraydata_locations[0].path)
            sds_paths = [
                v[0] for v in ds.GetSubDatasets()
            ]
            if sds_paths:
                path = join("/vsimem", uuid4().hex)

                vrt.gdalbuildvrt(path, [
                    get_subdataset_path(ds, field.identifier)
                    for field in range_type
                ], separate=True)

                # with vsi.open(path) as f:
                #     print f.read()

                return gdal.Open(path)

            return ds
        else:
            raise NotImplementedError
            # vrt_ = VRTBuilder(
            #     coverage.size_x, coverage.size_y,
            #     vrt_filename=temp_vsimem_filename()
            # )

            # compound_index = 0
            # for arraydata_location in arraydata_locations:
            #     path = arraydata_location

            #     # iterate over all bands of the data item
            #     indices = self._data_item_band_indices(arraydata_location)
            #     for set_index, item_index in indices:
            #         if set_index != compound_index + 1:
            #             raise ValueError
            #         compound_index = set_index

            #         band = range_type[set_index]
            #         vrt.add_band(band.data_type)
            #         vrt.add_simple_source(
            #             set_index, path, item_index
            #         )

            # return vrt.dataset

    def get_source_and_dest_rect(self, dataset, subsets):
        size_x, size_y = dataset.RasterXSize, dataset.RasterYSize
        image_rect = Rect(0, 0, size_x, size_y)

        if not subsets:
            subset_rect = image_rect

        # pixel subset
        elif subsets.srid is None:  # means "imageCRS"
            minx, miny, maxx, maxy = subsets.xy_bbox

            minx = int(minx) if minx is not None else image_rect.offset_x
            miny = int(miny) if miny is not None else image_rect.offset_y
            maxx = int(maxx) + 1 if maxx is not None else image_rect.upper_x
            maxy = int(maxy) + 1 if maxy is not None else image_rect.upper_y

            subset_rect = Rect(minx, miny, maxx - minx, maxy - miny)

        # subset in geographical coordinates
        else:
            vrt = VRTBuilder(*image_rect.size)
            vrt.copy_gcps(dataset)

            options = reftools.suggest_transformer(dataset)

            subset_rect = reftools.rect_from_subset(
                vrt.dataset, subsets.srid, *subsets.xy_bbox, **options
            )

        # check whether or not the subsets intersect with the image
        if not image_rect.intersects(subset_rect):
            raise RenderException("Subset outside coverage extent.", "subset")

        src_rect = subset_rect  # & image_rect # TODO: why no intersection??
        dst_rect = src_rect - subset_rect.offset

        return src_rect, dst_rect

    def perform_subset(self, src_ds, range_type, subset_rect, dst_rect,
                       rangesubset=None):

        vrt = VRTBuilder(*dst_rect.size)

        input_bands = list(range_type)

        # list of band indices/names. defaults to all bands
        if rangesubset:
            subset_bands = rangesubset.get_band_indices(range_type, 1)
        else:
            subset_bands = xrange(1, len(range_type) + 1)

        for dst_index, src_index in enumerate(subset_bands, start=1):
            input_band = input_bands[src_index-1]
            vrt.add_band(input_band.data_type)
            vrt.add_simple_source(
                dst_index, src_ds, src_index, subset_rect, dst_rect
            )

        vrt.copy_metadata(src_ds)
        vrt.copy_gcps(src_ds, subset_rect)

        return vrt.dataset

    def encode(self, dataset, frmt, encoding_params):
        options = ()
        if frmt == "image/tiff":
            options = _get_gtiff_options(**encoding_params)

        args = [
            ("%s=%s" % key, value) for key, value in options
        ]

        path = "/tmp/%s" % uuid4().hex
        out_driver = gdal.GetDriverByName("GTiff")
        out_ds = out_driver.CreateCopy(path, dataset, False, args)
        return out_ds, out_driver


def index_of(iterable, predicate, default=None, start=1):
    for i, item in enumerate(iterable, start):
        if predicate(item):
            return i
    return default


def temp_vsimem_filename():
    return "/vsimem/%s" % uuid4().hex


def _get_gtiff_options(compression=None, jpeg_quality=None,
                       predictor=None, interleave=None, tiling=False,
                       tilewidth=None, tileheight=None):

    logger.info("Applying GeoTIFF parameters.")

    if compression:
        if compression.lower() == "huffman":
            compression = "CCITTRLE"
        yield ("COMPRESS", compression.upper())

    if jpeg_quality is not None:
        yield ("JPEG_QUALITY", str(jpeg_quality))

    if predictor:
        pr = ["NONE", "HORIZONTAL", "FLOATINGPOINT"].index(predictor.upper())
        if pr == -1:
            raise ValueError("Invalid compression predictor '%s'." % predictor)
        yield ("PREDICTOR", str(pr + 1))

    if interleave:
        yield ("INTERLEAVE", interleave)

    if tiling:
        yield ("TILED", "YES")
        if tilewidth is not None:
            yield ("BLOCKXSIZE", str(tilewidth))
        if tileheight is not None:
            yield ("BLOCKYSIZE", str(tileheight))


class WCSConfigReader(config.Reader):
    section = "services.ows.wcs"
    maxsize = config.Option(type=int, default=None)
