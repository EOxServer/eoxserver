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

import subprocess
import math
from django.utils.six import string_types

from eoxserver.contrib import gdal, vsi, osr


def get_vrt_driver():
    """ Convenience function to get the VRT driver.
    """
    return gdal.GetDriverByName("VRT")


class VRTBuilder(object):
    """ This class is a helper to easily create VRT datasets from various
    sources.

    :param size_x: the pixel size of the X dimension
    :param size_y: the pixel size of the Y dimension
    :param num_bands: the initial number of bands; bands can be added afterwards
    :param data_type: the GDT data type identifier
    :param vrt_filename: a path the filename shall be stored at; if none is
                         specified the dataset will only be kept in memory
    """

    def __init__(self, size_x, size_y, num_bands=0, data_type=None,
                 vrt_filename=None):
        driver = get_vrt_driver()
        data_type = data_type if data_type is not None else gdal.GDT_Byte
        self._ds = driver.Create(
            vrt_filename or "", size_x, size_y, num_bands, data_type
        )

    @classmethod
    def from_dataset(cls, ds, vrt_filename=None):
        """ A helper function to create a VRT dataset from a given template
        dataset.

        :param ds: a :class:`GDAL Dataset <eoxserver.contrib.gdal.Dataset>`
        """

        vrt_builder = cls(
            ds.RasterXSize, ds.RasterYSize, ds.RasterCount,
            vrt_filename=vrt_filename
        )

        for key, value in ds.GetMetadata().items():
            vrt_builder.dataset.SetMetadataItem(key, value)

    @property
    def dataset(self):
        """ Returns a handle to the underlying VRT :class:`GDAL Dataset
        <eoxserver.contrib.gdal.Dataset>`.
        """
        return self._ds

    def copy_metadata(self, ds):
        """ Copy the metadata fields and values from the given dataset.

        :param ds: a :class:`GDAL Dataset <eoxserver.contrib.gdal.Dataset>`
        """
        for key, value in ds.GetMetadata().items():
            self._ds.SetMetadataItem(key, value)

    def copy_gcps(self, ds, offset=None):
        """ Copy the GCPs from the given :class:`GDAL Dataset
        <eoxserver.contrib.gdal.Dataset>`, optionally offsetting them

        :param ds: a :class:`GDAL Dataset <eoxserver.contrib.gdal.Dataset>`
        :param offset: a 2-tuple of integers; the pixel offset to be applied to
                       any GCP copied
        """
        gcps = ds.GetGCPs()
        if offset:
            gcps = [
                gdal.GCP(
                    gcp.GCPX, gcp.GCPY, gcp.GCPZ,
                    gcp.GCPPixel-offset[0], gcp.GCPLine-offset[1],
                    gcp.Info, gcp.Id
                ) for gcp in gcps
            ]
        self._ds.SetGCPs(gcps, ds.GetGCPProjection())

    def add_band(self, data_type=None, options=None, nodata=None):
        """ Add a band to the VRT Dataset.

        :param data_type: the data type of the band to add. if omitted this is
                          determined automatically by GDAL
        :param options: a list of any string options to be supplied to the new
                        band
        """
        self._ds.AddBand(data_type, options or [])
        if nodata is not None:
            band = self._ds.GetRasterBand(self._ds.RasterCount)
            band.SetNoDataValue(nodata)

    def _add_source_to_band(self, band_index, source):
        band = self._ds.GetRasterBand(band_index)
        if not band:
            raise IndexError

        band.SetMetadataItem("source_0", str(source), "new_vrt_sources")

    def add_simple_source(self, band_index, src, src_band,
                          src_rect=None, dst_rect=None):
        """ Add a new simple source to the VRT.

        :param band_index: the band index the source shall contribute to
        :param src: either a :class:`GDAL Dataset
                    <eoxserver.contrib.gdal.Dataset>` or a file path to the
                    source dataset
        :param src_band: specify which band of the source dataset shall
                         contribute to the target VRT band
        :param src_rect: a 4-tuple of integers in the form (offset-x, offset-y,
                         size-x, size-y) or a :class:`Rect
                         <eoxserver.core.util.rect.Rect>` specifying the source
                         area to contribute
        :param dst_rect: a 4-tuple of integers in the form (offset-x, offset-y,
                         size-x, size-y) or a :class:`Rect
                         <eoxserver.core.util.rect.Rect>` specifying the target
                         area to contribute
        """
        if isinstance(src, string_types):
            pass

        else:
            try:
                src = src.GetFileList()[0]
            except AttributeError:
                raise ValueError("Expected string or GDAL Dataset.")
            except IndexError:
                raise ValueError("Supplied Dataset does not have a filename.")

        lines = [
            "<SimpleSource>",
            '<SourceFilename relativeToVRT="1">%s</SourceFilename>' % src,
            "<SourceBand>%d</SourceBand>" % src_band
        ]
        if src_rect:
            lines.append(
                '<SrcRect xOff="%d" yOff="%d" xSize="%d" ySize="%d"/>'
                % src_rect
            )
        if dst_rect:
            lines.append(
                '<DstRect xOff="%d" yOff="%d" xSize="%d" ySize="%d"/>'
                % dst_rect
            )
        lines.append("</SimpleSource>")

        self._add_source_to_band(band_index, "".join(lines))


class VRTBuilder2(object):
    def __init__(self, size_x, size_y, num_bands=0, data_type=None, vrt_filename=None):
        self.size_x = size_x
        self.size_y = size_y
        self.bands =[]
        self.filename = vrt_filename
        for i in range(0):
            self.add_band(data_type)

        self.transformer = None
        self.geotransform = None

    def set_geotransform(self, geotransform):
        self.geotransform = geotransform

    def add_band(self, data_type=None, options=None, nodata=None):
        self.bands.append(
            dict(data_type=data_type, options=options, nodata=nodata, sources=[])
        )

    def add_simple_source(self, band_index, src, src_band,
                          src_rect=None, dst_rect=None):
        """ Add a new simple source to the VRT.

        :param band_index: the band index the source shall contribute to
        :param src: either a :class:`GDAL Dataset
                    <eoxserver.contrib.gdal.Dataset>` or a file path to the
                    source dataset
        :param src_band: specify which band of the source dataset shall
                         contribute to the target VRT band
        :param src_rect: a 4-tuple of integers in the form (offset-x, offset-y,
                         size-x, size-y) or a :class:`Rect
                         <eoxserver.core.util.rect.Rect>` specifying the source
                         area to contribute
        :param dst_rect: a 4-tuple of integers in the form (offset-x, offset-y,
                         size-x, size-y) or a :class:`Rect
                         <eoxserver.core.util.rect.Rect>` specifying the target
                         area to contribute
        """
        if isinstance(src, string_types):
            pass

        else:
            try:
                src = src.GetFileList()[0]
            except AttributeError:
                raise ValueError("Expected string or GDAL Dataset.")
            except IndexError:
                raise ValueError("Supplied Dataset does not have a filename.")

        self.bands[band_index-1]["sources"].append(
            (src, src_band, src_rect, dst_rect)
        )

    def warped_gcps(self, gcp_dsc, resample="NearestNeighbour", order=0):
        self.transformer = (gcp_ds, resample, order)

    def build_sources(self, sources):
        from lxml.builder import E
        sources = []
        for src, src_band, src_rect, dst_rect in sources:
            elem = E("SimpleSource",
                E("SourceFilename", src, relativeToVRT="0"),
                E("SourceBand", str(src_band))
            )
            if src_rect:
                elem.append(E("SrcRect",
                    xOff=str(src_rect[0]), yOff=str(src_rect[1]),
                    xSize=str(src_rect[2]), ySize=str(src_rect[3]))
                )
            if dst_rect:
                elem.append(E("DstRect",
                    xOff=str(dst_rect[0]), yOff=str(dst_rect[1]),
                    xSize=str(dst_rect[2]), ySize=str(dst_rect[3]))
                )

            sources.append(elem)

        return sources

    def build(self):
        from lxml.builder import E
        from lxml import etree
        root = E("VRTDataset", *[
            E("VRTRasterBand",
                *self.build_sources(band["sources"]),
                dataType=gdal.GetDataTypeName(band["data_type"]),
                band=str(i)
            ) for i, band in enumerate(self.bands, start=1)
        ], rasterXSize=str(self.size_x), rasterYSize=str(self.size_y))
        #root.append()

        if self.transformer:
            gcp_ds, resample, order = self.transformer
            root.append(E("GDALWarpOptions",
                E("WarpMemoryLimit", "6.71089e+07"),
                E("ResampleAlg", resample)
            ))
        return etree.tostring(root, pretty_print=True)


def gdalbuildvrt(filename, paths, separate=False, nodata=None):
    """ Builds a VRT file from the passed files using the
        `gdalbuildvrt` command and stores the resulting file
        under the passed filename.
    """
    args = [
        '/usr/bin/gdalbuildvrt',
        '-resolution',
        'highest',
        '-q',
        '/vsistdout/',
    ]
    if separate:
        args.append('-separate')

    if nodata is not None:
        args.extend([
            '-srcnodata',
            ' '.join(str(value) for value in nodata)
        ])

    content = subprocess.check_output(args + paths)

    with vsi.open(filename, "w") as f:
        f.write(content)


def _determine_parameters(datasets):
    first = datasets[0]
    first_proj = first.GetProjection()
    first_srs = osr.SpatialReference(first_proj)

    first_gt = first.GetGeoTransform()

    others = datasets[1:]

    res_x, res_y = first_gt[1], first_gt[5]
    o_x, o_y = first_gt[0], first_gt[3]

    e_x = o_x + res_x * first.RasterXSize
    e_y = o_y + res_y * first.RasterYSize

    for dataset in others:
        proj = dataset.GetProjection()
        srs = osr.SpatialReference(proj)

        gt = dataset.GetGeoTransform()

        dx, dy = gt[1], gt[5]

        res_x = min(dx, res_x)
        res_y = max(dy, res_y)

        o_x = min(gt[0], o_x)
        o_y = max(gt[3], o_y)

        e_x = max(gt[0] + dx * dataset.RasterXSize, e_x)
        e_y = min(gt[3] + dy * dataset.RasterYSize, e_y)

        assert srs.IsSame(first_srs)
        assert dataset.RasterCount == first.RasterCount

    x_size = int(math.ceil(abs(o_x - e_x) / res_x))
    y_size = int(math.ceil(abs(o_y - e_y) / abs(res_y)))

    return first_proj, (o_x, o_y), (e_x, e_y), (res_x, res_y), (x_size, y_size)


def _get_dst_rect(dataset, o_x, o_y, res_x, res_y):
    gt = dataset.GetGeoTransform()
    dx, dy = gt[1], gt[5]

    x_off = round((gt[0] - o_x) / res_x)
    y_off = round((o_y - gt[3]) / abs(res_y))

    e_x = gt[0] + dx * dataset.RasterXSize
    e_y = gt[3] + dy * dataset.RasterYSize

    x_size = round((e_x - o_x) / res_x) - x_off
    y_size = round((o_y - e_y) / abs(res_y)) - y_off

    return x_off, y_off, x_size, y_size


def mosaic(filenames, save=None):
    """ Creates a mosaic VRT from the specified filenames.
        This function always uses the highest resolution available. The VRT
        is stored under the ``save`` filename, when passed
    """
    datasets = [
        gdal.OpenShared(filename)
        for filename in filenames
    ]

    first = datasets[0]
    proj, (o_x, o_y), _, (res_x, res_y), (size_x, size_y) = \
        _determine_parameters(datasets)

    driver = get_vrt_driver()
    out_ds = driver.Create(save, size_x, size_y, 0)

    out_ds.SetProjection(proj)
    out_ds.SetGeoTransform([o_x, res_x, 0, o_y, 0, res_y])

    for i in range(1, first.RasterCount + 1):
        first_band = first.GetRasterBand(i)
        out_ds.AddBand(first_band.DataType)
        band = out_ds.GetRasterBand(i)
        nodata_value = first_band.GetNoDataValue()
        if nodata_value is not None:
            band.SetNoDataValue(nodata_value)

        for dataset, filename in zip(datasets, filenames):
            x_off, y_off, x_size, y_size = _get_dst_rect(
                dataset, o_x, o_y, res_x, res_y
            )
            nodata_value = dataset.GetRasterBand(i).GetNoDataValue()

            band.SetMetadataItem("source_0", """
                <{source_type}Source>
                    <SourceFilename relativeToVRT="0">{filename}</SourceFilename>
                    <SourceBand>{band}</SourceBand>
                    <SrcRect xOff="0" yOff="0" xSize="{x_size_orig}" ySize="{y_size_orig}"></SrcRect>
                    <DstRect xOff="{x_off}" yOff="{y_off}" xSize="{x_size}" ySize="{y_size}"></DstRect>
                    <NODATA>{nodata_value}</NODATA>
                </{source_type}Source>
            """.format(
                band=i, filename=filename,
                x_size_orig=dataset.RasterXSize,
                y_size_orig=dataset.RasterYSize,
                x_off=x_off, y_off=y_off,
                x_size=x_size, y_size=y_size,
                source_type='Complex' if nodata_value is not None else 'Simple',
                nodata_value=nodata_value if nodata_value is not None else '',
            ), "new_vrt_sources")

    return out_ds


def select_bands(filename, env, band_indices, save=None):
    with gdal.config_env(env):
        ds = gdal.OpenShared(filename)

        out_ds = get_vrt_driver().Create(save, ds.RasterXSize, ds.RasterYSize, 0)
        out_ds.SetProjection(ds.GetProjection())
        out_ds.SetGeoTransform(ds.GetGeoTransform())

        for i, index in enumerate(band_indices, start=1):
            band = ds.GetRasterBand(index)
            out_ds.AddBand(band.DataType)
            out_band = out_ds.GetRasterBand(i)

            nodata_value = band.GetNoDataValue()
            if nodata_value is not None:
                out_band.SetNoDataValue(nodata_value)

            out_band.SetMetadataItem("source_0", """
                <SimpleSource>
                    <SourceFilename relativeToVRT="0">{filename}</SourceFilename>
                    <SourceBand>{band}</SourceBand>
                </SimpleSource>
            """.format(
                band=index, filename=filename
            ), "new_vrt_sources")

    return out_ds


def stack_bands(filenames, env, save=None):
    with gdal.config_env(env):
        datasets = [
            gdal.OpenShared(filename)
            for filename in filenames
        ]

    first = datasets[0]
    proj, (o_x, o_y), _, (res_x, res_y), (size_x, size_y) = \
        _determine_parameters(datasets)

    out_ds = get_vrt_driver().Create(
        save, first.RasterXSize, first.RasterYSize, 0
    )
    out_ds.SetProjection(first.GetProjection())
    out_ds.SetGeoTransform(first.GetGeoTransform())

    out_index = 1
    for dataset, filename in zip(datasets, filenames):
        x_off, y_off, x_size, y_size = _get_dst_rect(
            dataset, o_x, o_y, res_x, res_y
        )

        for index in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(index)
            out_ds.AddBand(band.DataType)
            out_band = out_ds.GetRasterBand(out_index)

            nodata_value = band.GetNoDataValue()
            if nodata_value is not None:
                out_band.SetNoDataValue(nodata_value)

            out_band.SetMetadataItem("source_0", """
                <SimpleSource>
                    <SourceFilename relativeToVRT="0">{filename}</SourceFilename>
                    <SourceBand>{band}</SourceBand>
                    <SrcRect xOff="0" yOff="0" xSize="{x_size_orig}" ySize="{y_size_orig}"></SrcRect>
                    <DstRect xOff="{x_off}" yOff="{y_off}" xSize="{x_size}" ySize="{y_size}"></DstRect>
                </SimpleSource>
            """.format(
                band=index, filename=filename,
                x_size_orig=dataset.RasterXSize,
                y_size_orig=dataset.RasterYSize,
                x_off=x_off, y_off=y_off,
                x_size=x_size, y_size=y_size,
            ), "new_vrt_sources")

            out_index += 1

    return out_ds

def with_extent(filename, extent, save=None):
    """ Create a VRT and override the underlying files geolocation
    """
    src_ds = gdal.OpenShared(filename)
    width, height = src_ds.RasterXSize, src_ds.RasterYSize
    driver = gdal.GetDriverByName('VRT')
    out_ds = driver.CreateCopy(save, src_ds)

    x = extent[0]
    y = extent[3]

    resx = abs(extent[2] - extent[0]) / width
    resy = abs(extent[3] - extent[1]) / height
    out_ds.SetGeoTransform([
        x,
        resx,
        0,
        y,
        0,
        resy,
    ])
    return out_ds
