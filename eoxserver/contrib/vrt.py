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


from eoxserver.contrib import gdal


def get_vrt_driver():
    """ Convenience function to get the VRT driver.
    """
    return gdal.GetDriverByName("VRT")


class VRTBuilder(object):
    """ A driver for 
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
        vrt_builder = cls(
            ds.RasterXSize, ds.RasterYSize, ds.RasterCount, 
            vrt_filename=vrt_filename
        )

        for key, value in ds.GetMetadata().items():
            vrt_builder.dataset.SetMetadataItem(key, value)


    @property
    def dataset(self):
        return self._ds


    def copy_metadata(self, ds):
        for key, value in ds.GetMetadata().items():
            self._ds.SetMetadataItem(key, value)

    def copy_gcps(self, ds, rect=None):
        gcps = ds.GetGCPs()
        if rect:
            gcps = [
                gdal.GCP(
                    gcp.GCPX, gcp.GCPY, gcp.GCPZ, gcp.GCPPixel-rect[0], 
                    gcp.GCPLine-rect[1], gcp.Info, gcp.Id
                ) for gcp in gcps
            ]
        self._ds.SetGCPs(gcps, ds.GetGCPProjection())


    def add_band(self, data_type=None, options=None):
        self._ds.AddBand(data_type, options or [])


    def _add_source_to_band(self, band_index, source):
        band = self._ds.GetRasterBand(band_index)
        if not band:
            raise IndexError

        band.SetMetadataItem("source_0", source, "new_vrt_sources")


    def add_simple_source(self, band_index, src, src_band, 
                          src_rect=None, dst_rect=None):
        if isinstance(src, str):
            pass

        else:
            try:
                src = src.GetFileList()[0]
            except AttributeError:
                raise ValueErrror("Expected string or GDAL Dataset.")
            except IndexError:
                raise ValueErrror("Supplied Dataset does not have a filename.")

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


        
