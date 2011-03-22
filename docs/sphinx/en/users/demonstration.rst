.. EOxServer Demonstration

EOxServer Demonstration
=======================

The EOxServer demonstration is based on the Envisat MERIS sample data available `here <http://earth.esa.int/object/index.cfm?fobjectid=4320>`_.

The configuration which is also shipped together with EOxServer for the unit tests includes one DatasetSeries and one StitchedMosaic:

* DatasetSeries (EOId: MER_FRS_1P_reduced) containing the 3 MERIS sample datasets with all 15 radiance bands encoded as uint16 values
* StitchedMosaic (CoverageId: mosaic_MER_FRS_1P_RGB_reduced) containing the 3 MERIS sample datasets reduced to RGB 8-bit

Note, the data has been reduced to from 300m resolution to 3000m.

GetCapabilities
---------------

`GetCapabilities <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCapabilities>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCapabilities

DescribeCoverage
----------------

`DescribeCoverage StitchedMosaic <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=DescribeCoverage&coverageid=mosaic_MER_FRS_1P_RGB_reduced>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeCoverage&
        coverageid=mosaic_MER_FRS_1P_RGB_reduced
    
`DescribeCoverage Dataset <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=DescribeCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed

DescribeEOCoverageSet
---------------------

Dataset
~~~~~~~

`DescribeEOCoverageSet Dataset <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed>`_::

    http://www.eoxserver.org/demo_trunk/ows?
            service=wcs&
            version=2.0.0&
            request=DescribeEOCoverageSet&
            EOId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed

StitchedMosaic
~~~~~~~~~~~~~~

`DescribeEOCoverageSet StitchedMosaic (3 Datasets returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced

`DescribeEOCoverageSet StitchedMosaic, subset in time (2 Datasets returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")

`DescribeEOCoverageSet StitchedMosaic, subset in Lat and Long, containment contains (1 Dataset returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOId=mosaic_MER_FRS_1P_RGB_reduced&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=contains>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=DescribeEOCoverageSet&
        EOId=mosaic_MER_FRS_1P_RGB_reduced&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&
        containment=contains

DatasetSeries
~~~~~~~~~~~~~~

`DescribeEOCoverageSet DatasetSeries (3 Datasets returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced

`DescribeEOCoverageSet DatasetSeries, trim subset in time (2 Datasets returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")

`DescribeEOCoverageSet DatasetSeries, slice subset in time (1 Dataset returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-22T09:20:58Z%22)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-22T09:20:58Z")

`DescribeEOCoverageSet DatasetSeries, trim subset in time trim, containment contains (1 Dataset returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=phenomenonTime(%222006-08-01%22,%222006-08-22T09:22:00Z%22)&containment=contains>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&
        containment=contains

`DescribeEOCoverageSet DatasetSeries, subset in Lat and Long (3 Datasets returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)

`DescribeEOCoverageSet DatasetSeries, subset in Lat and Long, containment contains (1 Dataset returned) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid=MER_FRS_1P_reduced&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=contains>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=describeeocoverageset&
        eoid=MER_FRS_1P_reduced&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&
        containment=contains

GetCoverage
-----------

`GetCoverage StitchedMosaic, full (GML incl. contributingFootprint & GeoTIFF) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&mediatype=multipart/mixed>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=mosaic_MER_FRS_1P_RGB_reduced&
        format=image/tiff&
        mediatype=multipart/mixed

`GetCoverage Dataset, full (GML & GeoTIFF) <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&resolution=Lat(0.031324)&resolution=Long(0.031324)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed

`GetCoverage Dataset, subset in pixels <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(300,400)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        subset=x(100,200)&
        subset=y(300,400)

`GetCoverage Dataset, subset in epsg 4326 <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(40,41)&subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(17,18)>`_::

    ttp://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        subset=Lat,http://www.opengis.net/def/crs/EPSG/0/4326(40,41)&
        subset=Long,http://www.opengis.net/def/crs/EPSG/0/4326(17,18)

`GetCoverage Dataset, full, OutputCRS epsg 3035 <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&OutputCRS=http://www.opengis.net/def/crs/EPSG/0/3035&resolution=Lat(0.031324)&resolution=Long(0.031324)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        OutputCRS=http://www.opengis.net/def/crs/EPSG/0/3035

`GetCoverage Dataset, full, size 200x200 <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&size=x(200)&size=y(200)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        size=x(200)&size=y(200)

`GetCoverage Dataset, full, size 200x400 <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&size=x(200)&size=y(400)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        size=x(200)&size=y(400)

`GetCoverage Dataset, subset in bands <http://www.eoxserver.org/demo_trunk/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&rangesubset=1,2,3&resolution=Lat(0.031324)&resolution=Long(0.031324)>`_::

    http://www.eoxserver.org/demo_trunk/ows?
        service=wcs&
        version=2.0.0&
        request=GetCoverage&
        coverageid=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&
        format=image/tiff&
        mediatype=multipart/mixed&
        rangesubset=1,2,3
