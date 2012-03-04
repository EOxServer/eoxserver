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
* StitchedMosaic (CoverageId: mosaic_MER_FRS_1P_RGB_reduced) containing
  the 3 MERIS sample datasets reduced to RGB 8-bit

Note, the data has been reduced from 300m resolution to 3000m.

The demonstration tries to show the usage of all available 
:ref:`EO-WCS request parameters <EO-WCS Request Parameters>`.

.. index::
   single: GetCapabilities (Demonstration)

GetCapabilities
---------------

`GetCapabilities <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCapabilities>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCapabilities

Interesting parts of the repsonse:

* Advertising EO-WCS:

  .. code-block:: xml

    <ows:Profile>http://www.opengis.net/spec/WCS_profile_earth-observation/1.0/conf/ap-eo</ows:Profile>

* The additional EO-WCS operation:

  .. code-block:: xml

    <ows:Operation name="DescribeEOCoverageSet">
        <ows:DCP>
            <ows:HTTP>
                <ows:Get xlink:href="http://eoxserver.org/demo_stable/ows?" xlink:type="simple"/>
                <ows:Post xlink:href="http://eoxserver.org/demo_stable/ows?" xlink:type="simple"/>
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
        <wcs:CoverageId>mosaic_MER_FRS_1P_RGB_reduced</wcs:CoverageId>
        <wcs:CoverageSubtype>RectifiedStitchedMosaic</wcs:CoverageSubtype>
    </wcs:CoverageSummary>
        
* There is a DatasetSeries available:

  .. code-block:: xml

    <wcseo:DatasetSeriesSummary>
        <ows:WGS84BoundingBox>
            <ows:LowerCorner>-4.042969 32.080078</ows:LowerCorner>
            <ows:UpperCorner>33.134766 45.175781</ows:UpperCorner>
        </ows:WGS84BoundingBox>
        <wcseo:DatasetSeriesId>MER_FRS_1P_reduced</wcseo:DatasetSeriesId>
        <gml:TimePeriod gml:id="MER_FRS_1P_reduced_timeperiod">
            <gml:beginPosition>2006-08-16T00:00:00</gml:beginPosition>
            <gml:endPosition>2006-08-31T00:00:00</gml:endPosition>
        </gml:TimePeriod>
    </wcseo:DatasetSeriesSummary>

.. index::
   single: DescribeCoverage (Demonstration)

DescribeCoverage
----------------

`DescribeCoverage StitchedMosaic <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeCoverage&coverageid=mosaic_MER_FRS_1P_RGB_reduced>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeCoverage&
        coverageid=mosaic_MER_FRS_1P_RGB_reduced
    
`DescribeCoverage Dataset <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed

.. index::
   single: DescribeEOCoverageSet (Demonstration)

DescribeEOCoverageSet
---------------------

Dataset
~~~~~~~

`DescribeEOCoverageSet Dataset <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed>`_::

    http://eoxserver.org/demo_stable/ows?
            service=wcs&
            version=2.0.0&
            request=DescribeEOCoverageSet&
            EOId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed

StitchedMosaic
~~~~~~~~~~~~~~

`DescribeEOCoverageSet StitchedMosaic (3 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced

`DescribeEOCoverageSet StitchedMosaic, subset in time (2 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")

`DescribeEOCoverageSet StitchedMosaic, subset in Lat and Long, containment contains (1 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=contains>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&
        containment=contains

`DescribeEOCoverageSet StitchedMosaic, returned CoverageDescriptions limited to 2 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced&count=2>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced&
        count=2

DatasetSeries
~~~~~~~~~~~~~~

`DescribeEOCoverageSet DatasetSeries (3 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced

`DescribeEOCoverageSet DatasetSeries, trim subset in time (2 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")

`DescribeEOCoverageSet DatasetSeries, slice subset in time (1 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-22T09:20:58Z%22)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-22T09:20:58Z")

`DescribeEOCoverageSet DatasetSeries, trim subset in time trim, containment contains (1 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)&containment=contains>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&
        containment=contains

`DescribeEOCoverageSet DatasetSeries, subset in Lat and Long (3 Datasets returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)

`DescribeEOCoverageSet DatasetSeries, subset in Lat and Long, containment contains (1 Dataset returned) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=contains>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&
        containment=contains

.. index::
   single: GetCoverage (Demonstration)

GetCoverage
-----------

`GetCoverage StitchedMosaic, full (GML incl. contributingFootprint & GeoTIFF) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&mediatype=multipart/mixed>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=mosaic_MER_FRS_1P_RGB_reduced&
        format=image/tiff&
        mediatype=multipart/mixed

`GetCoverage Dataset, full (GML & GeoTIFF) <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&resolution=Lat(0.031324)&resolution=Long(0.031324)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed

`GetCoverage Dataset, subset in pixels <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(300,400)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        subset=x(100,200)&
        subset=y(300,400)

`GetCoverage Dataset, subset in epsg 4326 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(40,41)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(17,18)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(40,41)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(17,18)

`GetCoverage Dataset, full, OutputCRS epsg 3035 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&OutputCRS=http://www.opengis.net/def/crs/EPSG/0/3035&resolution=Lat(0.031324)&resolution=Long(0.031324)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        OutputCRS=http://www.opengis.net/def/crs/EPSG/0/3035

`GetCoverage Dataset, full, size 200x200 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&size=x(200)&size=y(200)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        size=x(200)&size=y(200)

`GetCoverage Dataset, full, size 200x400 <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&size=x(200)&size=y(400)>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        size=x(200)&size=y(400)

`GetCoverage Dataset, subset in bands <http://eoxserver.org/demo_stable/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&rangesubset=1,2,3>`_::

    http://eoxserver.org/demo_stable/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        rangesubset=1,2,3
