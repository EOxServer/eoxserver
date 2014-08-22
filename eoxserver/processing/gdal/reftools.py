#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

from tempfile import mkstemp
import ctypes as C
from ctypes.util import find_library
import os.path
import logging
from itertools import izip
import math

from functools import wraps 

from eoxserver.contrib import gdal
from eoxserver.core.util.rect import Rect
from eoxserver.core.exceptions import InternalError


try:
    from osgeo.gdal import GCI_AlphaBand
except ImportError:
    from gdal import GCI_AplhaBand
    
#-------------------------------------------------------------------------------
# approximation transformer's threshold in pixel units 
# 0.125 is the default value used by CLI gdalwarp tool 

APPROX_ERR_TOL=0.125 

#-------------------------------------------------------------------------------
# GDAL transfomer methods 

METHOD_GCP=1  
METHOD_TPS=2  
METHOD_TPS_LSQ=3  

METHOD2STR = { METHOD_GCP: "METHOD_GCP", METHOD_TPS:"METHOD_TPS", METHOD_TPS_LSQ:"METHOD_TPS_LSQ" } 

#-------------------------------------------------------------------------------

logger = logging.getLogger(__name__)
"""
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


class IMAGE_INFO(C.Structure):
    _fields_ = [("x_size", C.c_int),
                ("y_size", C.c_int),
                ("geotransform", C.ARRAY(C.c_double, 6))]
"""

class WARP_OPTIONS(C.Structure):
    _fields_ = [
        ("papszWarpOptions", C.POINTER(C.c_char_p)),
        ("dfWarpMemoryLimit", C.c_double),
        ("eResampleAlg", C.c_int),
        ("eWorkingDataType", C.c_int),
        ("hSrcDS", C.c_void_p),
        ("hDstDS", C.c_void_p),
        ("nBandCount", C.c_int),
        ("panSrcBands", C.POINTER(C.c_int)),
        ("panDstBands", C.POINTER(C.c_int)),
        ("nSrcAlphaBand", C.c_int),
        ("nDstAlphaBand", C.c_int),
        ("padfSrcNoDataReal", C.POINTER(C.c_double)),
        ("padfSrcNoDataImag", C.POINTER(C.c_double)),
        ("padfDstNoDataReal", C.POINTER(C.c_double)),
        ("padfDstNoDataImag", C.POINTER(C.c_double)),
        ("pfnProgress", C.c_void_p),
        ("pProgressArg", C.c_void_p),
        ("pfnTransformer", C.c_void_p),
        ("pTransformerArg", C.c_void_p),
        ("papfnSrcPerBandValidityMaskFunc", C.c_void_p),
        ("papSrcPerBandValidityMaskFuncArg", C.c_void_p),
        ("pfnSrcValidityMaskFunc", C.c_void_p),
        ("pSrcValidityMaskFuncArg", C.c_void_p),
        ("pfnSrcDensityMaskFunc", C.c_void_p),
        ("pSrcDensityMaskFuncArg", C.c_void_p),
        ("pfnDstDensityMaskFunc", C.c_void_p),
        ("pDstDensityMaskFuncArg", C.c_void_p),
        ("pfnDstValidityMaskFunc", C.c_void_p),
        ("pDstValidityMaskFuncArg", C.c_void_p),
        ("pfnPreWarpChunkProcessor", C.c_void_p),
        ("pPreWarpProcessorArg", C.c_void_p),
        ("pfnPostWarpChunkProcessor", C.c_void_p),
        ("pPostWarpProcessorArg", C.c_void_p),
        ("hCutline", C.c_void_p),
        ("dfCutlineBlendDist", C.c_double),
    ]

_libgdal = C.LibraryLoader(C.CDLL).LoadLibrary(find_library("gdal"))


GDALGetGCPs = _libgdal.GDALGetGCPs
GDALGetGCPs.restype = C.c_void_p # actually array of GCPs, but more info not required
GDALGetGCPs.argtypes = [C.c_void_p]


# baseline GDAL transformer creation functions

GDALCreateGCPTransformer = _libgdal.GDALCreateGCPTransformer
GDALCreateGCPTransformer.restype = C.c_void_p
# TODO: argtypes

GDALCreateTPSTransformer = _libgdal.GDALCreateTPSTransformer
GDALCreateTPSTransformer.restype = C.c_void_p
# TODO: argtypes

GDALGenImgProjTransform = _libgdal.GDALGenImgProjTransform

GDALCreateGenImgProjTransformer2 =_libgdal.GDALCreateGenImgProjTransformer2
GDALCreateGenImgProjTransformer2.restype = C.c_void_p
GDALCreateGenImgProjTransformer2.argtypes = [C.c_void_p, C.c_void_p, C.POINTER(C.c_char_p)]

GDALUseTransformer = _libgdal.GDALUseTransformer
GDALUseTransformer.restype = C.c_int
GDALUseTransformer.argtypes = [C.c_void_p, C.c_int, C.c_int, C.POINTER(C.c_double), C.POINTER(C.c_double), C.POINTER(C.c_double), C.POINTER(C.c_int)]

GDALDestroyTransformer = _libgdal.GDALDestroyTransformer
GDALDestroyTransformer.argtypes = [C.c_void_p]

# extended GDAL transformer creation functions
try:
    GDALCreateTPS2TransformerExt = _libgdal.GDALCreateTPS2TransformerExt
    GDALCreateTPS2TransformerExt.restype = C.c_void_p
    # TODO: argtypes
except AttributeError:
    GDALCreateTPS2TransformerExt = None

try:
    GDALCreateTPS2TransformerLSQGrid = _libgdal.GDALCreateTPS2TransformerLSQGrid
    GDALCreateTPS2TransformerLSQGrid.restype = C.c_void_p
    # TODO: argtypes
except AttributeError:
    GDALCreateTPS2TransformerLSQGrid = None


OCTNewCoordinateTransformation = _libgdal.OCTNewCoordinateTransformation
OCTNewCoordinateTransformation.restype = C.c_void_p
OCTNewCoordinateTransformation.argtypes = [C.c_void_p, C.c_void_p]
#OCTNewCoordinateTransformation.errcheck = None # TODO!

OCTDestroyCoordinateTransformation = _libgdal.OCTDestroyCoordinateTransformation
OCTDestroyCoordinateTransformation.argtypes = [C.c_void_p]

GDALCreateWarpOptions = _libgdal.GDALCreateWarpOptions
GDALCreateWarpOptions.restype = C.POINTER(WARP_OPTIONS)

GDALSuggestedWarpOutput = _libgdal.GDALSuggestedWarpOutput
GDALSuggestedWarpOutput.restype = C.c_int
GDALSuggestedWarpOutput.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_double * 6, C.POINTER(C.c_int), C.POINTER(C.c_int)]

GDALSetGenImgProjTransformerDstGeoTransform = _libgdal.GDALSetGenImgProjTransformerDstGeoTransform
GDALSetGenImgProjTransformerDstGeoTransform.argtypes = [C.c_void_p, C.c_double * 6]

class Transformer(object):
    def __init__(self, handle):
        self._handle = handle

    @property
    def _as_parameter_(self):
        return self._handle

    def __del__(self):
        GDALDestroyTransformer(self._handle)

    #def __call__(self, points, ):


class CoordinateTransformation(object):

    def __init__(self, src_srs, dst_srs):
        self._handle = OCTNewCoordinateTransformation(
            src_srs.this, dst_srs.this
        )

    @property
    def _as_parameter_(self):
        return self._handle

    def __del__(self):
        OCTDestroyCoordinateTransformation(self)



def _create_referenceable_grid_transformer(ds, method, order):
    # TODO: check method and order
    num_gcps = ds.GetGCPCount()
    gcps = GDALGetGCPs(ds.this)

    handle = None

    if method == METHOD_GCP:
        handle = GDALCreateGCPTransformer(num_gcps, gcps, order, 0);
    elif method == METHOD_TPS:
        if GDALCreateTPS2TransformerExt:
            handle = GDALCreateTPS2TransformerExt(num_gcps, gcps, 0, order)
        else:
            handle = GDALCreateTPSTransformer(num_gcps, gcps, 0)

    elif method == METHOD_TPS_LSQ and GDALCreateTPS2TransformerLSQGrid:
        handle = GDALCreateTPS2TransformerLSQGrid(num_gcps, gcps, 0, order, 0, 0)
    elif method == METHOD_TPS_LSQ:
        raise AttributeError("GDALCreateTPS2TransformerLSQGrid not available")

    else:
        raise

    return Transformer(handle)



CSLFetchNameValue = _libgdal.CSLFetchNameValue
CSLFetchNameValue.restype = C.c_char_p
CSLFetchNameValue.argtypes = [C.POINTER(C.c_char_p), C.c_char_p]

CSLSetNameValue = _libgdal.CSLSetNameValue
CSLSetNameValue.restype = C.POINTER(C.c_char_p)
CSLSetNameValue.argtypes = [C.POINTER(C.c_char_p), C.c_char_p, C.c_char_p]

CSLDestroy = _libgdal.CSLDestroy
CSLDestroy.argtypes = [C.POINTER(C.c_char_p)]

CSLCount = _libgdal.CSLCount
CSLCount.restype = C.c_int
CSLCount.argtypes = [C.POINTER(C.c_char_p)]

CPLParseNameValue = _libgdal.CPLParseNameValue
CPLParseNameValue.restype = C.c_char_p
CPLParseNameValue.argtypes = [C.c_char_p, C.POINTER(C.c_char_p)]

CPLMalloc = _libgdal.CPLMalloc
CPLMalloc.argtypes=[C.c_size_t ]
CPLMalloc.restype = C.c_void_p

CPLCalloc = _libgdal.CPLCalloc
CPLCalloc.argtypes = [C.c_size_t,C.c_size_t]
CPLCalloc.restype = C.c_void_p

CPLFree = _libgdal.free
CPLFree.argtypes = [C.c_void_p]


class CSL(object):
    """ Wrapper for GDAL CSL API.
    """

    

    def __init__(self, **kwargs):
        self._handle = None
        for key, value in kwargs.items():
            self[key] = value

    @property
    def _as_parameter_(self):
        if not self._handle:
            return C.cast(self._handle, C.POINTER(C.c_char_p))
        return self._handle

    def __getitem__(self, key):
        value = CSLGetNameValue(self, key)
        if not value:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._handle = CSLSetNameValue(self, key, value)

    def __del__(self):
        CSLDestroy(self)

    def __len__(self):
        return CSLCount(self)

    def __iter__(self):
        if not self._handle:
            raise StopIteration

        i = 0
        while True:
            p = self._handle[i]
            if not p:
                break
            key, _, value = p.partition("=")
            yield key, value
            i += 1

    def __repr__(self):
        return "{%s}" % (
            ", ".join(
                "%r: %r" % (key, value) for key, value in self
            )
        )


def _create_generic_transformer(src_ds, src_wkt, dst_ds, dst_wkt, method, order):
    # TODO: check method and order

    try:
        src_ds = C.c_void_p(long(src_ds.this))
    except AttributeError:
        pass
    try:
        dst_ds = C.c_void_p(long(dst_ds.this))
    except AttributeError:
        pass

    options = CSL()

    if src_wkt:
        options["SRC_SRS"] = src_wkt
    if dst_wkt:
        options["DST_SRS"] = dst_wkt

    if method == METHOD_GCP:
        options["METHOD"] = "GCP_POLYNOMIAL"
        options["GCPS_OK"]  = "TRUE"
        if order > 0:
            options["MAX_GCP_ORDER"] = str(order)

    elif method in (METHOD_TPS, METHOD_TPS_LSQ):
        # TODO: TPS2 only if 
        if GDALCreateTPS2TransformerLSQGrid:
            options["METHOD"] = "GCP_TPS2"
            options["TPS2_AP_ORDER"] = str(order)
            if method == METHOD_TPS_LSQ:
                options["TPS2_LSQ_GRID"] = "1"
                options["TPS2_LSQ_GRID_NX"] = "0"
                options["TPS2_LSQ_GRID_NY"] = "0"
        else:
            options["METHOD"] = "GCP_TPS"

    else:
        raise some_error # TODO: raise proper error

    # TODO: proper error handling
    handle = GDALCreateGenImgProjTransformer2(src_ds, dst_ds, options)
    if not handle:
        raise Exception(gdal.GetLastErrorMsg())

    transformer = Transformer(handle)
    return transformer


def get_footprint_wkt(ds, method, order):
    """ 
        methods: 

            METHOD_GCP 
            METHOD_TPS
            METHOD_TPS_LSQ 

        order (method specific):

        - GCP (order of global fitting polynomial)  
            0 for automatic order
            1, 2, and 3  for 1st, 2nd and 3rd polynomial order  

        - TPS and TPS_LSQ (order of augmenting polynomial) 
           -1  for no-polynomial augmentation 
            0  for 0th order (constant offset) 
            1, 2, and 3  for 1st, 2nd and 3rd polynomial order  

        General guide: 

            method TPS, order 3  should work in most cases
            method TPS_LSQ, order 3  shoudl work in cases 
                of an excessive number of tiepoints but
                it may become wobbly for small number
                of tiepoints 
            
           The global polynomoal (GCP) interpolation does not work 
           well for images covering large geographic areas (e.g.,
           ENVISAT ASAR and MERIS).

        NOTE: The default parameters are left for backward compatibility.
              They can be, however, often inappropriate!
    """
    transformer = _create_transformer(ds, method, order)

    x_size = ds.RasterXSize
    y_size = ds.RasterYSize

    x_e = max(x_size / 100 -1, 0)
    y_e = max(y_size / 100 -1, 0)

    num_points = 4 + 2 * x_e + 2 * y_e
    coord_array_type = (C.c_double * num_points)
    x = coord_array_type()
    y = coord_array_type()
    z = coord_array_type()

    success = (C.c_int * num_points)()

    for i in xrange(1, x_e + 1):
        x[i] = float(i * x_size / x_e)
        y[i] = 0.0

    for i in xrange(1, y_e + 1):
        x[x_e + 1 + i] = float(x_size)
        y[x_e + 1 + i] = float(i * y_size * y_e)

    for i in xrange(1, x_e + 1):
        x[x_e + y_e + 2 + i] = 0.0
        y[x_e + y_e + 2 + i] = float(y_size - i * y_size / y_e)

    GDALUseTransformer(transformer, False, num_points, x, y, z, success)

    return "POLYGON((%s))" % (
        ",".join(
            "%f %f" % (coord_x, coord_y)
            for coord_x, coord_y in izip(x, y)
        )
    )


def rect_from_subset(path_or_ds, srid, minx, miny, maxx, maxy,
                     method=METHOD_GCP, order=0):

    transformer = _create_referenceable_grid_transformer(ds, method, order)


    x_size = ds.RasterXSize
    y_size = ds.RasterYSize


    transformer = _create_referenceable_grid_transformer(ds, method, order)

    gcp_srs = osr.SpatialReference(ds.GetGCPProjection())

    subset_srs = osr.SpatialReference()
    subset_srs.ImportFromEPSG(srid)

    coord_array_type = (C.c_double * 4)
    x = coord_array_type()
    y = coord_array_type()
    z = coord_array_type()

    success = (C.c_int * 4)()

    x[1] = float(x_size)
    y[1] = 0.0

    x[2] = float(x_size)
    y[2] = float(y_size)

    x[3] = 0.0
    y[3] = float(y_size)


    GDALUseTransformer(transformer, False, 4, x, y, z, success)

    dist = min(
        (max(x) - min(x)) / (x_size / 100),
        (max(y) - min(y)) / (y_size / 100)
    )

    x[0] = minx; y[0] = miny
    x[1] = maxx; y[1] = miny
    x[2] = maxx; y[2] = maxy
    x[3] = minx; y[3] = maxy


    ct = CoordinateTransformation(subset_srs, gcp_srs)
    
    OCTTransform(ct, 4, x, y, z)

    num_x = math.ceil((max(x) - min(x)) / dist)
    num_y = math.ceil((max(y) - min(y)) / dist)

    x_step = (maxx - minx) / num_x
    y_step = (maxy - miny) / num_y

    n_points = 4 + 2 * n_x + 2 * n_y

    coord_array_type = (C.c_double * num_points)
    x = coord_array_type()
    y = coord_array_type()
    z = coord_array_type()
    success = (C.c_int * num_points)()

    for i in xrange(1, num_x + 1):
        x[i] = minx + i * x_step
        y[i] = miny

    for i in xrange(1, n_y + 1):
        x[i + num_x + 1] = maxx
        y[i + num_y + 1] = maxy + i * y_step

    for i in xrange(1, num_x + 1):
        x[i + num_x + num_y + 2] = maxx - i * x_step
        y[i + num_x + num_y + 2] = maxy

    for i in xrange(1, num_y + 1):
        x[i + 2 * num_x + num_y + 3] = minx
        y[i + 2 * num_x + num_y + 3] = maxy - i * y_step


    OCTTransform(ct, num_points, x, y, z)
    GDALUseTransformer(transformer, True, num_points, x, y, z, success)

    minx = math.floor(min(x))
    miny = math.floor(min(y))
    size_x = math.ceil(max(x) - minx) + 1
    size_y = math.ceil(max(y) - miny) + 1

    return Rect(minx, miny, size_x, size_y)


def create_rectified_vrt(path_or_ds, vrt_path, srid=None,
    resample=gdal.GRA_NearestNeighbour, memory_limit=0.0,
    max_error=APPROX_ERR_TOL, method=METHOD_GCP, order=0):

    ds = _open_ds(path_or_ds)
    ptr = C.c_void_p(long(ds.this))    

    if srid: 
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(srid)
        wkt = srs.ExportToWkt()
        srs = None
    else:
        wkt = ds.GetGCPProjection()

    transformer = _create_generic_transformer(
        ds, None, None, wkt, method, order
    )

    x_size = C.c_int()
    y_size = C.c_int()
    geotransform = (C.c_double * 6)()

    GDALSuggestedWarpOutput(
        ptr,
        GDALGenImgProjTransform, transformer, geotransform, 
        C.byref(x_size), C.byref(y_size)
    )

    GDALSetGenImgProjTransformerDstGeoTransform(transformer, geotransform)

    options = GDALCreateWarpOptions()
    options.contents.dfWarpMemoryLimit = memory_limit
    options.contents.eResampleAlg = resample
    options.contents.pfnTransformer = C.cast(GDALGenImgProjTransform,C.c_void_p)
    options.contents.pTransformerArg = C.cast(transformer,C.c_void_p)
    options.contents.hSrcDS = ptr

    nb = ds.RasterCount
    options.contents.nBandCount = nb
    options.contents.panSrcBands = C.cast(CPLMalloc(C.sizeof(C.c_int) * nb),C.POINTER(C.c_int))
    options.contents.panDstBands = C.cast(CPLMalloc(C.sizeof(C.c_int) * nb),C.POINTER(C.c_int))
    
    # TODO: nodata value setup
    for i in xrange(nb):
        options.contents.panSrcBands[i]=i+1
        options.contents.panDstBands[i]=i+1
    
    for i in xrange(nb):
        band = ds.GetRasterBand(i+1)
        v_noda=band.GetNoDataValue()
        if v_noda is not None:
            if not options.contents.padfSrcNoDataReal:
                options.contents.padfSrcNoDataImag = C.cast(CPLCalloc(nb,C.sizeof(C.c_double)),C.POINTER(C.c_double))
                options.contents.padfSrcNoDataReal = C.cast(CPLCalloc(nb,C.sizeof(C.c_double)),C.POINTER(C.c_double))
                for j in xrange(nb):
                    options.contents.padfSrcNoDataReal[j] = -1.1e20
            options.contents.padfSrcNoDataReal[i]=v_noda
        if band.GetRasterColorInterpretation() == GCI_AlphaBand:
            options.contents.nSrcAlphaBand = i+1
            options.contents.nDstAlphaBand = i+1
            
    if max_error > 0:
#        print "maxerr>0"
        GDALCreateApproxTransformer = _libgdal.GDALCreateApproxTransformer
        GDALCreateApproxTransformer.restype = C.c_void_p
        GDALCreateApproxTransformer.argtypes = [C.c_void_p, C.c_void_p, C.c_double]

        GDALApproxTransform = _libgdal.GDALApproxTransform

        GDALApproxTransformerOwnsSubtransformer = _libgdal.GDALApproxTransformerOwnsSubtransformer
        GDALApproxTransformerOwnsSubtransformer.argtypes = [C.c_void_p, C.c_bool]

        options.contents.pTransformerArg = GDALCreateApproxTransformer(
            options.contents.pfnTransformer, options.contents.pTransformerArg, max_error
        )
        options.contents.pfnTransformer = C.cast(GDALApproxTransform,C.c_void_p) 
        # TODO: correct for python
        # Will be destroyed by Transformer.__del__ ?
        GDALApproxTransformerOwnsSubtransformer(options.contents.pTransformerArg, False)


    GDALCreateWarpedVRT = _libgdal.GDALCreateWarpedVRT
    GDALCreateWarpedVRT.restype = C.c_void_p
    GDALCreateWarpedVRT.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_double * 6, C.POINTER(WARP_OPTIONS)]

#    print "XXXX"

    GDALAutoCreateWarpedVRT = _libgdal.GDALAutoCreateWarpedVRT
    GDALAutoCreateWarpedVRT.restype = C.c_void_p
    GDALAutoCreateWarpedVRT.argtypes = [C.c_void_p, C.c_char_p, C.c_char_p, C.c_int, C.c_double, C.POINTER(WARP_OPTIONS)]
    
#    print x_size, y_size, tuple(geotransform), options
    vrt_ds = GDALCreateWarpedVRT(ptr, x_size, y_size, geotransform, options)

#    print "YYYY"

    GDALSetProjection = _libgdal.GDALSetProjection
    GDALSetProjection.argtypes = [C.c_void_p, C.c_char_p]
    GDALSetProjection(vrt_ds, wkt)
#    print "ZZZZ"

    GDALSetDescription = _libgdal.GDALSetDescription
    GDALSetDescription.argtypes = [C.c_void_p, C.c_char_p]
    GDALSetDescription(vrt_ds, vrt_path)
#    print "AAAA"

    GDALClose = _libgdal.GDALClose
    GDALClose.argtypes = [C.c_void_p]
    GDALClose(vrt_ds)
#    print "BBBB"

    GDALDestroyWarpOptions = _libgdal.GDALDestroyWarpOptions
    GDALDestroyWarpOptions.argtypes = [C.POINTER(WARP_OPTIONS)]
    GDALDestroyWarpOptions(options)
#    print "CCCC"

def suggested_warp_output(ds, src_wkt, dst_wkt, method=METHOD_GCP, order=0):
    geotransform = (C.c_double * 6)()
    x_size = C.c_int()
    y_size = C.c_int()
    transformer = _create_generic_transformer(ds, src_wkt, dst_wkt, method, order)
    GDALSuggestedWarpOutput(
        ds, GDALGenImgProjTransform, transformer, 
        geotransform, C.byref(x_size), C.byref(y_size)
    )

    return x_size.value, y_size.value, tuple(geotransform)


def reproject_image(src_ds, src_wkt, dst_ds, dst_wkt, 
                    resample=gdal.GRA_NearestNeighbour, memory_limit=0.0,
                    max_error=APPROX_ERR_TOL, method=METHOD_GCP, order=0):

    transformer = _create_generic_transformer(
        src_ds.this, src_wkt, dst_ds.this, dst_wkt, method, order
    )
    size_x = dst_ds.RasterXSize
    size_y = dst_ds.RasterYSize

    options = GDALCreateWarpOptions()
    options.eResampleAlg = resample
    options.dfWarpMemoryLimit = memory_limit

    options.hSrcDS = src_ds.this
    options.hSrcDS = dst_ds.this

    if max_error > 0:
        options.pTransformerArg = GDALCreateApproxTransformer(
            GDALGenImgProjTransform, transformer, max_error
        )
        options.pfnTransformer = GDALApproxTransform
    else:
        options.pfnTransformer = GDALGenImgProjTransform
        options.pTransformerArg = transformer

    if options.nBandCount == 0:
        # TODO: implement srcbands
        pass

    # TODO: nodata setup

    warper = GDALCreateWarpOperation(options)
    GDALChunkAndWarpImage(warper, 0, 0, size_x, size_y)

    GDALDestroyWarpOptions(options)


def _open_ds(path_or_ds):
    if isinstance(path_or_ds, basestring):
        gdal.AllRegister()
        return gdal.Open(str(path_or_ds))
    return path_or_ds

def is_extended() : 
    """ check whether the EOX's GDAL extensions are available
        (True) or not (False)
    """
    return bool(GDALCreateTPS2TransformerLSQGrid or GDALCreateTPS2TransformerExt)


def suggest_transformer( path_or_ds ) : 
    """ suggest value of method and order to be passed 
        tp ``get_footprint_wkt`` and ``rect_from_subset``
    """

    # get info about the dataset 
    ds = _open_ds(path_or_ds)

    nn = ds.GetGCPCount()
    sx = ds.RasterXSize
    sy = ds.RasterYSize

    # guess reasonable limit number of tie-points
    # (Assuming that the tiepoints cover but not execeed
    # the full raster image. That way we don't need 
    # to calculate bounding box of the tiepoints' set.)  
    nx = 5 
    ny = int(max(1, 0.5*nx*float(sy)/float(sx))) 
    ng = (nx+1) * (ny+1) + 10 

    # check if we deal with an outline along the image's vertical edges
    if nn < 500: # avoid check for large tie-point sets 
        cnt = 0 
        for gcp in ds.GetGCPs() : 
            cnt += (gcp.GCPPixel < 1) or (gcp.GCPPixel >= (sx - 1)) 
        is_vertical_outline = (cnt == nn)
    else: 
        is_vertical_outline = False
    
    # check whether the GDAL extensions are available 

    if is_extended(): # extended GDAL 
        
        # set default to TPS and 3rd order augmenting polynomial 
        order = 3
        method = METHOD_TPS

        # some very short ASAR products need 1st order augmenting polynomial
        # the numerics for higher order aug.pol. becomes a bit `wobbly`
        if 4 * sy < sx:
            order = 1 
         
        # small fotprints such as ngEO should use lower TPS-AP order  
        if is_vertical_outline:
            order = 1 

        # for excessive number of source tiepoints use Least-Square TPS fit 
        if nn > ng: 
            method = METHOD_TPS_LSQ
         
    else: # baseline GDAL 

        # set default to TPS and 1st order 
        # (the only order available in baseline GDAL)
        order = 1 
        method = METHOD_TPS
        
        # for excessive number of source tiepoints use polynomial GCP fit 
        # (the result will most likely incorrect but there is nothing 
        # better to be done with the baseline GDAL)  
        if nn > ng: 
            method = METHOD_GCP
            order = 0 # automatic order selection 

    return {'method':method, 'order':order} 
