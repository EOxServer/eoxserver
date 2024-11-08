.. OpenSearch
  #-----------------------------------------------------------------------------
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Fabian Schindler <fabian.schindler@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (c) 2016 EOX IT Services GmbH
  #
  # Permission is hereby granted, free of charge, to any person obtaining a
  # copy of this software and associated documentation files (the "Software"),
  # to deal in the Software without restriction, including without limitation
  # the rights to use, copy, modify, merge, publish, distribute, sublicense,
  # and/or sell copies of the Software, and to permit persons to whom the
  # Software is furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies of this Software or works derived from this Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  # DEALINGS IN THE SOFTWARE.
  #-----------------------------------------------------------------------------

.. _opensearch:

OpenSearch
==========

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

Introduction
------------

Since version 0.4, EOxServer features an OpenSearch 1.1 interface to allow the
exploration of its contents in a different manner than by using the EO-WCS or
WMS functionality.

In contrast to EO-WCS and WMS, the OpenSearch interface operates on metadata
only and allows a performant view of the data, by using slimmer output formats
such as GeoJSON or Atom/RSS XML structures.

In EOxServer, `Time
<http://www.opensearch.org/Specifications/OpenSearch/Extensions/Time/1.0/Draft_1>`_ and
`Geo <http://www.opensearch.org/Specifications/OpenSearch/Extensions/Geo/1.0/Draft_2>`_
extensions are implemented to limit the spatio-temporal scope of the search.
Additionally, `EO <https://docs.opengeospatial.org/is/13-026r8/13-026r8.html>`_
extension is implemented to support most of the required and recommended
best practices of the `CEOS OpenSearch Best Practice Document
<https://earthdata.nasa.gov/files/CEOS_OpenSearch_Best_Practice_Doc-v.1.0.1_Jun2015.pdf>`_.

Setup
-----

To enable the OpenSearch interface in the EOxServer instance, the ``urls.py``
has to be adjusted and the following line added:

.. code-block:: python

    from django.urls import include, re_path

    urlpatterns = [
        ...
        re_path(r'^opensearch/', include('eoxserver.services.opensearch.urls')),
        ...
    )

This adds the necessary URLs and views to the instances setup to expose the
interface to the users.

Additionally, the the string ``"eoxserver.services.opensearch.**"`` has to be
added to the ``COMPONENTS`` of the ``settings.py`` file.

The ``EOXS_OPENSEARCH_FORMATS``, ``EOXS_OPENSEARCH_EXTENSIONS``,
``EOXS_OPENSEARCH_SUMMARY_TEMPLATE``, and ``EOXS_OPENSEARCH_RECORD_MODEL``
settings in the ``settings.py`` alter the behavior of the service. The details
can be found in the `instance configuration section <InstanceConfiguration>`_.

Usage
-----

The OpenSearch implementation of EOxServer follows a two-step search approach:

  1. the instance can be searched for collections
  2. single collections can be searched for records

For each of those steps, the OpenSearch interface allows two interactions, the
``description`` and the``search``.
The description operation returns an XML document with service metadata and
parametrized endpoints for further searches. The ``search`` operation hosts the
main searching functionality: the search parameters are sent the service, and
the results are encoded end returned.

Collection Search
~~~~~~~~~~~~~~~~~

To get the description of the OpenSearch service running in your instance, you
have to access the URL previously specified in the ``urlpatterns``. In the
:doc:`autotest instance <../../developers/autotest>`, this looks like this::

    $ curl http://localhost/opensearch/
    <?xml version='1.0' encoding='iso-8859-1'?>
    <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="">
      <ShortName/>
      <Description/>
      <Url type="application/atom+xml" rel="collection" template="http://localhost/opensearch/atom/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Url type="application/vnd.geo+json" rel="collection" template="http://localhost/opensearch/json/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Url type="application/vnd.google-earth.kml+xml" rel="collection" template="http://localhost/opensearch/kml/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Url type="application/rss+xml" rel="collection" template="http://localhost/opensearch/rss/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Contact/>
      <LongName/>
      <Developer/>
      <Attribution/>
      <SyndicationRight>open</SyndicationRight>
      <AdultContent/>
      <Language/>
      <InputEncoding/>
      <OutputEncoding/>
    </OpenSearchDescription>

As you can see, the description XML document contains a ``Url`` element for
each registered output format. Each URL also has a set of parameter
placeholders from which the actual query can be constructed. Most of the
parameters are optional, as indicated by the suffixed ``?`` within the curly
braces.

To perform a search for collections, a request template has to be used and
filled with parameters_. See this example, where a simple bounding box is used
to limit the search::

    $ curl http://localhost/opensearch/atom/?bbox=10,33,12,35
    <feed xmlns:georss="http://www.georss.org/georss" xmlns:geo="http://a9.com/-/opensearch/extensions/geo/1.0/" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:time="http://a9.com/-/opensearch/extensions/time/1.0/" xmlns="http://www.w3.org/2005/Atom">
      <id>http://localhost/opensearch/atom/?bbox=10,33,12,35</id>
      <title>None Search</title>
      <link href="http://localhost/opensearch/atom/?bbox=10,33,12,35" rel="self"/>
      <description/>
      <opensearch:totalResults>1</opensearch:totalResults>
      <opensearch:startIndex>0</opensearch:startIndex>
      <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
      <opensearch:Query role="request" geo:box="10,33,12,35"/>
      <link href="http://localhost/opensearch/" type="application/opensearchdescription+xml" rel="search"/>
      <link href="http://localhost/opensearch/atom/?bbox=10,33,12,35" type="application/atom+xml" rel="self"/>
      <link href="http://localhost/opensearch/atom/?bbox=10%2C33%2C12%2C35" type="application/atom+xml" rel="first"/>
      <link href="http://localhost/opensearch/atom/?startIndex=1&amp;bbox=10%2C33%2C12%2C35" type="application/atom+xml" rel="last"/>
      <entry>
        <title>MER_FRS_1P_reduced_RGB</title>
        <id>MER_FRS_1P_reduced_RGB</id>
        <link href="http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/" rel="search"/>
        <georss:box>32.264541 -3.437981 46.218445 27.968591</georss:box>
      </entry>
    </feed>

The resulting atom feed contains information used for paging and the matched
collections. Each ``entry`` (or ``item`` in RSS) contains a rough metadata
overview of the collection and a link to the collections OpenSearch description
document, which can be used to make searches for records within the collection.


Record Search
~~~~~~~~~~~~~

Searching for records within a collection is very similar to searching for
collections on the service itself. The first step is to obtain the OpenSearch
description document for the collections::

    $ curl http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/
    <?xml version='1.0' encoding='iso-8859-1'?>
    <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="">
      <ShortName/>
      <Description/>
      <Url type="application/atom+xml" rel="results" template="http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/atom/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Url type="application/vnd.geo+json" rel="results" template="http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/json/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Url type="application/vnd.google-earth.kml+xml" rel="results" template="http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/kml/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Url type="application/rss+xml" rel="results" template="http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/rss/?q={searchTerms?}&amp;count={count?}&amp;startIndex={startIndex?}&amp;bbox={geo:box?}&amp;geom={geo:geometry?}&amp;lon={geo:lon?}&amp;lat={geo:lat?}&amp;r={geo:radius?}&amp;georel={geo:relation?}&amp;uid={geo:uid?}&amp;start={time:start?}&amp;end={time:end?}&amp;timerel={time:relation?}"/>
      <Contact/>
      <LongName/>
      <Developer/>
      <Attribution/>
      <SyndicationRight>open</SyndicationRight>
      <AdultContent/>
      <Language/>
      <InputEncoding/>
      <OutputEncoding/>
    </OpenSearchDescription>

Again, the result contains a list of URL templates, one for each enabled result
format. These templates can be used to perform the searches for records. The
following example uses a time span to limit the records::

    $ curl "http://localhost/opensearch/collections/MER_FRS_1P_reduced_RGB/json/?start=2006-08-16T09:09:29Z&end=2006-08-22T09:09:29Z"
    {
    "type": "FeatureCollection",
    "bbox": [ 11.648344, 32.269746, 27.968591, 46.216558 ],
    "features": [
    { "type": "Feature", "properties": { "id": "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced", "begin_time": "2006-08-16T09:09:29Z", "end_time": "2006-08-16T09:12:46Z" }, "bbox": [ 11.648344, 32.269746, 27.968591, 46.216558 ], "geometry": { "type": "MultiPolygon", "coordinates": [ [ [ [ 14.322576, 46.216558 ], [ 14.889221, 46.152076 ], [ 15.714163, 46.044475 ], [ 16.939196, 45.874384 ], [ 18.041168, 45.707637 ], [ 19.696621, 45.437661 ], [ 21.061979, 45.188708 ], [ 22.14653, 44.985502 ], [ 22.972839, 44.817601 ], [ 24.216794, 44.548719 ], [ 25.078471, 44.353026 ], [ 25.619454, 44.222401 ], [ 27.096691, 43.869453 ], [ 27.968591, 43.648678 ], [ 27.608909, 42.914276 ], [ 26.904154, 41.406745 ], [ 26.231198, 39.890887 ], [ 25.79281, 38.857425 ], [ 25.159378, 37.327455 ], [ 24.607823, 35.91698 ], [ 24.126822, 34.659956 ], [ 23.695477, 33.485864 ], [ 23.264471, 32.269746 ], [ 21.93772, 32.597366 ], [ 20.490342, 32.937415 ], [ 18.720985, 33.329502 ], [ 17.307239, 33.615994 ], [ 16.119969, 33.851259 ], [ 14.83709, 34.086159 ], [ 13.692708, 34.286728 ], [ 12.702329, 34.450209 ], [ 11.648344, 34.612576 ], [ 11.818952, 35.404302 ], [ 12.060892, 36.496444 ], [ 12.273682, 37.456615 ], [ 12.465752, 38.338768 ], [ 12.658489, 39.179619 ], [ 12.861886, 40.085426 ], [ 13.125704, 41.224754 ], [ 13.249298, 41.773101 ], [ 13.442094, 42.58703 ], [ 13.647311, 43.450338 ], [ 13.749196, 43.879742 ], [ 13.904244, 44.51596 ], [ 14.076176, 45.247154 ], [ 14.21562, 45.812577 ], [ 14.322576, 46.216558 ] ] ] ] } }

    ]
    }


EO Extension
------------
Since version 0.4 EOxServer prvides implementation of the
`OpenSearch EO <https://docs.opengeospatial.org/is/13-026r8/13-026r8.html>`_
extension. This extension supports most of the required and recommended
best practices of the `CEOS OpenSearch Best Practice Document
<https://earthdata.nasa.gov/files/CEOS_OpenSearch_Best_Practice_Doc-v.1.0.1_Jun2015.pdf>`_.

The EO extension allows the following EO parameters to be added
to the Opensearch request:

.. _table_opensearch_search_request_EO_parameters:

.. table:: OpenSearch Search Request EO Parameters

    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | Parameter                              | Description                                          | Example                                  |
    | (Replacement Tag)                      |                                                      |                                          |
    +========================================+======================================================+==========================================+
    | productType                            | A string that identifies the product type.           |   productType=GES_DISC_AIRH3STD_V005     |
    | (eop:productType)                      |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | doi                                    | A Digital Object Identifier "string" identifying the |   doi=doi:10.7666/d.y351065              |
    | (eo:doi)                               | product in the `DOI <http://www.doi.org/>`_ system.  |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | platform                               | The platform / satellite short name.                 |   platform=Sentinel-1                    |
    | (eo:shortName)                         |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | platformSerialIdentifier               | The Platform / satellite serial identifier.          |                                          |
    | (eo:serialIdentifier)                  |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | instrument                             | The name of the sensor / instrument.                 |   instrument=ASAR                        |
    | (eop:shortName)                        |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | sensorType                             | The sensor type.                                     |   sensorType=ATMOSPHERIC                 |
    | (eo:sensorType)                        |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | compositeType                          | The type of composite product expressed as time      |   compositeType=P10D (P10D) is for       |
    | (eo:compositeType)                     | period that the composite product covers.            |   10 days coverage period                |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | processingLevel                        | The processing level applied to the product.         |                                          |
    | (eo:processingLevel)                   |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | orbitType                              | The platform / satellite orbit type.                 |   orbitType=LEO (low earth orbit)        |
    | (eo:orbitType)                         |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | spectralRange                          | The sensor spectral range.                           |   spectralRange= INFRARED                |
    | (eo:spectralRange)                     |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | wavelengths                            | A number, set or interval requesting the sensor      |                                          |
    | (eo:discreteWavelengths)               | wavelengths in nanometers.                           |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | hasSecurityConstraints                 | A text informs if the resource has any security      |   hasSecurityConstraints=FALSE           |
    |                                        | constraints. Possible values: TRUE, FALSE            |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | dissemination                          | The dissemination method.                            |   dissemination=EUMETCast                |
    |                                        |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | recordSchema                           | Metadata model in which additional metadata should   |                                          |
    |                                        | be provided inline.                                  |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | parentIdentifier                       | The parent of the entry in a hierarchy of resources. |                                          |
    | (eo:parentIdentifier)                  |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | productionStatus                       | The status of the entry.                             |   productionStatus=ARCHIVED              |
    | (eo:status)                            |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | acquisitionType                        | Used to distinguish at a high level the              |    acquisitionType=CALIBRATION           |
    | (eo:acquisitionType)                   | appropriateness of the acquisition for "general" use,|                                          |
    |                                        | whether the product is a nominal acquisition, special|                                          |
    |                                        | calibration product or other.                        |                                          |
    |                                        | Values: NOMINAL, CALIBRATION, OTHER.                 |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | orbitNumber                            | A number, set or interval requesting the acquisition |                                          |
    | (eo:orbitNumber)                       | orbit.                                               |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | orbitDirection                         | the acquisition orbit direction.                     |   orbitDirection=ASCENDING               |
    | (eo:orbitDirection)                    |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | track                                  | the orbit track.                                     |                                          |
    | (eo:wrsLongitudeGrid)                  |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | frame                                  | the orbit frame.                                     |                                          |
    | (eo:wrsLatitudeGrid)                   |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | swathIdentifier                        | Swath identifier. Value list can be retrieved with   |   swathIdentifier=I3 (Envisat ASAR       |
    | (eo:swathIdentifier)                   | codeSpace.                                           |   has 7 distinct swaths (I1,I2...I7)     |
    |                                        |                                                      |   that correspond to precise             |
    |                                        |                                                      |   incidence angles for the sensor)       |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | cloudCover                             | The cloud coverage percantage.                       |   cloudCover=65                          |
    | (eo:cloudCoverPercentage               |                                                      |                                          |
    | or eo:cloudCoverPercentage)            |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | snowCover                              | The cloud coverage percantage.                       |   cloudCover=65                          |
    | (eo:snowCoverPercentage                |                                                      |                                          |
    | or eo:snowCoverPercentage)             |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | lowestLocation                         | The bottom height of datalayer (in meters).          |                                          |
    | (eo:lowestLocation)                    |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | highestLocation                        | The top height of datalayer (in meters).             |                                          |
    | (eo:highestLocation)                   |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | productVersion                         | The version of the Product.                          |                                          |
    | (eo:version)                           |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | productQualityStatus                   | An optional field that must be provided if the       |   productQualityStatus=DEGRADED          |
    | (eo:productQualityDegradation)         | product passed a quality check. Possible             |                                          |
    |                                        | values: NOMINAL and DEGRADED.                        |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | productQualityDegradationTag           | The degradations affecting the product.Possible      |  productQualityDegradationTag=RADIOMETRY |
    | (eo:productQualityDegradationTag)      | values are mission specific and can be freely        |                                          |
    |                                        | defined.                                             |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | processorName                          | The processor software name.                         |                                          |
    | (eo:processorName)                     |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | processingCenter                       | The processing center.                               |   processingCenter=PDHS-E                |
    | (eo:processingCenter)                  |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | creationDate                           | The date when the metadata item was ingested for     |                                          |
    | (eo:creationDate)                      | the first time (i.e. inserted) in the catalogue.     |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | modificationDate                       | The date when the metadata item was last modified    |                                          |
    | (eo:modificationDate)                  | (i.e. updated) in the catalogue.                     |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | processingDate                         | A date interval requesting entries processed within  |                                          |
    | (eo:processingDate)                    | a given time interval.                               |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | sensorMode                             | The sensor mode.                                     |                                          |
    | (eo:operationalMode)                   |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | archivingCenter                        | The the archiving center.                            |                                          |
    | (eo:archivingCenter)                   |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | processingMode                         | Processing mode. Often referred to as Real Time,     |                                          |
    | (eo:ProcessingMode)                    | Near Real Time etc.                                  |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | availabilityTime                       | The time when the result became available            |                                          |
    | (eo:timePosition)                      | (i.e. updated) in the catalogue.                     |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | acquisitionStation                     | The station used for the acquisition.                |                                          |
    | (eo:acquisitionStation)                |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | acquisitionSubType                     | The Acquisition sub-type.                            |                                          |
    | (eo:acquisitionSubType)                |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | startTimeFromAscendingNode             | Start time of acquisition in milliseconds from       |                                          |
    | (eo:startTimeFromAscendingNode)        | Ascending node date.                                 |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | completionTimeFromAscendingNode        | Completion time of acquisition in milliseconds from  |                                          |
    | (eo:completionTimeFromAscendingNode)   | Ascending node date.                                 |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | illuminationAzimuthAngle               | Mean illumination/solar azimuth angle given in       |                                          |
    | (eo:illuminationAzimuthAngle)          | degrees.                                             |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | illuminationZenithAngle                | Mean illumination/solar zenith angle given in        |                                          |
    | (eo:illuminationZenithAngle)           | degrees.                                             |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | illuminationElevationAngle             | Mean illumination/solar elevation angle given in     |                                          |
    | (eo:illuminationElevationAngle)        | degrees.                                             |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | polarisationMode                       | The polarisation mode taken from codelist:           |     polarisationMode=D                   |
    | (eo:polarisationMode)                  | S (for single), D (for dual), T (for twin),          |                                          |
    |                                        | Q (for quad), UNDEFINED                              |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | polarisationChannels                   | Polarisation channel transmit/receive configuration. |    polarisationChannels=vertical         |
    | (eo:polarisationChannels)              |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | antennaLookDirection                   | LEFT or RIGHT.                                       |                                          |
    | (eo:antennaLookDirection)              |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | minimumIncidenceAngle                  | Minimum incidence angle given in degrees.            |                                          |
    | (eo:minimumIncidenceAngle)             |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | maximumIncidenceAngle                  | Maximum incidence angle given in degrees.            |                                          |
    | (eo:maximumIncidenceAngle)             |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | dopplerFrequency                       | Doppler Frequency of acquisition.                    |                                          |
    | (eo:dopplerFrequency)                  |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+
    | incidenceAngleVariation                | Incidence angle variation                            |                                          |
    | (eo:incidenceAngleVariation)           |                                                      |                                          |
    +----------------------------------------+------------------------------------------------------+------------------------------------------+


Parameters
----------

As mentioned before, EOxServers implementation of OpenSearch adheres to the
core, and the time, geo and EO extensions. Thus the interface allows the
following parameters when searching for datasets:

.. _table_opensearch_search_request_parameters:
.. table:: OpenSearch Search Request Parameters

    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | Parameter (Replacement Tag) | Description                                               | Example                          |
    +=============================+===========================================================+==================================+
    | q (searchTerms)             | This parameter is currently not used.                     |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | count                       | Number of returned elements as an integer                 |   count=25                       |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | startIndex                  | The initial offset to get elements as an integer          |   startIndex=125                 |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | format                      | The output format of the search. Currently supported are  |   format=json                    |
    |                             | "json", "kml", "atom", and "rss".                         |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | bbox (geo:box)              | The geographical area expressed as a bounding box defined |   bbox=-120.0,40.5,-110.5,43.8   |
    |                             | as "west,south,east,north" in EPSG:4326 decimal degrees.  |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | lat and lon                 | latitude and longitude geographical coordinate pair as    |   lat=32.25&lon=125.654          |
    | (geo:lat/geo:lon)           | decimal degrees in EPSG:4326.                             |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | r (geo:radius)              | The radius parameter used with lat and lon parameters.    |   lat=32.25&lon=125.654          |
    |                             | Units are meters on along the earths surface.             |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | geom (geo:geometry)         | A custom geometry encoded as WKT. Supported are           |   geom=POINT(6 10)               |
    |                             | POINT, LINESTRING, POLYGON, MULTIPOINT, MULTILINESTRING,  |   geom=LINESTRING(3 4,1 5,20 25) |
    |                             | and MULTIPOLYGON. The geometry must be expressed in       |                                  |
    |                             | EPSG:4326.                                                |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | georel (geo:relation)       | The geospatial relation of the supplied geometry (or      |   georel=contains                |
    |                             | bounding box/circle) and the                              |                                  |
    |                             | searched datasets geometry. This parameter allows the     |                                  |
    |                             | following values:                                         |                                  |
    |                             |                                                           |                                  |
    |                             | - "intersects" (default): the passed geometry has to      |                                  |
    |                             |   intersect with the datasets geometry                    |                                  |
    |                             | - "contains": the passed geometry has to fully enclose    |                                  |
    |                             |   datasets geometry. Currently only PostgreSQL/PostGIS    |                                  |
    |                             |   supports this relation for distance lookups.            |                                  |
    |                             | - "disjoint": the passed geometry has no spatial overlap  |                                  |
    |                             |   with the datasets geometry.                             |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | uid (geo:uid)               | This parameter allows to match a single record by its     |   uid=MER_FRS_1P_reduced_RGB     |
    |                             | exact identifier. This is also used to allow links to     |                                  |
    |                             | searches with only a specific item, as used in the atom   |                                  |
    |                             | and RSS formats.                                          |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | start and end               | The start and end data/time of the given time interval    |   start=2006-08-16T09:09:29Z&    |
    | (time:start/time:end)       | encoded in                                                |   end=2006-08-17                 |
    |                             | `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601>`_.     |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | timerel (time:relation)     | The temporal relation between the passed interval and the |   timerel=equals                 |
    |                             | datasets time intervals. This parameter allows the        |                                  |
    |                             | following values:                                         |                                  |
    |                             |                                                           |                                  |
    |                             | - "intersects": the given interval has to somehow         |                                  |
    |                             |   intersect with the datasets time span.                  |                                  |
    |                             | - "during": the given interval has to enclose the         |                                  |
    |                             |   datasets time span.                                     |                                  |
    |                             | - "disjoint": the given interval must have no temporal    |                                  |
    |                             |   overlap with the datasets time span.                    |                                  |
    |                             | - "equals": the given interval has to exactly match the   |                                  |
    |                             |   datasets time span.                                     |                                  |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+
    | cql                         | This parameter allows to perform more complex queries     |   For more information see the   |
    |                             | using the Common Query Language (CQL).                    |   :ref:`CQL` documentation.      |
    +-----------------------------+-----------------------------------------------------------+----------------------------------+

.. note::

    Unfortunately there are some known issues for certain parameters, especially
    concerning the ``geo:radius`` with the ``geo:lat`` and ``geo:lon``: On
    certain platforms any distance based search results in an abort `caused by
    GEOS <https://trac.osgeo.org/geos/ticket/377>`_, the underlying geometric
    algorithm library.

All parameters are available for both collection and record searches.


Output Formats
--------------

EOxServer supports various output formats to encode the results of the
searches. All formats are available for both collection and record searches.

ATOM and RSS
~~~~~~~~~~~~

The EOxServer OpenSearch implementation tries to adhere the specification and
recommendations for using OpenSearch with either of the two formats.
Apart from the usual metadata links are added to the various enabled services
like WMS and WCS wherever applicable. When searching for collections a link to
the collections OpenSearch description document is also added.

GeoJSON and KML
~~~~~~~~~~~~~~~

These formats aim to provide only a compact metadata overview of the matched
collections and records. Only the identifier, begin/end timestamps and the
footprint geometry are included.
