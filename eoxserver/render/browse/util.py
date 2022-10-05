from uuid import uuid4

from eoxserver.contrib import gdal, osr
from eoxserver.resources.coverages import crss


def create_mem_ds(width, height, data_type):
    driver = gdal.GetDriverByName('MEM')
    return driver.Create('', width, height, 1, data_type)


def warp_fields(coverages, field_name, bbox, crs, width, height):
    driver = gdal.GetDriverByName('MEM')
    field = coverages[0].range_type.get_field(field_name)
    out_ds = driver.Create(
        '',
        width,
        height,
        1,
        field.data_type
    )
    nil_value = None
    band = out_ds.GetRasterBand(1)
    if field.nil_values:
        nil_value = float(field.nil_values[0][0])
        band.SetNoDataValue(nil_value)
        band.Fill(nil_value)

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

    # set initial statistics
    stats = coverages[0].get_statistics_for_field(field_name)
    if stats:
        band.SetStatistics(
            stats.minimum or 0,
            stats.maximum or 0,
            stats.mean or 0,
            stats.stddev or 0,
        )
        histogram = stats.histogram
        if histogram:
            band.SetDefaultHistogram(
                histogram.min or 0,
                histogram.max or 0,
                histogram.buckets,
            )

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

        gdal.Warp(out_ds, ds, multithread=True)
        ds = None

        if vrt_filename:
            gdal.Unlink(vrt_filename)

    return out_ds
