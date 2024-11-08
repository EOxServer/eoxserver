.. Instance
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2020 EOX IT Services GmbH
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

Instance
========

EOxServer can only be used in an instantiated Django project. This instance
incorporates the whole configuration necessary to run the web application. With
this approach it is possible to deploy more than one web application per host.

.. _InstanceCreation:

Creation
--------

An instance can be created in multiple ways. The easiest way is to run the
``eoxserver-instance.py`` script, that available through the EOxServer Python
package, which has to be installed first. See the :ref:`Installation` for more
details.


Another option is to use the ``django-admin`` command to start a new Django
project, that will later be enhanced to be a fully functioning EOxServer. See
next section :ref:`Configuration` for what can be configured.

.. _InstanceConfiguration:

Configuration
-------------

The instance provides various different configuration files to configure the
resulting web application. As each EOxServer instance is a Django Project at
its core, it inherits all its configuration files.

These files are first and foremost the ``settings.py`` and ``urls.py`` files,
but also the ``wsgi.py`` and ``manage.py`` to a lesser degree.

EOxServer uses the ``settings.py`` file to configure some of its internal
functions. Please see the next section for the available sections and their
effect.

Please see the Django Documentation for a coverage of the configuration
capabilities.


Configurations in settings.py
-----------------------------

These settings are used by Django directly, but are usually necessary do adapt:

PROJECT_DIR
  Absolute path to the instance directory.

DATABASES
  The database connection details. EOxServer requires a spatially enabled
  database backend. Both Spatialite and PostGIS are tested and known to work.

LOGGING
  what and how logs are prcessed and stored. EOxServer provides a
  very basic configuration that stores logfiles in the instace directory, but
  they will probably not be suitable for every instance.

You can also customize further settings, for a complete reference please refer
to the `Django settings overview
<https://docs.djangoproject.com/en/2.2/topics/settings/>`_.

Please especially consider the setting of the `TIME_ZONE
<https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-TIME_ZONE>`_
parameter and read the Notes provided in the ``settings.py`` file.

The following settings can be used to configure various parts of EOxServer.

EOXS_STORAGE_HANDLERS
  The enabled storage handlers as a list of paths to their respective
  implementing class.

  Default:

  .. code-block:: python

      [
          'eoxserver.backends.storages.ZIPStorageHandler',
          'eoxserver.backends.storages.TARStorageHandler',
          'eoxserver.backends.storages.DirectoryStorageHandler',
          'eoxserver.backends.storages.HTTPStorageHandler',
          'eoxserver.backends.storages.FTPStorageHandler',
          'eoxserver.backends.storages.SwiftStorageHandler',
      ]

EOXS_STORAGE_AUTH_HANDLERS
  The enabled storage authorization handlers as a list of paths to their
  respective implementing class.

  Default:

  .. code-block:: python

      [
          'eoxserver.backends.keystone.storage_auth.KeystoneStorageAuthHandler',
      ]

EOXS_MAP_RENDERER (="eoxserver.render.mapserver.map_renderer.MapserverMapRenderer")
  The map renderer to use for map rendering such as in WMS GetMap requests.

  Default:

  .. code-block:: python

      "eoxserver.render.mapserver.map_renderer.MapserverMapRenderer"

EOXS_MAPSERVER_LAYER_FACTORIES
  The list of layer factories for when the default MapServer map renderer is
  used.


  Default:

  .. code-block:: python

      [
          'eoxserver.render.mapserver.factories.CoverageLayerFactory',
          'eoxserver.render.mapserver.factories.OutlinedCoverageLayerFactory',
          'eoxserver.render.mapserver.factories.MosaicLayerFactory',
          'eoxserver.render.mapserver.factories.BrowseLayerFactory',
          'eoxserver.render.mapserver.factories.OutlinedBrowseLayerFactory',
          'eoxserver.render.mapserver.factories.MaskLayerFactory',
          'eoxserver.render.mapserver.factories.MaskedBrowseLayerFactory',
          'eoxserver.render.mapserver.factories.OutlinesLayerFactory',
          'eoxserver.render.mapserver.factories.HeatmapLayerFactory',
      ]


DEFAULT_EOXS_MAPSERVER_HEATMAP_RANGE_DEFAULT = (0, 10)
  The default range for heatmap layers when none are provided via ``dim_range``.

  Default:

  .. code-block:: python

      (0, 10)

EOXS_COVERAGE_METADATA_FORMAT_READERS
  The list of coverage metadata readers that will be employed to read metadata
  when a new coverage is registered.

  Default:

  .. code-block:: python

      [
          'eoxserver.resources.coverages.metadata.coverage_formats.gsc.GSCFormatReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.dimap_general.DimapGeneralFormatReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.eoom.EOOMFormatReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.gdal_dataset.GDALDatasetMetadataReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.inspire.InspireFormatReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.native.NativeFormat',
          'eoxserver.resources.coverages.metadata.coverage_formats.native_config.NativeConfigFormatReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.landsat8_l1.Landsat8L1CoverageMetadataReader',
      ]

EOXS_COVERAGE_METADATA_GDAL_DATASET_FORMAT_READERS
  The list of coverage metadata readers that will be employed to read metadata
  when a new coverage is registered. These readers will use a GDAL dataset
  underneath.

  Default:

  .. code-block:: python

      [
          'eoxserver.resources.coverages.metadata.coverage_formats.gdal_dataset_envisat.GDALDatasetEnvisatMetadataFormatReader',
      ]

EOXS_PRODUCT_METADATA_FORMAT_READERS
  The list of product metadata readers that will be employed to read metadata
  when a new product is registered.

  Default:

  .. code-block:: python

      [
          'eoxserver.resources.coverages.metadata.product_formats.sentinel1.S1ProductFormatReader',
          'eoxserver.resources.coverages.metadata.product_formats.sentinel2.S2ProductFormatReader',
          'eoxserver.resources.coverages.metadata.product_formats.landsat8_l1.Landsat8L1ProductMetadataReader',
          'eoxserver.resources.coverages.metadata.coverage_formats.eoom.EOOMFormatReader',
          'eoxserver.resources.coverages.metadata.product_formats.gsc.GSCProductMetadataReader',
      ]

EOXS_MAPSERVER_CONNECTORS
  Default:

  .. code-block:: python

      [
          'eoxserver.services.mapserver.connectors.simple_connector.SimpleConnector',
          'eoxserver.services.mapserver.connectors.multifile_connector.MultiFileConnector',
          'eoxserver.services.mapserver.connectors.mosaic_connector.MosaicConnector',
      ]

EOXS_OPENSEARCH_FORMATS
  The list of OpenSearch result formats that shall be available for searching.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.opensearch.formats.atom.AtomResultFormat',
          'eoxserver.services.opensearch.formats.rss.RSSResultFormat',
          'eoxserver.services.opensearch.formats.html.HTMLResultFormat',
          'eoxserver.services.opensearch.formats.kml.KMLResultFormat',
          'eoxserver.services.opensearch.formats.geojson.GeoJSONResultFormat',
      ]

EOXS_OPENSEARCH_EXTENSIONS
  The list of OpenSearch extension implementations.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.opensearch.extensions.eo.EarthObservationExtension',
          'eoxserver.services.opensearch.extensions.geo.GeoExtension',
          'eoxserver.services.opensearch.extensions.time.TimeExtension',
          'eoxserver.services.opensearch.extensions.cql.CQLExtension',
      ]

EOXS_OPENSEARCH_SUMMARY_TEMPLATE (="opensearch/summary.html")
  The name of the template to use to generate the item summary.

  Default:

  .. code-block:: python

      "opensearch/summary.html"

EOXS_OPENSEARCH_RECORD_MODEL (="eoxserver.resources.coverages.models.EOObject")
  What record base model to use for OpenSearch searches. Can be set to
  ``"eoxserver.resources.coverages.models.EOObject"``,
  ``"eoxserver.resources.coverages.models.Coverage"``, or
  ``"eoxserver.resources.coverages.models.Product"``. When using the generic
  EOObject the search can find both Products and Coverages, but the underlying
  query is significantly more complex, negatively impacting the performance.

  Default:

  .. code-block:: python

      "eoxserver.resources.coverages.models.EOObject"

EOXS_OWS_SERVICE_HANDLERS
  The enabled OWS service handlers. This configuration specifies what OWS
  services and versions are available for this instance.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.ows.wcs.v10.handlers.GetCapabilitiesHandler',
          'eoxserver.services.ows.wcs.v10.handlers.DescribeCoverageHandler',
          'eoxserver.services.ows.wcs.v10.handlers.GetCoverageHandler',
          'eoxserver.services.ows.wcs.v11.handlers.GetCapabilitiesHandler',
          'eoxserver.services.ows.wcs.v11.handlers.DescribeCoverageHandler',
          'eoxserver.services.ows.wcs.v11.handlers.GetCoverageHandler',
          'eoxserver.services.ows.wcs.v20.handlers.GetCapabilitiesHandler',
          'eoxserver.services.ows.wcs.v20.handlers.DescribeCoverageHandler',
          'eoxserver.services.ows.wcs.v20.handlers.DescribeEOCoverageSetHandler',
          'eoxserver.services.ows.wcs.v20.handlers.GetCoverageHandler',
          'eoxserver.services.ows.wcs.v20.handlers.GetEOCoverageSetHandler',
          'eoxserver.services.ows.wms.v10.handlers.WMS10GetCapabilitiesHandler',
          'eoxserver.services.ows.wms.v10.handlers.WMS10GetMapHandler',
          'eoxserver.services.ows.wms.v11.handlers.WMS11GetCapabilitiesHandler',
          'eoxserver.services.ows.wms.v11.handlers.WMS11GetMapHandler',
          'eoxserver.services.ows.wms.v13.handlers.WMS13GetCapabilitiesHandler',
          'eoxserver.services.ows.wms.v13.handlers.WMS13GetMapHandler',
          'eoxserver.services.ows.wps.v10.getcapabilities.WPS10GetCapabilitiesHandler',
          'eoxserver.services.ows.wps.v10.describeprocess.WPS10DescribeProcessHandler',
          'eoxserver.services.ows.wps.v10.execute.WPS10ExecuteHandler',
          'eoxserver.services.ows.dseo.v10.handlers.GetCapabilitiesHandler',
          'eoxserver.services.ows.dseo.v10.handlers.GetProductHandler',
      ]

EOXS_OWS_EXCEPTION_HANDLERS
  The enabled OWS service exception handlers. This is similar to the service
  handlers, but defines how exceptions are encoded.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.ows.wcs.v10.exceptionhandler.WCS10ExceptionHandler',
          'eoxserver.services.ows.wcs.v11.exceptionhandler.WCS11ExceptionHandler',
          'eoxserver.services.ows.wcs.v20.exceptionhandler.WCS20ExceptionHandler',
          'eoxserver.services.ows.wms.v13.exceptionhandler.WMS13ExceptionHandler',
      ]

EOXS_CAPABILITIES_RENDERERS
  The WCS capabilities renderers to use. Each one is tried with the given
  request parameters and the first fitting one is used.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.native.wcs.capabilities_renderer.NativeWCS20CapabilitiesRenderer',
          'eoxserver.services.mapserver.wcs.capabilities_renderer.MapServerWCSCapabilitiesRenderer',
      ]

EOXS_COVERAGE_DESCRIPTION_RENDERERS
  The WCS coverage description renderers to use. For a DescribeCoverage request
  each implementation checked for compatibility and the first fitting one is
  used.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.mapserver.wcs.coverage_description_renderer.CoverageDescriptionMapServerRenderer',
          'eoxserver.services.native.wcs.coverage_description_renderer.NativeWCS20CoverageDescriptionRenderer',
      ]

EOXS_COVERAGE_RENDERERS
  The WCS coverage renderers to use. For a GetCoverage request each
  implementation checked for compatibility and the first fitting one is used.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.mapserver.wcs.coverage_renderer.RectifiedCoverageMapServerRenderer',
          'eoxserver.services.gdal.wcs.referenceable_dataset_renderer.GDALReferenceableDatasetRenderer',
      ]

EOXS_COVERAGE_ENCODING_EXTENSIONS
  Additional coverage encoding extensions to use.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.ows.wcs.v20.encodings.geotiff.WCS20GeoTIFFEncodingExtension'
      ]

EOXS_PROCESSES
  This setting defines what processes shall be available for WPS.

  Default:

  .. code-block:: python

      [
          'eoxserver.services.ows.wps.processes.get_time_data.GetTimeDataProcess'
      ]

EOXS_ASYNC_BACKENDS (=[])
  The enabled WPS asynchronous backends. This setting is necessary to enable
  asynchronous WPS.


Configurations in ``eoxserver.conf``
------------------------------------

The ``eoxserver.conf`` uses the ``.ini`` file structure. This means the file is
divided into sections like this: ``[some.section]``. The following sections and
their respective configuration keys are as follows:


[core.system]
  instance_id
    Mandatory. The ID (name) of your instance. This is used on several
    locations throughout EOxServer and is inserted into a number of service
    responses.


[processing.gdal.reftools]
  vrt_tmp_dir
    A path to a directory for temporary files created during the
    orthorectification of referencial coverages. This configuration option
    defaults to the `systems standard
    <http://docs.python.org/library/tempfile.html#tempfile.mkstemp>`_.

[resources.coverages.coverage_id]
  reservation_time
    Determines the time a coverage ID is reserved when inserting a coverage
    into the system. Needs to be in the following form:
    <days>:<hours>:<minutes>:<seconds> and defaults to `0:0:30:0`.

[services.owscommon]
  http_service_url
    Mandatory. This parameter is the actual domain and path URL to the OWS
    services served with the EOxServer instance. This parameter is used in
    various contexts and is also included in several OWS service responses.

[services.ows]
  This section entails various service metadata settings which are embedded in
  W*S GetCapabilities documents.

  update_sequence=20131219T132000Z
    The service capabilities update sequence. This is used for clients to
    determine whether or not the service experienced updates since the last
    sequence.

  name=EOxServer EO-WCS
    The service instance name.

  title=Test configuration of MapServer used to demonstrate EOxServer
    The service instance title.

  abstract=Test configuration of MapServer used to demonstrate EOxServer
    The service instance abstract/description.

  onlineresource=http://eoxserver.org
    The service link.

  keywords=<KEYWORDLIST>
    A comma separated list of keywords for this service.

  fees=None
    Some additional information about service fees.

  access_constraints=None
    Whether and how the service access is constrained.

  provider_name=<CONTACTORGANIZATION>
    The service providing organizations name.

  provider_site=<URL>
    The service providing organizations HTTP URL.

  individual_name=<CONTACTPERSON>
    The main contact persons name.

  position_name=<CONTACTPOSITION>
    The main contact persons position.

  phone_voice=<CONTACTVOICETELEPHONE>
    The main contact persons voice phone number.

  phone_facsimile=<CONTACTFACSIMILETELEPHONE>
    The main contact persons facsimile phone number.

  electronic_mail_address=<CONTACTELECTRONICMAILADDRESS>
    The main contact persons email address.

  delivery_point=<ADDRESS>
    The service providing organizations address.

  city=<CITY>
    The service providing organizations city.

  administrative_area=<STATEORPROVINCE>
    The service providing organizations province.

  postal_code=<POSTCODE>
    The service providing organizations postal code.

  country=<COUNTRY>
    The service providing organizations country.

  hours_of_service=<HOURSOFSERVICE>
    The service providing organizations hours of service.

  contact_instructions=<CONTACTINSTRUCTIONS>
    Additional contact instructions

  role=Service provider
    The service providing organizations role.

[services.ows.wms]
  supported_formats=<MIME type>[,<MIME type>[,<MIME type> ... ]]
    A comma-separated list of MIME-types defining the raster file format
    supported by the WMS ``getMap()`` operation. The MIME-types used for this
    option must be defined in the *Format Registry*
    (see ":ref:`FormatsConfiguration`").

  supported_crs=<EPSG-code>[,<EPSG-code>[,<EPSG-code> ... ]]
    List of common CRSes supported by the WMS ``getMap()`` operation
    (see also ":ref:`CRSConfiguration`").

[services.ows.wcs]
  supported_formats=<MIME type>[,<MIME type>[,<MIME type> ... ]]
    A comma-separated list of MIME-types defining the raster file format
    supported by the WCS ``getCoverage()`` operation. The MIME-types used for
    this option must be defined in the *Format Registry*
    (see ":ref:`FormatsConfiguration`").

  supported_crs= <EPSG-code>[,<EPSG-code>[,<EPSG-code> ... ]]
    List of common CRSes supported by the WCS ``getMap()`` operation.
    (see also ":ref:`CRSConfiguration`").

[services.ows.wcs20]
  paging_count_default=10
    The maximum number of `wcs:coverageDescription` elements returned in a WCS
    2.0 `EOCoverageSetDescription`. This also limits the :ref:`count parameter
    <table_eo-wcs_request_parameters_describeeocoverageset>`. Defaults to 10.

  default_native_format=<MIME-type>
    The default *native format* cases when the source format cannot be used
    (read-only GDAL driver) and  there is no explicit source-to-native format
    mapping.  This option must be always set to a valid format (GeoTIFF by
    default). The MIME-type used for this option must be defined in the
    *Format Registry* (see ":ref:`FormatsConfiguration`").

  source_to_native_format_map=[<src.MIME-type,native-MIME-type>[,<src.MIME-type,native-MIME-type> ... ]]
    The explicit source to native format mapping. As the name suggests, it
    defines mapping of the (zero, one, or more) source formats to a
    non-defaults native formats. The source formats are not restricted to the
    read-only ones. This option accepts comma-separated list of MIME-type
    pairs. The MIME-types used for this option must be defined in the
    *Format Registry* (see ":ref:`FormatsConfiguration`").

  maxsize=2048
    The maximum size for each dimension in WCS GetCoverage responses. All sizes
    above will result in exception reports.

.. _InstanceSetup:

Setup
-----

When your instance is configured, several steps need to be taken in order to
set up the application. First off, the configured database needs to be
migrated. This is achieved using the `migrate
<https://docs.djangoproject.com/en/2.2/ref/django-admin/#django-admin-migrate>`_
command. The following command performs the necessary migrations:

.. code-block:: bash

    python manage.py migrate

Migration performs various steps depending on the necessity. For example it
creates a database schema if it is not already present. If there already is a
database schema, it is inspected to see whether it needs to be updated. If yes
both the schema and the data already in the database will be updated.

Finally all the static files need to be collected at the location configured
by ``STATIC_ROOT`` in ``settings.py`` by using the following command from
within your instance:

.. code-block:: bash

    python manage.py collectstatic
