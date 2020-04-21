from eoxserver.contrib import vrt, gdal, osr

import numpy as np
import rasterio
import rasterio.transform
import rasterio.warp


#.from_bounds


def create_mem_ds(width, height, data_type):
    driver = gdal.GetDriverByName('MEM')
    return driver.Create('', width, height, 1, data_type)


def warp_fields(coverages, field_name, bbox, crs, width, height):
    transform = rasterio.transform.from_bounds(
        bbox[0], bbox[1], bbox[2], bbox[3], width, height
    )
    dst = np.zeros((height, width), np.float64)
    for coverage in coverages:
        location = coverage.get_location_for_field(field_name)
        band_index = coverage.get_band_index_for_field(field_name)

        # o_x = bbox[0]
        # o_y = bbox[3]
        # res_x = (bbox[2] - bbox[0]) / width
        # res_y = -(bbox[3] - bbox[1]) / height

        with rasterio.Env(**location.env):
            with rasterio.open(location.path) as in_ds:
                in_band = rasterio.band(in_ds, band_index)
                # out_ds = rasterio.open(
                #     '', 'w', driver='MEM', count=1, dtype=in_band.dtype,
                #     transform=transform, width=width, height=height, crs=crs
                # )
                # out_band = rasterio.band(out_ds, 1)

                # np.dtype(in_band.dtype))
                rasterio.warp.reproject(
                    in_band, dst, dst_transform=transform, dst_crs=crs
                )

    # # in_ds = gdal.open_with_env(location.path, location.env)
    # out_ds = create_mem_ds(
    #     width,
    #     height,
    #     in_ds.GetRasterBand(band_index).DataType
    # )
    # out_ds.SetGeoTransform([o_x, res_x, 0, o_y, 0, res_y])
    # out_ds.SetProjection(osr.SpatialReference(crs).wkt)

    # gdal.Warp(out_ds, in_ds.GetRasterBand(band_index))
    return dst


def stack_datasets(datasets):
    pass
