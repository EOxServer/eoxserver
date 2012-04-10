from tempfile import mkstemp
import ctypes as C
import os.path
import logging

from osgeo import gdal

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError

class RECT(C.Structure):
    _fields_ = [("x_off", C.c_int),
                ("y_off", C.c_int),
                ("x_size", C.c_int),
                ("y_size", C.c_int)]

class SUBSET(C.Structure):
    _fields_ = [("srid", C.c_int),
                ("minx", C.c_double),
                ("miny", C.c_double),
                ("maxx", C.c_double),
                ("maxy", C.c_double)]

_lib_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "_reftools.so"
)

global REFTOOLS_USEABLE
    
try:
    _lib = C.LibraryLoader(C.CDLL).LoadLibrary(_lib_path)

    _get_footprint_wkt = _lib.eoxs_get_footprint_wkt
    _get_footprint_wkt.argtypes = [C.c_void_p]
    _get_footprint_wkt.restype = C.POINTER(C.c_char)

    _rect_from_subset = _lib.eoxs_rect_from_subset
    _rect_from_subset.argtypes = [C.c_void_p, C.POINTER(SUBSET)]
    _rect_from_subset.restype = C.POINTER(RECT)

    _create_rectified_vrt = _lib.eoxs_create_rectified_vrt
    _create_rectified_vrt.argtypes = [C.c_void_p, C.c_char_p, C.c_int]
    _create_rectified_vrt.restype = C.c_int

    _free_string = _lib.eoxs_free_string
    _free_string.argtypes = [C.c_char_p]

    REFTOOLS_USABLE = True
except:
    logging.warn("Could not load '%s'. Referenceable Datasets will not be usable." % _lib_path)
    
    REFTOOLS_USABLE = False


def _open_ds(path_or_ds):
    if isinstance(path_or_ds, gdal.Dataset):
        return path_or_ds
    gdal.AllRegister()
    return gdal.Open(str(path_or_ds))


def get_footprint_wkt(path_or_ds):
    if not REFTOOLS_USABLE:
        raise InternalError("Referenceable grid handling disabled")
    
    ds = _open_ds(path_or_ds)
    
    ret = _get_footprint_wkt(C.c_void_p(long(ds.this)))
    string = C.cast(ret, C.c_char_p).value
    
    _free_string(ret)
    return string

def rect_from_subset(path_or_ds, srid, minx, miny, maxx, maxy):
    if not REFTOOLS_USABLE:
        raise InternalError("Referenceable grid handling disabled")

    ds = _open_ds(path_or_ds)
    
    rect = RECT()
    ret = _rect_from_subset(
        C.c_void_p(long(ds.this)),
        C.byref(SUBSET(srid, minx, miny, maxx, maxy)),
        C.byref(rect)
    )
    if not ret:
        return None
    
    return (rect.x_off, rect.y_off, rect.x_size, rect.y_size)

def create_rectified_vrt(path_or_ds, vrt_path, srid=None):
    if not REFTOOLS_USABLE:
        raise InternalError("Referenceable grid handling disabled")

    ds = _open_ds(path_or_ds)
    ptr = C.c_void_p(long(ds.this))

    if srid:
        ret = _create_rectified_vrt(ptr, vrt_path, srid)
    else:
        ret = _create_rectified_vrt(ptr, vrt_path, 0)  
    
    if not ret:
        raise InternalError(
            "Could not create rectified VRT."
        )

def create_temporary_vrt(path_or_ds, srid=None):
    if not REFTOOLS_USABLE:
        raise InternalError("Referenceable grid handling disabled")

    _, vrt_path = mkstemp(
        dir = System.getConfig().getConfigValue("processing.gdal.reftools", "vrt_tmp_dir"),
        suffix = ".vrt"
    )
    
    create_rectified_vrt(path_or_ds, vrt_path, srid)
    
    return vrt_path
