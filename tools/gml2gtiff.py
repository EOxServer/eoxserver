#!/usr/bin/env python
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

from argparse import ArgumentParser
from decimal import Decimal

from osgeo import gdal, osr
import numpy
from lxml import etree

"""
    Helper functions to namespaceify xml tag names
"""
def ns_gml(string):
    return "{http://www.opengis.net/gml/3.2}%s" % string

def ns_swe(string):
    return "{http://www.opengis.net/swe/2.0}%s" % string

def ns_gmlcov(string):
    return "{http://www.opengis.net/gmlcov/1.0}%s" % string

"""
    Setup and parse user arguments.
"""
parser = ArgumentParser(prog = "gml2gtiff")
parser.add_argument("-m", "--map", dest = "map")
parser.add_argument("input", help = "the path to the input GML file")
parser.add_argument("output", help = "the path to the output GTiff file")
options = parser.parse_args()

"""
    Parse the XML file into an ElementTree structure
"""
f = open(options.input)
tree = etree.parse(f)
root = tree.getroot()

coverageid = root.get(ns_gml("id"))

"""
    Assert that we are dealing with a two dimensional image and find out
    width and height.
"""
assert(root.find(ns_gml("domainSet/")
                 + ns_gml("RectifiedGrid")
                 ).get("dimension") == "2")
width, height = root.findtext(ns_gml("domainSet/")
                              + ns_gml("RectifiedGrid/")
                              + ns_gml("limits/")
                              + ns_gml("GridEnvelope/")
                              + ns_gml("high")
                              ).split(" ")

width = int(width) + 1
height = int(height) + 1

"""
    Find out the number of the bands and their metadata.
"""
bands = []
for band in root.findall(ns_gmlcov("rangeType/")
                         + ns_swe("DataRecord/")
                         + ns_swe("field")):
    bandinfo = {}
    bandinfo['band_name'] = band.get("name")
    bandinfo['band_uom'] = band.find(ns_swe("Quantity/")
                                     + ns_swe("uom")
                                     ).get("code")
    bandinfo['band_interval'] = band.findtext(ns_swe("Quantity/")
                                              + ns_swe("constraint/")
                                              + ns_swe("AllowedValues/")
                                              + ns_swe("interval"))
    bandinfo['band_definition'] = band.find(ns_swe("Quantity")
                                            ).get("definition")
    bandinfo['band_description'] = band.findtext(ns_swe("Quantity/")
                                                 + ns_swe("description"))
    significant_figures = band.findtext(ns_swe("Quantity/")
                                        + ns_swe("constraint/")
                                        + ns_swe("AllowedValues/")
                                        + ns_swe("significantFigures"))
    if significant_figures is not None:
        bandinfo['significant_figures'] = int(significant_figures)

    bands.append(bandinfo)

"""
    Get the tuple list and transform the strings to actual float values.
"""
band_values = [ [] for i in range(len(bands)) ]

tuples = root.findtext(ns_gml("rangeSet/")
                       + ns_gml("DataBlock/")
                       + ns_gml("tupleList")
                       ).split(" ")

for tup in tuples:
    values = tup.split(",")
    assert(len(values) == len(bands))
    for index, value in enumerate(values):
        band_values[index].append(float(value))

        # find out significant figures
        e = abs(Decimal(value).as_tuple().exponent)
        try:
            if bands[index]['significant_figures'] < e:
                bands[index]['significant_figures'] = e
        except KeyError:
            bands[index]['significant_figures'] = e

"""
    Create a numpy array for each band, using the float list for each
    band.
"""
band_arrays = [numpy.array(band_value).reshape(height, width)
                    for band_value in band_values]

"""
    Create a new GDAL dataset. We are using GTiff, but any other might
    be fine also.
"""
driver = gdal.GetDriverByName("GTiff")
ds = driver.Create(options.output, int(width), int(height),
                   len(bands), gdal.GDT_Float32)

"""
    Write all tuple values into the raster band.
"""
for i in range(len(bands)):
    rb = ds.GetRasterBand(i + 1)
    rb.WriteArray(band_arrays[i])

"""
    To set the projection, create a osr.SpatialReference, load the EPSG
    into it and export it as WKT to set as projection in the dataset.
"""
srs = root.find(ns_gml("boundedBy/")
                + ns_gml("Envelope")
                ).get("srsName")

epsg = int(srs.split("/")[-1])

sr = osr.SpatialReference()
sr.ImportFromEPSG(epsg)
wkt = sr.ExportToWkt()
ds.SetProjection(wkt)

"""
    Create a textual representation of the extent.
"""

extent = "%s %s" % (root.findtext(ns_gml("boundedBy/")
                                  + ns_gml("Envelope/")
                                  + ns_gml("lowerCorner")
                                  ),
                    root.findtext(ns_gml("boundedBy/")
                                  + ns_gml("Envelope/")
                                  + ns_gml("upperCorner")
                                  )
                    )

"""
    To set the geotransform, find out the origin and the two offset
    vectors.
"""
origin = [float(string) for string in
                                root.findtext(ns_gml("domainSet/")
                                              + ns_gml("RectifiedGrid/")
                                              + ns_gml("origin/")
                                              + ns_gml("Point/")
                                              + ns_gml("pos")
                                              ).split(" ")]

offsets = root.findall(ns_gml("domainSet/")
                       + ns_gml("RectifiedGrid/")
                       + ns_gml("offsetVector"))

offset1 = [float(string) for string in offsets[0].text.split(" ")]
offset2 = [float(string) for string in offsets[1].text.split(" ")]

gt = (
    origin[0],
    offset1[0],
    offset1[1],
    origin[1],
    offset2[0],
    offset2[1],
)
ds.SetGeoTransform(gt)

"""
    Is the creation of a map requested? If yes, create and save it.
"""
if options.map is not None:
    from mapscript import (
        mapObj, layerObj, outputFormatObj,
        MS_IMAGEMODE_FLOAT32, MS_ON, MS_LAYER_RASTER
    )

    # create a new map object
    map = mapObj()
    map.setProjection("init=epsg:%d" % epsg)
    map.setMetaData("ows_enable_request", "*")

    # create new layer
    layer = layerObj(map)
    layer.name = coverageid
    layer.data = options.output
    layer.status = MS_ON
    layer.type = MS_LAYER_RASTER
    layer.setProjection("init=epsg:%d" % epsg)
    layer.setMetaData("wcs_srs", "epsg:%d" % epsg)
    layer.setMetaData("wcs_extent", extent)
    layer.setMetaData("wcs_size", "%d %d" % (width, height))
    layer.setMetaData("wcs_default_format", "application/gml+xml")

    # set band metadata
    layer.setMetaData("wcs_bandcount", str(len(bands)))
    layer.setMetaData("wcs_band_names", " ".join([band['band_name'] for band in bands]))
    for band in bands:
        for key, value in band.items():
            if value is None or key == "band_name":
                continue
            layer.setMetaData("%s_%s" % (band['band_name'], key), str(value))

    # append GML outputformat
    format = outputFormatObj("GDAL/GTiff", "GML")
    format.setExtension("xml")
    format.setMimetype("application/gml+xml")
    format.imagemode = MS_IMAGEMODE_FLOAT32
    map.appendOutputFormat(format)

    #save the map to the disk
    map.save(options.map)
