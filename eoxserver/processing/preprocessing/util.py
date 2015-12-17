#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
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

from os.path import exists, join
from uuid import uuid4
import tempfile
import contextlib
import logging

import numpy

from eoxserver.contrib import gdal, gdal_array


logger = logging.getLogger(__name__)


def get_limits(dt):
    """ Returns the numeric limits of the GDAL/numpy datatype """
    if dt in gdal_array.codes:
        dt = gdal_array.codes[dt]

    try:
        info = numpy.iinfo(dt)
    except ValueError:
        info = numpy.finfo(dt)

    return info.min, info.max


#===============================================================================
# helper functions
#===============================================================================

def create_mem_copy(ds, *args, **kwargs):
    """ Create a new In-Memory Dataset as copy from an existing dataset. """
    mem_drv = gdal.GetDriverByName('MEM')
    return mem_drv.CreateCopy('', ds, *args, **kwargs)


def create_mem(sizex, sizey, numbands, datatype=gdal.GDT_Byte,
               options=None):
    """ Create a new In-Memory Dataset. """
    if options is None:
        options = []

    mem_drv = gdal.GetDriverByName('MEM')
    return mem_drv.Create('', sizex, sizey, numbands, datatype, options)


def create_temp(sizex, sizey, numbands, datatype=gdal.GDT_Byte,
                options=None, temp_root=None):
    """ Create a temporary Dataset. """

    temp_root = temp_root if temp_root is not None else tempfile.gettempdir()

    if options is None:
        options = []

    tiff_drv = gdal.GetDriverByName('GTiff')
    filename = join(temp_root, '%s.tif' % uuid4().hex)
    logger.debug(
        "Creating temporary dataset '%s' (%dx%dx%d)" % (
            filename, sizex, sizey, numbands
        )
    )
    return tiff_drv.Create(filename, sizex, sizey, numbands, datatype, options)


def cleanup_temp(ds):
    """ Delete a temporary dataset.
    """
    if isinstance(ds, str):
        driver = gdal.IdentifyDriver(ds)
        filelist = [ds]
    else:
        driver = ds.GetDriver()
        filelist = ds.GetFileList() or []
        ds.FlushCache()
        ds = None

    try:
        for filename in filelist:
            if filename.endswith(".ovr") or filename.endswith(".msk"):
                continue
            logger.debug("Cleaning up temporary dataset '%s'." % filename)
            driver.Delete(filename)
    except:
        logger.warning(
            "Failed to delete dataset '%s', falling back to raw delete."
            % filename
        )
        for filename in filelist:
            gdal.Unlink(filename)


@contextlib.contextmanager
def temporary_dataset(sizex, sizey, numbands, datatype=gdal.GDT_Byte,
                      options=None, temp_root=None):
    ds = create_temp(sizex, sizey, numbands, datatype, options, temp_root)
    yield ds
    cleanup_temp(ds)


def copy_projection(src_ds, dst_ds):
    """ Copy the projection and geotransform from on dataset to another """
    dst_ds.SetProjection(src_ds.GetProjection())
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())


def copy_metadata(src_ds, dst_ds):
    """ Copy the metadata from on dataset to another """
    dst_ds.SetMetadata(src_ds.GetMetadata_Dict())


def copy_nodatavalue(src_ds, dst_ds):
    """ Copy the nodata value from on dataset to another """
    assert src_ds.RasterCount == dst_ds.RasterCount
    for i in range(src_ds.RasterCount):
        src_band = src_ds.GetRasterBand(i+1)
        if src_band.GetNoDataValue() is not None:
            dst_band = dst_ds.GetRasterBand(i+1)
            dst_band.SetNoDataValue(src_band.GetNoDataValue())


def check_file_existence(filename):
    " Check if file exists and raise an IOError if it does. "
    if exists(filename):
        raise IOError("The output file '%s' already exists." % filename)
