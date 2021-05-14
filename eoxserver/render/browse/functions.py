from contextlib import contextmanager
from uuid import uuid4

import numpy as np

from eoxserver.contrib import gdal
from eoxserver.contrib import gdal_array


__all__ = [
    'get_function',
    'get_buffer',
]


@contextmanager
def temp_ds(*args, **kwargs):
    filename = '/vsimem/%s.tif' % uuid4().hex
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(filename, *args, **kwargs)
    yield ds
    del ds
    gdal.Unlink(filename)


def hillshade(in_data, zfactor=1, scale=1, azimuth=315, altitude=45, alg='Horn'):
    in_ds = gdal_array.OpenNumPyArray(in_data)
    with temp_ds(in_ds.RasterXSize, in_ds.RasterYSize, 3) as out_ds:
        gdal.DEMProcessing(
            out_ds.GetFileList()[0],
            in_ds,
            'hillshade',
            zFactor=zfactor,
            scale=scale,
            azimuth=azimuth,
            altitude=altitude,
            alg=alg,
        )

        band = out_ds.GetRasterBand(1)
        out_data = band.ReadAsArray()
        del out_ds

    return out_data


def slopeshade(in_data, scale=1, alg='Horn'):
    in_ds = gdal_array.OpenNumPyArray(in_data)
    with temp_ds() as out_ds:
        gdal.DEMProcessing(
            out_ds.GetFileList()[0],
            in_ds,
            'slope',
            scale=scale,
            alg=alg,
        )

        band = out_ds.GetRasterBand(1)
        out_data = band.ReadAsArray()
        del out_ds

    return out_data


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
}

# TODO: find out really required buffer values
buffer_map = {
    'hillshade': 5,
    'slopeshade': 5,
}


def get_function(name):
    func = function_map.get(name)
    if not func:
        raise ValueError(
            'Invalid function %s, available functions are %s'
            % (name, ', '.join(function_map.keys()))
        )
    return func


def get_buffer(name):
    return buffer_map.get(name, 0)
