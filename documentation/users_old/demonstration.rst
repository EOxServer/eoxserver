.. Demonstration
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 EOX IT Services GmbH
  #
  # Permission is hereby granted, free of charge, to any person obtaining a copy
  # of this software and associated documentation files (the "Software"), to
  # deal in the Software without restriction, including without limitation the
  # rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
  # sell copies of the Software, and to permit persons to whom the Software is
  # furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies of this Software or works derived from this Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
  # IN THE SOFTWARE.
  #-----------------------------------------------------------------------------

.. index::
   single: Demonstration

.. _Demonstration:

Demonstration
=============

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

The EOxServer demonstration is an instantiation of the :ref:`autotest instance 
<Autotest>` and is based on the Envisat MERIS sample data available `here 
<http://earth.esa.int/object/index.cfm?fobjectid=4320>`_.

The configuration includes one DatasetSeries and one StitchedMosaic both
combining the three available datasets:

* DatasetSeries (EOId: MER_FRS_1P_reduced) containing the 3 MERIS sample
  datasets with all 15 radiance bands encoded as uint16 values
* StitchedMosaic (CoverageId: mosaic_MER_FRS_1P_reduced_RGB) containing
  the 3 MERIS sample datasets reduced to RGB 8-bit

Note, the data has been reduced from 300m resolution to 3000m.

The demonstration tries to show the usage of all available 
:ref:`EO-WCS request parameters <EO-WCS Request Parameters>`.

.. index::
   single: GetCapabilities (Demonstration)

GetCapabilities
---------------

`GetCapabilities <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCapabilities>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCapabilities

Interesting parts of the repsonse:

* Advertising EO-WCS:

  .. code-block:: xml

    <ows:Profile>http://www.opengis.net/spec/WCS_application-profile_earth-observation/1.0/conf/eowcs</ows:Profile>

* The additional EO-WCS operation:

  .. code-block:: xml

    <ows:Operation name="DescribeEOCoverageSet">
        <ows:DCP>
            <ows:HTTP>
                <ows:Get xlink:href="http://eoxserver.org/demo_stable/ows?" xlink:type="simple"/>
                <ows:Post xlink:href="http://eoxserver.org/demo_stable/ows?" xlink:type="simple">
                    <ows:Constraint name="PostEncoding">
                        <ows:AllowedValues>
                            <ows:Value>XML</ows:Value>
                        </ows:AllowedValues>
                    </ows:Constraint>
                </ows:Post>
            </ows:HTTP>
        </ows:DCP>
    </ows:Operation>

* The server will limit the number of CoverageDescription elements in DescribeEOCoverageSet responses:

  .. code-block:: xml

    <ows:Constraint name="CountDefault">
        <ows:NoValues/>
        <ows:DefaultValue>100</ows:DefaultValue>
    </ows:Constraint>

* There is a StitchedMosaic available:

  .. code-block:: xml

    <wcs:CoverageSummary>
        <wcs:CoverageId>mosaic_MER_FRS_1P_reduced_RGB</wcs:CoverageId>
        <wcs:CoverageSubtype>RectifiedStitchedMosaic</wcs:CoverageSubtype>
    </wcs:CoverageSummary>

* There is a DatasetSeries available:

  .. code-block:: xml

    <wcseo:DatasetSeriesSummary>
        <ows:WGS84BoundingBox>
            <ows:LowerCorner>-3.43798100 32.26454100</ows:LowerCorner>
            <ows:UpperCorner>27.96859100 46.21844500</ows:UpperCorner>
        </ows:WGS84BoundingBox>
        <wcseo:DatasetSeriesId>MER_FRS_1P_reduced</wcseo:DatasetSeriesId>
        <gml:TimePeriod gml:id="MER_FRS_1P_reduced_timeperiod">
            <gml:beginPosition>2006-08-16T09:09:29</gml:beginPosition>
            <gml:endPosition>2006-08-30T10:13:06</gml:endPosition>
        </gml:TimePeriod>
    </wcseo:DatasetSeriesSummary>

.. index::
   single: DescribeCoverage (Demonstration)

DescribeCoverage
----------------

`DescribeCoverage StitchedMosaic <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeCoverage&coverageid=mosaic_MER_FRS_1P_reduced_RGB>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=DescribeCoverage&
        coverageid=mosaic_MER_FRS_1P_reduced_RGB
    
`DescribeCoverage Dataset <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=DescribeCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed

.. index::
   single: DescribeEOCoverageSet (Demonstration)

DescribeEOCoverageSet
---------------------

Dataset
~~~~~~~

`DescribeEOCoverageSet Dataset <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeEOCoverageSet&EOId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed>`_::

    http://eoxserver.org/demo_stable/ows?
            service=wcs&
            version=2.0.1&
            request=DescribeEOCoverageSet&
            EOId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed

StitchedMosaic
~~~~~~~~~~~~~~

`DescribeEOCoverageSet StitchedMosaic (4 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_reduced_RGB>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_reduced_RGB

`DescribeEOCoverageSet StitchedMosaic, subset in time (3 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_reduced_RGB&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_reduced_RGB&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")

`DescribeEOCoverageSet StitchedMosaic, subset in Lat and Long, containment contains (1 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_reduced_RGB&subset=Lat(32,47)&subset=Long(11,33)&containment=contains>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_reduced_RGB&
        subset=Lat(32,47)&
        subset=Long(11,33)&
        containment=contains

`DescribeEOCoverageSet StitchedMosaic, returned CoverageDescriptions limited to 2 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_reduced_RGB&count=2>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_reduced_RGB&
        count=2

DatasetSeries
~~~~~~~~~~~~~~

`DescribeEOCoverageSet DatasetSeries (5 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=describeeocoverageset&eoid=MER_FRS_1P_reduced>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced

`DescribeEOCoverageSet DatasetSeries, trim subset in time (4 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")

`DescribeEOCoverageSet DatasetSeries, slice subset in time (2 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-22T09:20:58Z%22)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-22T09:20:58Z")

`DescribeEOCoverageSet DatasetSeries, trim subset in time trim, containment contains (2 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)&containment=contains>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&
        containment=contains

`DescribeEOCoverageSet DatasetSeries, subset in Lat and Long (5 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=Lat(32,47)&subset=Long(11,33)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=Lat(32,47)&
        subset=Long(11,33)

`DescribeEOCoverageSet DatasetSeries, subset in Lat and Long, containment contains (2 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=Lat(32,47)&subset=Long(11,33)&containment=contains>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=Lat(32,47)&
        subset=Long(11,33)&
        containment=contains

.. index::
   single: GetCoverage (Demonstration)

GetCoverage
-----------

`GetCoverage StitchedMosaic, full (GML incl. contributingFootprint & GeoTIFF) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&mediatype=multipart/mixed>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=mosaic_MER_FRS_1P_reduced_RGB&
        format=image/tiff&
        mediatype=multipart/mixed

`GetCoverage Dataset, full (GML & GeoTIFF) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&scalesize=x(200),y(200)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed

`GetCoverage Dataset, subset in pixels <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(300,400)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        subset=x(100,200)&
        subset=y(300,400)

`GetCoverage Dataset, subset in epsg 4326 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=Lat(40,41)&subset=Long(17,18)&subsettingCrs=http://www.opengis.net/def/crs/EPSG/0/4326>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        subset=Lat(40,41)&
        subset=Long(17,18)&
        subsettingCrs=http://www.opengis.net/def/crs/EPSG/0/4326

`GetCoverage Dataset, full, OutputCRS epsg 3035 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&OutputCRS=http://www.opengis.net/def/crs/EPSG/0/3035&scalesize=x(200),y(200)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        outputCrs=http://www.opengis.net/def/crs/EPSG/0/3035

`GetCoverage Dataset, full, size 200x200 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&scalesize=x(200),y(200)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        scalesize=x(200),y(200)

`GetCoverage Dataset, full, size 200x400 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&scalesize=x(200),y(400)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        scalesize=x(200),y(400)

`GetCoverage Dataset, subset in bands <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.1&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&rangesubset=MERIS_radiance_01_uint16:MERIS_radiance_03_uint16>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.1&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        rangesubset=MERIS_radiance_01_uint16:MERIS_radiance_03_uint16


GetCoverage POST/XML
--------------------

GetCoverage requests with POST/XML encoding might look like this:


A simple request:

  .. code-block:: xml

    <wcs:GetCoverage service="WCS" version="2.0.1"
       xmlns:wcs="http://www.opengis.net/wcs/2.0">
      <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
      <wcs:format>image/tiff</wcs:format>
      <wcs:mediaType>multipart/related</wcs:mediaType>
    </wcs:GetCoverage>

With a subset in pixel coordinates:

  .. code-block:: xml

    <wcs:GetCoverage service="WCS" version="2.0.1"
       xmlns:wcs="http://www.opengis.net/wcs/2.0">
      <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
      <wcs:DimensionTrim>
        <wcs:Dimension>x</wcs:Dimension>
        <wcs:TrimLow>0</wcs:TrimLow>
        <wcs:TrimHigh>99</wcs:TrimHigh>
      </wcs:DimensionTrim>
      <wcs:DimensionTrim>
        <wcs:Dimension>y</wcs:Dimension>
        <wcs:TrimLow>0</wcs:TrimLow>
        <wcs:TrimHigh>99</wcs:TrimHigh>
      </wcs:DimensionTrim>
      <wcs:format>image/tiff</wcs:format>
      <wcs:mediaType>multipart/related</wcs:mediaType>
    </wcs:GetCoverage>

With a subset in geographic coordinates with bilinear interpolation:

  .. code-block:: xml

    <wcs:GetCoverage service="WCS" version="2.0.1"
       xmlns:wcs="http://www.opengis.net/wcs/2.0" 
       xmlns:int="http://www.opengis.net/wcs/interpolation/1.0"
       xmlns:crs="http://www.opengis.net/wcs/crs/1.0">
      <wcs:Extension>
        <crs:subsettingCrs>http://www.opengis.net/def/crs/EPSG/0/4326</crs:subsettingCrs>
        <int:Interpolation>
          <int:globalInterpolation>http://www.opengis.net/def/interpolation/OGC/1/bilinear</int:globalInterpolation>
        </int:Interpolation>
      </wcs:Extension>
      <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
      <wcs:DimensionTrim>
        <wcs:Dimension>Long</wcs:Dimension>
        <wcs:TrimLow>20</wcs:TrimLow>
        <wcs:TrimHigh>22</wcs:TrimHigh>
      </wcs:DimensionTrim>
      <wcs:DimensionTrim>
        <wcs:Dimension>Lat</wcs:Dimension>
        <wcs:TrimLow>36</wcs:TrimLow>
        <wcs:TrimHigh>38</wcs:TrimHigh>
      </wcs:DimensionTrim>
      <wcs:format>image/tiff</wcs:format>
      <wcs:mediaType>multipart/related</wcs:mediaType>
    </wcs:GetCoverage>

With a range-subset and pixel-subset:

  .. code-block:: xml

    <wcs:GetCoverage service="WCS" version="2.0.1"
       xmlns:wcs="http://www.opengis.net/wcs/2.0"
       xmlns:rsub="http://www.opengis.net/wcs/range-subsetting/1.0">
      <wcs:Extension>
        <rsub:RangeSubset>
          <rsub:RangeItem>
            <rsub:RangeComponent>MERIS_radiance_04_uint16</rsub:RangeComponent>
          </rsub:RangeItem>
          <rsub:RangeItem>
            <rsub:RangeInterval>
              <rsub:startComponent>MERIS_radiance_05_uint16</rsub:startComponent>
              <rsub:endComponent>MERIS_radiance_07_uint16</rsub:endComponent>
            </rsub:RangeInterval>
          </rsub:RangeItem>
        </rsub:RangeSubset>
      </wcs:Extension>
      <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
      <wcs:DimensionTrim>
        <wcs:Dimension>x</wcs:Dimension>
        <wcs:TrimLow>0</wcs:TrimLow>
        <wcs:TrimHigh>99</wcs:TrimHigh>
      </wcs:DimensionTrim>
      <wcs:DimensionTrim>
        <wcs:Dimension>y</wcs:Dimension>
        <wcs:TrimLow>0</wcs:TrimLow>
        <wcs:TrimHigh>99</wcs:TrimHigh>
      </wcs:DimensionTrim>
      <wcs:format>image/tiff</wcs:format>
      <wcs:mediaType>multipart/related</wcs:mediaType>
    </wcs:GetCoverage>

With a set of GeoTIFF encoding parameters:

  .. code-block:: xml

    <wcs:GetCoverage service="WCS" version="2.0.1"
       xmlns:wcs="http://www.opengis.net/wcs/2.0"
       xmlns:geotiff="http://www.opengis.net/gmlcov/geotiff/1.0">
      <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
      <wcs:format>image/tiff</wcs:format>
      <wcs:Extension>
        <geotiff:parameters>
          <geotiff:compression>Deflate</geotiff:compression>
          <geotiff:predictor>FloatingPoint</geotiff:predictor>
          <geotiff:interleave>Band</geotiff:interleave>
          <geotiff:tiling>true</geotiff:tiling>
          <geotiff:tilewidth>32</geotiff:tilewidth>
          <geotiff:tileheight>64</geotiff:tileheight>
        </geotiff:parameters>
      </wcs:Extension>
    </wcs:GetCoverage>
