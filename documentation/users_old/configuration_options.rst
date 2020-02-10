.. ConfigurationOptions
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Fabian Schindler <fabian.schindler@eox.at>
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
    single: Configuration Options

.. _ConfigurationOptions:

Configuration Options
=====================

In this section, all valid configuration options and their interpretations are
listed.


[core.system]
-------------

::

    instance_id

Mandatory. The ID (name) of your instance. This is used on several locations
throughout EOxServer and is inserted into a number of service responses.


[processing.gdal.reftools]
--------------------------

::

    vrt_tmp_dir

A path to a directory for temporary files created during the orthorectification
of referencial coverages. This configuration option defaults to the `systems
standard <http://docs.python.org/library/tempfile.html#tempfile.mkstemp>`_.

[backends.cache]
----------------

In future, options in this section will influence the behavior of caching of
FTP and rasdaman data.


[resources.coverages.coverage_id]
---------------------------------

::

    reservation_time

Determines the time a coverage ID is reserved when inserting a coverage into
the system. Needs to be in the following form:
<days>:<hours>:<minutes>:<seconds> and defaults to `0:0:30:0`.


[services.owscommon]
--------------------

::

    http_service_url

Mandatory. This parameter is the actual domain and path URL to the OWS services
served with the EOxServer instance. This parameter is used in various contexts
and is also included in several OWS service responses.


[services.ows]
--------------

This section entails various service metadata settings which are embedded in 
W*S GetCapabilities documents.

::

    update_sequence=20131219T132000Z

::

    name=EOxServer EO-WCS

::

    title=Test configuration of MapServer used to demonstrate EOxServer

::

    abstract=Test configuration of MapServer used to demonstrate EOxServer

::

    onlineresource=http://eoxserver.org

::

    keywords=<KEYWORDLIST>

::

    fees=None

::

    access_constraints=None

::

    provider_name=<CONTACTORGANIZATION>

::

    provider_site=<URL>

::

    individual_name=<CONTACTPERSON>

::

    position_name=<CONTACTPOSITION>

::

    phone_voice=<CONTACTVOICETELEPHONE>

::

    phone_facsimile=<CONTACTFACSIMILETELEPHONE>

::

    delivery_point=<ADDRESS>

::

    city=<CITY>

::

    administrative_area=<STATEORPROVINCE>

::

    postal_code=<POSTCODE>

::

    country=<COUNTRY>

::

    electronic_mail_address=<CONTACTELECTRONICMAILADDRESS>

::

    hours_of_service=<HOURSOFSERVICE>

::

    contact_instructions=<CONTACTINSTRUCTIONS>


::

    role=Service provider



[services.ows.wms]
------------------

::

    supported_formats=<MIME type>[,<MIME type>[,<MIME type> ... ]]

A comma-separated list of MIME-types defining the raster file format supported
by the WMS ``getMap()`` operation. The MIME-types used for this option must be
defined in the *Format Registry* (see ":ref:`FormatsConfiguration`").

:: 

    supported_crs= <EPSG-code>[,<EPSG-code>[,<EPSG-code> ... ]]

List of common CRSes supported by the WMS ``getMap()`` operation 
(see also ":ref:`CRSConfiguration`").

[services.ows.wcs]
------------------

::

    supported_formats=<MIME type>[,<MIME type>[,<MIME type> ... ]]

A comma-separated list of MIME-types defining the raster file format supported
by the WCS ``getCoverage()`` operation. The MIME-types used for this option must
be defined in the *Format Registry* (see  ":ref:`FormatsConfiguration`").
:: 

    supported_crs= <EPSG-code>[,<EPSG-code>[,<EPSG-code> ... ]]

List of common CRSes supported by the WCS ``getMap()`` operation.
(see also ":ref:`CRSConfiguration`").

[services.ows.wcs20]
--------------------

::

    paging_count_default

The maximum number of `wcs:coverageDescription` elements returned in a WCS 2.0
`EOCoverageSetDescription`. This also limits the :ref:`count parameter
<table_eo-wcs_request_parameters_describeeocoverageset>`. Defaults to 10.

:: 

    default_native_format=<MIME-type>

The default *native format* cases when the source format cannot be used
(read-only GDAL driver) and  there is no explicit source-to-native format
mapping.  This option must be always set to a valid format (GeoTIFF by default).
The MIME-type used for this option must be defined in the *Format Registry* (see
":ref:`FormatsConfiguration`").

::

    source_to_native_format_map=[<src.MIME-type,native-MIME-type>[,<src.MIME-type,native-MIME-type> ... ]]

The explicit source to native format mapping. As the name suggests, it defines
mapping of the (zero, one, or more) source formats to a non-defaults native
formats. The source formats are not restricted to the read-only ones. This
option accepts comma-separated list of MIME-type pairs.   
The MIME-types used for this option must be defined in the *Format Registry* (see
":ref:`FormatsConfiguration`").
    

::

    maxsize = 2048

The maximum size for each dimension in WCS GetCoverage responses. All sizes 
above will result in exception reports.


.. _ConfigurationOptionsWCST11:

[services.ows.wcst11]
---------------------

::

    allow_multiple_actions

This flag enables/disables mutiple actions per WCSt request. Defaults to `False`.

NOTE: It is safer to keep this feature disabled. In case of a failure of one of
the multiple actions, an OWS exception is returned without any notification which
of the actions were actually performed, and which have not been performed at all.
Therefore, we recomend to use only one action per request. 

::

    allowed_actions

Comma-separated list of allowed actions. Each item is one of `Add`, `Delete`,
`UpdateAll`, `UpdateMetadata` and `UpdateDataPart`. By default no action is
allowed and each needs to be explicitly activated. Currently, only the `Add` and
`Delete` actions are implemented by the EOxServer. 

::

    path_wcst_temp

Mandatory. A path to an existing directory for temporary data storage during the
WCS-T request processing. This should be a directory which is not used in any
other context, since it might be cleared under certain circumstances.

::

    path_wcst_perm

Mandatory. A path to a directory for permanent storage of transacted data. This
is the final location where transacted datasets will be stored. It is also a
place where the `Delete` action (when enabled) is allowed to remove the stored
data.


[services.auth.base]
--------------------

For detailed information about authorization refer to the documentation of the
:ref:`Identity Management System`.

::

    pdb_type

Determine the Policy Decision Point type; defaults to 'none' which deactives
authorization.

::

    authz_service

URL of the Authorization Service.

::

    attribute_mapping

Path to an attribute dictionary for user attributes.

::

    serviceID

Sets a custom service identifier


::

    allowLocal

Allows full local access to the EOxServer. Use with care!


[webclient]
-----------

The following configuration options affect the behavior of the :ref:`Webclient
interface <webclient>`.

::

    preview_service
    outline_service

The service type for the outline and the preview layer in the webclient map.
One of `wms` (default) or `wmts`.

::

    preview_url
    outline_url

The URL of the preview and outline service. Defaults to the vaule of the
`services.owscommon.http_service_url` configuration option.


.. _config-testing:

[testing]
---------

These configuration options are used within the context of the :ref:`Autotest
instance <Autotest>`.

::

    binary_raster_comparison_enabled

Enable/disable the binary comparison of rasters in test runs. If disabled these
tests will be skipped. By default this feature is activated but might be turned
off in order to prevent test failures originating on platform differences.

::

    rasdaman_enabled

Enable/disable rasdaman test cases. If disabled these tests will be skipped.
Defaults to `false`.
