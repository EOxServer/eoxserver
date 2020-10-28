from uuid import uuid4

from eoxserver.contrib import gdal, osr
from eoxserver.resources.coverages import crss


def create_mem_ds(width, height, data_type):
    driver = gdal.GetDriverByName('MEM')
    return driver.Create('', width, height, 1, data_type)


def warp_fields(coverages, field_name, bbox, crs, width, height):
    driver = gdal.GetDriverByName('MEM')
    out_ds = driver.Create(
        '',
        width,
        height,
        1,
        coverages[0].range_type.get_field(field_name).data_type
    )

    out_ds.SetGeoTransform([
        bbox[0],
        (bbox[2] - bbox[0]) / width,
        0,
        bbox[3],
        0,
        -(bbox[3] - bbox[1]) / height,
    ])
    epsg = crss.parseEPSGCode(crs, [crss.fromShortCode])
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg)

    out_ds.SetProjection(sr.ExportToWkt())

    for coverage in coverages:
        location = coverage.get_location_for_field(field_name)
        band_index = coverage.get_band_index_for_field(field_name)

        orig_ds = gdal.open_with_env(location.path, location.env)

        vrt_filename = None
        if orig_ds.RasterCount > 1:
            vrt_filename = '/vsimem/' + uuid4().hex
            gdal.BuildVRT(vrt_filename, orig_ds, bandList=[band_index])
            ds = gdal.Open(vrt_filename)
        else:
            ds = orig_ds

        gdal.Warp(out_ds, ds)
        ds = None

        if vrt_filename:
            gdal.Unlink(vrt_filename)

    band = out_ds.GetRasterBand(1)
    return band.ReadAsArray()
