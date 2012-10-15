from os.path import exists
import numpy

from osgeo import gdal, gdalconst, gdal_array, ogr, osr


gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()


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
    

def create_mem(sizex, sizey, numbands, datatype=gdalconst.GDT_Byte,
                options=None):
    """ Create a new In-Memory Dataset. """
    if options is None:
        options = []
    
    mem_drv = gdal.GetDriverByName('MEM')
    return mem_drv.Create('', sizex, sizey, numbands, datatype, options)


def copy_projection(src_ds, dst_ds):
    """ Copy the projection and geotransform from on dataset to another """
    dst_ds.SetProjection(src_ds.GetProjection())
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())

    
def copy_metadata(src_ds, dst_ds):
    """ Copy the metadata from on dataset to another """
    dst_ds.SetMetadata(src_ds.GetMetadata_Dict())


def check_file_existence(filename):
    " Check if file exists and raise an IOError if it does. "
    if exists(filename):
        raise IOError("The output file '%s' already exists." % filename)
