#-------------------------------------------------------------------------------
# $Id$
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

import os, os.path
from shutil import copy2
from fnmatch import filter as fnfilter
from osgeo import gdal, osr
import numpy
import math
from xml.dom import minidom

from django.conf import settings

from eoxserver.lib.domainset import EOxSRectifiedGrid, getGridFromFile

def _roundint(f):
    return int(numpy.int_(numpy.rint(f)))

def resample(srid, origin, offsets, raw_imagery_path, output_path, image_pattern):
    data_path = os.path.join(settings.PROJECT_DIR, "examples", "data")
    
    filenames = os.listdir(os.path.join(data_path, raw_imagery_path))
    imgs = fnfilter(filenames, image_pattern)

    
    for img in imgs:
        src_path = os.path.join(data_path, raw_imagery_path, img)
        src = gdal.Open(src_path)
        
        src_grid = getGridFromFile(src_path)
        src_minx, src_miny, src_maxx, src_maxy = src_grid.getExtent2D()
        
        src_x_min = _roundint(math.floor((src_minx - origin[0]) / offsets[0][0]))
        src_y_min = _roundint(math.floor((src_maxy - origin[1]) / offsets[1][1]))
        src_x_max = _roundint(math.ceil((src_maxx - origin[0]) / offsets[0][0]))
        src_y_max = _roundint(math.ceil((src_miny - origin[1]) / offsets[1][1]))
        
        x_size = src_x_max - src_x_min + 1
        y_size = src_y_max - src_y_min + 1
        
        dst_path = os.path.join(data_path, output_path, "mosaic_%s" % img)
        driver = gdal.GetDriverByName('GTiff')
        dst = driver.Create(dst_path, x_size, y_size, 3)
        gt = [origin[0] + float(src_x_min) * offsets[0][0], offsets[0][0], 0.0,
              origin[1] + float(src_y_min) * offsets[1][1], 0.0, offsets[1][1]]
        dst.SetGeoTransform(gt)
        dst.SetProjection(src.GetProjection())
        
        gdal.ReprojectImage(src, dst)

def resampleImage2009():    
    mosaic_grid = EOxSRectifiedGrid(
        srid = 3035,
        low = (0, 0),
        high = (1492, 899),
        origin = (4208500.0, 2948000.0),
        offsets = ((500.0, 0.0), (0.0, -500.0)),
    )
    
    resample(
        mosaic_grid.srid, mosaic_grid.origin, mosaic_grid.offsets,
        "image2009", "image2009_mosaic_resampled", "*.tiff"
    )

def resampleMERIS():
    srid = 4326
    origin = (-3.75,46.3)
    offsets = ((0.0031355,0.0),(0.0,-0.0031355))
    
    resample(srid, origin, offsets, "meris/MER_FRS_1P_RGB", "meris/mosaic_MER_FRS_1P_RGB", "*.tif")

def resampleMERISreduced():
    srid = 4326
    origin = (-3.75,46.3)
    offsets = ((0.031355,0.0),(0.0,-0.031355))

    resample(srid, origin, offsets, "meris/MER_FRS_1P_reduced_RGB", "meris/mosaic_MER_FRS_1P_reduced_RGB", "*.tif")

