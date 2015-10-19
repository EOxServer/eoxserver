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


from eoxserver.contrib import gdal


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
        if isinstance(src, basestring):
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
        if isinstance(src, basestring):
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
