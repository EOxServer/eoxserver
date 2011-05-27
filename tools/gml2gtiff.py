#!/usr/bin/env python
#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl, Fabian Schindler
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from osgeo import gdal, osr
try:
  from lxml import etree
except ImportError:
  try:
    import xml.etree.cElementTree as etree
  except ImportError:
    try:
      import xml.etree.ElementTree as etree
    except ImportError:
      try:
        import cElementTree as etree
      except ImportError:
        try:
          import elementtree.ElementTree as etree
        except ImportError:
          print("Failed to import ElementTree from any known place")
import sys
import numpy

gml = "http://www.opengis.net/gml/3.2"

def ns(ns, string):
	"""
		Helper function to namespaceify a string for etree.
	"""
	return "{%s}%s" % (ns, string)

if len(sys.argv) != 3:
	print("Usage: gml2gtiff.py INPUT_GML OUTPUT_GTIFF")
	sys.exit(1)

""" 
	Parse the XML file into an ElementTree structure
"""
f = open(sys.argv[1])
tree = etree.parse(f)
root = tree.getroot()

"""
	Assert that we are dealing with a two dimensional image and find out
	width and height.
"""
assert(root.find(ns(gml, "domainSet/") + ns(gml, "RectifiedGrid")).get("dimension") == "2")
width, height = root.findtext(ns(gml, "domainSet/") + ns(gml, "RectifiedGrid/")
							  + ns(gml, "limits/") + ns(gml, "GridEnvelope/")
							  + ns(gml, "high")).split(" ")

width = int(width) + 1
height = int(height) + 1

"""
	Get the tuple list and create an array out of it./home/fabian/wcs_test/tests_wcs20
"""
tuples = [float(string) for string in root.findtext(ns(gml, "rangeSet/")
													+ ns(gml, "DataBlock/")
													+ ns(gml, "tupleList")).split(" ")]

values = numpy.array(tuples).reshape(height, width)

"""
	Create a new GDAL dataset. We are using GTiff, but any other might
	be fine also.
"""
driver = gdal.GetDriverByName("GTiff")
ds = driver.Create(sys.argv[2], int(width), int(height), 1, gdal.GDT_Float32)

"""
	Write all tuple values into the raster band.
"""
rb = ds.GetRasterBand(1)
rb.WriteArray(values)

"""
	To set the projection, create a osr.SpatialReference, load the EPSG
	into it and export it as WKT to set as projection in the dataset.
"""
epsg = int(root.find(ns(gml, "boundedBy/") + ns(gml, "Envelope")).get("srsName").split("/")[-1])

sr = osr.SpatialReference()
sr.ImportFromEPSG(epsg)
ds.SetProjection(sr.ExportToWkt())

"""
	To set the geotransform, find out the origin and the two offset
	vectors.
"""
origin = [float(string) for string in root.findtext(ns(gml, "domainSet/")
													+ ns(gml, "RectifiedGrid/")
													+ ns(gml, "origin/") + ns(gml, "Point/")
													+ ns(gml, "pos")).split(" ")]

offsets = root.findall(ns(gml, "domainSet/") + ns(gml, "RectifiedGrid/")
					      + ns(gml, "offsetVector"))

offset1 = [float(string) for string in offsets[0].text.split(" ")]
offset2 = [float(string) for string in offsets[1].text.split(" ")]

geotransform = (
	origin[0],
	offset1[0],
	offset1[1],
	origin[1],
	offset2[0],
	offset2[1],
)
ds.SetGeoTransform(geotransform)
