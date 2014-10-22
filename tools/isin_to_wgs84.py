#!/usr/bin/python
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

from osgeo import gdal, osr
import numpy as np
import math

import os, os.path

from threading import Thread

import sys

R_E = 6378.137
FAPAR_SUBDATASET_NO = 6

def get_projection_ref():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    return srs.ExportToWkt()


def get_geo_transform(size_x, size_y):
    return [-180.0, 360.0/float(size_x), 0.0,
            90.0,   0.0,                -180.0/float(size_y)]

def compute(data):
    # create the array for the reprojected data
    rp_data = np.zeros(data.shape)

    r_e = R_E # earth radius (km)
    n_lat = data.shape[0] # number of latitudinal rows
    N = data.shape[1] # number of columns in the reprojected data
    d_r = math.pi * r_e / float(n_lat) # latitudinal bin width (km)
    delta_phi = math.pi / float(n_lat) # latitudinal discretization angle (km)

    n = np.arange(n_lat)

    phi = - math.pi / 2.0 + delta_phi / 2.0 + np.float_(n) * delta_phi # center latitude of the row
    p = r_e * np.cos(phi) # local perimeter of the row (km)
    n_lon = 2 * np.round(math.pi * p / d_r) # number of columns in the row

    rp_left =  math.pi * ( np.arange(N) / float(N) - 1.0 )
    rp_right = np.zeros(N)
    rp_right[0:N-1] = rp_left[1:N]
    rp_right[N-1] = math.pi

    for iy in range(0, n_lat):
        print iy

        left = np.zeros(N)
        left[(N / 2 - n_lon[iy] / 2):(N / 2 + n_lon[iy] / 2)] = \
            math.pi * ( np.arange(n_lon[iy]) / n_lon[iy] - 1.0 )
        right = np.zeros(N)
        right[(N / 2 - n_lon[iy] / 2):(N / 2 + n_lon[iy] / 2 - 1)] =\
            left[(N / 2 - n_lon[iy] / 2 + 1):(N / 2 + n_lon[iy] / 2)]
        right[N / 2 + n_lon[iy] / 2 - 1] = math.pi

        k_min = np.int_(np.floor( float(n_lon[iy]) / float(N) * np.arange(N) + (N - n_lon[iy]) / 2 ))

        for j in range(0, N):
            k = k_min[j]

            if left[k] <= rp_left[j] and rp_right[j] <= right[k]:
                rp_data[iy][j] = data[iy][k]
            elif left[k] <= rp_left[j] and rp_right[j] > right[k]:
                rp_data[iy][j] = float(N) / math.pi * ((right[k] - rp_left[j]) * data[iy][k] + (rp_right[j] - right[k]) * data[iy][k+1])

    return rp_data

def reproject(ds, out_path):

    # read the raster data
    data = ds.GetRasterBand(1).ReadAsArray()

    # get the size of the image
    size_y, size_x = data.shape

    # create a GeoTiff file
    driver = gdal.GetDriverByName("GTiff")

    out_ds = driver.Create(out_path, size_x, size_y, 1, gdal.GDT_Byte)

    if out_ds is None:
        print "Could not create output file '%s'." % out_path
    else:
        # set the geospatial metadata
        proj = get_projection_ref()
        gt = get_geo_transform(size_x, size_y)

        out_ds.SetProjection(proj)
        out_ds.SetGeoTransform(gt)

        # write the computed / reprojected data to the file
        rp_data = compute(data)
        out_ds.GetRasterBand(1).WriteArray(rp_data)

def run(args):
    threads = []

    for arg in args:

        # open the file
        dataset = gdal.Open(arg)

        if dataset is None:
            print "Could not open file '%s'." % arg
        else:

            # determine the FAPAR subdataset
            fapar_subdataset_name = dataset.GetSubDatasets()[FAPAR_SUBDATASET_NO][0]

            # open the FAPAR subdataset
            fapar_subdataset = gdal.Open(fapar_subdataset_name)

            if fapar_subdataset is not None:
                # create the output dataset name
                out_path = "%s.%s" % (os.path.splitext(arg)[0], "tiff")

                # start the thread
                thread = Thread(target=reproject, args=(fapar_subdataset, out_path))

                thread.start()

            else:
                print "Could not open FAPAR subdataset '%s'." %\
                    fapar_subdataset_name

    for thread in threads:
        thread.join()

    exit(0)

if __name__ == "__main__":
    run(sys.argv[1:])
