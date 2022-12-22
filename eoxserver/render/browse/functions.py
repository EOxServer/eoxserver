# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

import logging
from uuid import uuid4
from functools import wraps
from typing import List, SupportsFloat as Numeric

import numpy as np

from eoxserver.contrib import gdal
from eoxserver.contrib import ogr
from eoxserver.contrib import gdal_array
from eoxserver.render.browse.util import convert_dtype


logger = logging.getLogger(__name__)

__all__ = [
    'get_function',
    'get_buffer',
]


def _dem_processing(data, processing, **kwargs):
    filename = '/vsimem/%s.tif' % uuid4().hex
    try:
        gdal.DEMProcessing(
            filename,
            data,
            processing,
            **kwargs
        )
    except Exception:
        gdal.Unlink(filename)
    out_ds = gdal.Open(filename)
    return out_ds


def hillshade(data, zfactor=1, scale=1, azimuth=315, altitude=45, alg='Horn'):
    return _dem_processing(
        data,
        'hillshade',
        zFactor=zfactor,
        scale=scale,
        azimuth=azimuth,
        altitude=altitude,
        alg=alg,
    )


def slopeshade(data, scale=1, alg='Horn'):
    return _dem_processing(
        data,
        'slope',
        scale=scale,
        alg=alg,
    )


def aspect(data, trignonometric=False, zero_for_flat=False, alg='Horn'):
    return _dem_processing(
        data,
        'aspect',
        trigonometric=trignonometric,
        zeroForFlat=zero_for_flat,
        alg=alg,
    )


def tri(data, alg='Wilson'):
    return _dem_processing(
        data,
        'TRI',
        alg=alg,
    )


def tpi(data):
    return _dem_processing(
        data,
        'TPI',
    )


def roughness(data):
    return _dem_processing(
        data,
        'roughness',
    )


def contours(data, offset=0, interval=100, fill_value=-9999, format='raster'):
    in_band = data.GetRasterBand(1)
    vec_filename = '/tmp/%s.shp' % uuid4().hex
    out_filename = '/vsimem/%s.tif' % uuid4().hex
    vector_driver = ogr.GetDriverByName('ESRI Shapefile')

    try:
        contour_datasource = vector_driver.CreateDataSource(vec_filename)
        contour_layer = contour_datasource.CreateLayer('contour')

        # set up fields for id/value
        field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
        contour_layer.CreateField(field_defn)

        field_defn = ogr.FieldDefn("value", ogr.OFTReal)
        contour_layer.CreateField(field_defn)

        gdal.ContourGenerate(
            in_band,
            interval,
            offset,
            [],
            0,
            0,
            contour_layer,
            0,
            1
        )

        del contour_layer
        del contour_datasource
        vector_ds = gdal.OpenEx(vec_filename, gdal.OF_VECTOR)
        if format == 'raster':
            vector_layer = vector_ds.GetLayer(0)

            xmin, xres, _, ymax, _, yres = data.GetGeoTransform()
            xmax = xmin + (data.RasterXSize * xres)
            ymin = ymax + (data.RasterYSize * yres)
            gdal.Rasterize(
                out_filename,
                vector_ds,
                width=data.RasterXSize,
                height=data.RasterYSize,
                format='GTiff',
                attribute='value',
                layers=[vector_layer.GetName()],
                outputType=gdal.GDT_Float32,
                initValues=fill_value,
                xRes=xres,
                yRes=yres,
                outputBounds=[xmin, ymin, xmax, ymax],
            )

            out_data = gdal.Open(out_filename)
        elif format == 'vector':
            out_data = vector_ds
    except Exception:
        gdal.Unlink(out_filename)
    finally:
        vector_driver.DeleteDataSource(vec_filename)

    return out_data


def pansharpen(pan_ds, *spectral_dss):
    spectral_band_xml = ''.join(
        '<SpectralBand dstBand="%d"></SpectralBand>' % (i + 1)
        for i in range(len(spectral_dss))
    )
    ds = gdal.CreatePansharpenedVRT(
        """
        <VRTDataset subClass="VRTPansharpenedDataset">
            <PansharpeningOptions>
                %s
            </PansharpeningOptions>
        </VRTDataset>
        """ % spectral_band_xml,
        pan_ds.GetRasterBand(1), [
            spectral_ds.GetRasterBand(1) for spectral_ds in spectral_dss
        ]
    )

    out_ds = gdal_array.OpenNumPyArray(ds.ReadAsArray(), True)
    # restore original nodata from pan band to output ds
    nodata_value = pan_ds.GetRasterBand(1).GetNoDataValue()
    if nodata_value is not None:
        for i in range(out_ds.RasterCount):
            out_ds.GetRasterBand(i + 1).SetNoDataValue(nodata_value)

    return out_ds


def percentile(ds, perc, default=0):
    band = ds.GetRasterBand(1)
    histogram = band.GetDefaultHistogram()
    if histogram:
        min_, max_, _, buckets = histogram
        bucket_diff = (max_ - min_) / len(buckets)
        cumsum = np.cumsum(buckets)
        bucket_index = np.searchsorted(cumsum, cumsum[-1] * (perc / 100))
        return min_ + (bucket_index * bucket_diff)
    return default


def _has_stats(band):
    return 'STATISTICS_MINIMUM' in band.GetMetadata()

def statistics_min(ds, default=0):
    band = ds.GetRasterBand(1)
    if _has_stats(band):
        min_, _, _, _ = band.GetStatistics(True, False)
        return min_
    return default


def statistics_max(ds, default=0):
    band = ds.GetRasterBand(1)
    if _has_stats(band):
        _, max_, _, _ = band.GetStatistics(True, False)
        return max_
    return default

def statistics_mean(ds, default=0):
    band = ds.GetRasterBand(1)
    if _has_stats(band):
        _, _, mean, _ = band.GetStatistics(True, False)
        return mean
    return default


def statistics_stddev(ds, default=0):
    band = ds.GetRasterBand(1)
    if _has_stats(band):
        _, _, _, stddev = band.GetStatistics(True, False)
        return stddev
    return default


def interpolate(
        ds:gdal.Dataset, x1:Numeric, x2:Numeric, y1:Numeric, y2:Numeric, clip:bool=False, nodata_range:List[Numeric]=None
    ):
    """Perform linear interpolation for x between (x1,y1) and (x2,y2) with
    optional clamp and additional masking out multiple no data value ranges

    Args:
        ds (gdal.Dataset): input gdal dataset
        x1 (Numeric): linear interpolate from min
        x2 (Numeric): linear interpolate from max
        y1 (Numeric): linear interpolate to min
        y2 (Numeric): linear interpolate to max
        clip (bool, optional): if set to True, performs clip (values below y1 set to y1, values above y2 set to y2). Defaults to False.
        additional_no_data (List, optional): additionally masks out (sets to band no_data_value) a range of values. Defaults to []. Example [1,5]

    Returns:
        gdal.Dataset: Interpolated dataset
    """
    band = ds.GetRasterBand(1)
    nodata_value = band.GetNoDataValue()
    orig_image = band.ReadAsArray()
    # NOTE: the interpolate formula uses large numbers which lead to overflows on uint16
    if orig_image.dtype != convert_dtype(orig_image.dtype):
        orig_image = orig_image.astype(convert_dtype(orig_image.dtype))
    interpolated_image = ((y2 - y1) * orig_image + x2 * y1 - x1 * y2) / (x2 - x1)
    if clip:
        # clamp values below min to min and above max to max
        np.clip(interpolated_image, y1, y2, out=interpolated_image)
    if nodata_value is not None:
        # restore nodata pixels on interpolated array from original array
        interpolated_image[orig_image == nodata_value] = nodata_value
        if nodata_range:
            # apply mask of additional nodata ranges from original array on interpolated array
            interpolated_image[(orig_image >= nodata_range[0]) & (orig_image <= nodata_range[1])] = nodata_value

    ds = gdal_array.OpenNumPyArray(interpolated_image, True)
    if nodata_value is not None:
        ds.GetRasterBand(1).SetNoDataValue(nodata_value)
    return ds


def wrap_numpy_func(function):
    @wraps(function)
    def inner(ds, *args, **kwargs):
        band = ds.GetRasterBand(1)
        data = band.ReadAsArray()
        function(data, *args, **kwargs)
        band.WriteArray(data)
        return ds
    return inner


function_map = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'arcsin': np.arcsin,
    'arccos': np.arccos,
    'arctan': np.arctan,
    'hypot': np.hypot,
    'arctan2': np.arctan2,
    'degrees': np.degrees,
    'radians': np.radians,
    'unwrap': np.unwrap,
    'deg2rad': np.deg2rad,
    'rad2deg': np.rad2deg,
    'sinh': np.sinh,
    'cosh': np.cosh,
    'tanh': np.tanh,
    'arcsinh': np.arcsinh,
    'arccosh': np.arccosh,
    'arctanh': np.arctanh,
    'exp': np.exp,
    'expm1': np.expm1,
    'exp2': np.exp2,
    'log': np.log,
    'log10': np.log10,
    'log2': np.log2,
    'log1p': np.log1p,
    'hillshade': hillshade,
    'slopeshade': slopeshade,
    'aspect': aspect,
    'tri': tri,
    'tpi': tpi,
    'roughness': roughness,
    'contours': contours,
    'pansharpen': pansharpen,
    'percentile': percentile,
    'statistics_min': statistics_min,
    'statistics_max': statistics_max,
    'statistics_mean': statistics_mean,
    'statistics_stddev': statistics_stddev,
    'interpolate': interpolate,
}


def get_function(name):
    func = function_map.get(name)
    if not func:
        raise ValueError(
            'Invalid function %s, available functions are %s'
            % (name, ', '.join(function_map.keys()))
        )
    return func


buffer_map = {
    'hillshade': 1,
    'slopeshade': 1,
}


def get_buffer(name):
    return buffer_map.get(name, 0)
