#!/usr/bin/env python
#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Simple CLI tool to compare files with GDAL.
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

import sys

def extent_from_ds(ds):
    gt = ds.GetGeoTransform()
    size_x = ds.RasterXSize
    size_y = ds.RasterYSize
    
    return (gt[0],                   # minx
            gt[3] + size_x * gt[5],  # miny
            gt[0] + size_y * gt[1],  # maxx
            gt[3])                   # maxy


def resolution_from_ds(ds):
    gt = ds.GetGeoTransform()
    return (abs(gt[1]), abs(gt[5]))


def compare_files(filename1, filename2):
    import filecmp, os
    
    try:
        os.stat(filename1)
    except OSError:
        raise Exception("Error while reading '%s'." % filename1)
    
    try:
        os.stat(filename2)
    except OSError:
        raise Exception("Error while reading '%s'." % filename2)

    if filecmp.cmp(filename2,filename1,0):
        return True
    
    try:
        try:
            from osgeo import gdal
            from osgeo.osr import SpatialReference
        except ImportError:
            import gdal
            from osr import SpatialReference
        
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        file1 = gdal.Open(filename1)
        gdal.PopErrorHandler()
        if file1 == None:
            raise Exception("Error while reading '%s' via GDAL." % filename1)
        file2 = gdal.Open(filename2)
        gdal.PopErrorHandler()
        if file2 == None:
            raise Exception("Error while reading '%s' via GDAL." % filename2)
        
        # Check image checksums
        print "Checking checksums..."
        
        for band_num in range(1,file2.RasterCount+1):
            if file1.GetRasterBand(band_num).Checksum() != \
               file2.GetRasterBand(band_num).Checksum():
                raise Exception("Checksum of band '%s' differs: '%s' != '%s'." \
                                % (band_num, \
                                file1.GetRasterBand(band_num).Checksum(), \
                                file2.GetRasterBand(band_num).Checksum()))
            else:
                print "Checksum of band '%s' matches and is '%s'." % \
                      (band_num, file1.GetRasterBand(band_num).Checksum())
        
        # Check image size
        print "Checking size..."
        
        if file1.RasterXSize != file2.RasterXSize or \
           file1.RasterYSize != file2.RasterYSize:
            raise Exception("Size differs: '%s x %s' != '%s x %s'." % \
                            (file1.RasterXSize, file1.RasterYSize, 
                             file2.RasterXSize, file2.RasterYSize))
        
        # Check extent
        print "Checking extent..."
        
        EPSILON = 1e-8
        extent1 = extent_from_ds(file1)
        extent2 = extent_from_ds(file2)
        if max([
            abs(extent1[i] - extent2[i]) for i in range(0, 4)
        ]) >= EPSILON:
            raise Exception("Extent differs: '%s' != '%s'." % \
                            ((', '.join(map(str, extent1))), 
                             (', '.join(map(str, extent2)))))
        
        # Check resolution
        print "Checking resolution..."
        
        resolution1 = resolution_from_ds(file1)
        resolution2 = resolution_from_ds(file2)
        if resolution1[0] != resolution2[0] or resolution1[1] != resolution2[1]:
            raise Exception("Resolution differs: '%s' != '%s'." % \
                            ((', '.join(map(str, resolution1))), 
                             (', '.join(map(str, resolution2)))))
        
        # Check projection
        print "Checking projection..."
        
        if file1.GetProjection() != file2.GetProjection():
            raise Exception("Projection differs.")
        
        # Check GCPs
        print "Checking GCPs..."
        
        if file1.GetGCPCount() != file2.GetGCPCount():
            raise Exception("Number of GCPs differs: '%s' != '%s'." % \
                            (file1.GetGCPCount(), file2.GetGCPCount()))
        
        # Check GCP projection
        print "Checking GCP projection..."
        
        if file1.GetGCPProjection() != file2.GetGCPProjection():
            raise Exception("GCP projection differs.")
        
        # Check metadata
        print "Checking metadata..."
        
        file1_md = file1.GetMetadata()
        file2_md = file2.GetMetadata()

        if file1_md.keys() != file2_md.keys():
            raise Exception("Metadata keys don't match.")
        
        diffkeys = [k for k in file1_md if file1_md[k] != file2_md[k]]
        error = ""
        for k in diffkeys:
            error += "    %s: %s != %s\n" % (k, file1_md[k], file2_md[k])
        if len(diffkeys) > 0:
            raise Exception("Metadata not equal:\n%s" % error)
    
    except Exception as e:
        raise Exception("Comparison via GDAL failed: '%s'" % e)


if __name__ == "__main__":
    
    try:
        src0 = sys.argv[1]
        src1 = sys.argv[2]
        print "< FILE: %s" % src0
        print "> FILE: %s" % src1
    except:
        sys.stderr.write("ERROR: Not enough input arguments!\n")
        sys.stderr.write("USAGE: %s <filename> <filename>\n" % sys.argv[0])
        sys.exit(1)
    
    try:
        compare_files(src0, src1)
    except Exception as e:
        sys.stderr.write("ERROR: %s\n" % str(e))
        sys.exit(1)
    
    print "OK - Files match."
    sys.exit(0)
