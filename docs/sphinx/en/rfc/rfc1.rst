.. RFC 1: Software Architecture
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
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
   single: RFC; RFC 1
   single: software architecture; overview
   
.. _rfc1:

RFC 1: An Extensible Software Architecture for EOxServer
========================================================

:Author: Stephan Krause
:Created: 2011-02-18
:Last Edit: 2011-07-20
:Status: ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc1

This RFC proposes an extensible software architecture for EOxServer that
is based on the following ideas:

* Separation of instance and distribution code
* Structuring of the distribution in layers
* Extensibility through a plugin system

.. _rfc1_intro:

Introduction
------------

EOxServer development has been initiated in the course of two ESA
projects that aim at providing a harmonized standard interface to
access Earth Observation (EO) products, namely:

* Heterogeneous Mission Accessibility - Follow-On Open Data Access 
  (HMA-FO ODA)
* Open-standard Online Observation Service (O3S)

The specification of a software architecture is required by these
projects. From a practical point of view, EOxServer has reached a point
where a common framework for a rapidly evolving project is needed.

Summarizing the requirements in a nutshell EOxServer has to integrate:

* different OGC Web Services
* different data and processing resources
* heterogeneous data and metadata formats

This leads to the conclusion that an extensible software architecture
is needed. The problems to address are discussed in further detail in
the :ref:`rfc1_req` section.

The :ref:`proposed architecture <rfc1_prop_arch>` is modular, extensible
and flexible and structured in layers. The following separate components
are identified:

* Distribution

  * :ref:`rfc1_core`
  * :ref:`rfc1_svc_lyr`
  * :ref:`rfc1_proc_lyr`
  * :ref:`rfc1_dint_lyr`
  * :ref:`rfc1_dacc_lyr`
  
* :ref:`rfc1_inst`

In this architecture the Core shall provide the central logic for
the extension mechanism while the layers shall contain interface
definitions based on the extension model of the Core that can be
implemented by extending modules and plugins.

.. index::
   single: software architecture; requirements

.. _rfc1_req:

Requirements
------------

The main sources of requirements for EOxServer at the moment of writing
this RFC are:

* the `HMA-FO Open Data Access Sofware Requirements Specification (SRS) 
  <http://wiki.services.eoportal.org/tiki-download_wiki_attachment.php?attId=957&download=y>`_
* the O3S Software System Specification (SSS)
* the feature requests posted on the `EOxServer Trac
  <http://www.eoxserver.org>`_

Most of the requirements are related to the features EOxServer shall
implement. There is one requirement, however, in the O3S SSS that is
directly related to the software architecture;
`O3S_QUA_004 <https://o3s.eox.at/requirements/ticket/122>`_ states:

  The O3S3 shall sustain maintainability and reusability by using a
  modular system architecture
  
  This shall facilitate

  * isolation and removal of code defects
  * integration of new functionality, such as the implementation of new
    interface standard versions
  * extension of the system functionality according to new or modified
    requirements

Thus, modularity as well as integration and extension of functionality
are central issues in the drafting of the EOxServer software
architecture. The question remains what considerations shall govern the
structuring of the software into modules, what functionality it shall
implement and in what way the system shall be able to be extended.

Our approach to this question is to identify different topics of concern
for the EOxServer development that shall structure the requirements
analysis and give a first hint on the architectural design.

The main goal of EOxServer is to furnish an implementation of `OGC
<http://www.opengeospatial.org>`_ Web Services (OWS) intended for use
within the Earth Observation (EO) domain. These :ref:`services
<rfc1_req_svc>` shall provide access to different kinds of
:ref:`resources <rfc1_req_res>` and to :ref:`processes <rfc1_req_proc>`
operating on these resources. The requirements cite different
:ref:`backends <rfc1_req_backend>` that the software shall implement in
order to allow access to local and remote content. Finally, we discuss
where and how the software is going to be :ref:`deployed
<rfc1_req_deploy>`.

.. _rfc1_req_svc:

Services
~~~~~~~~

The following OGC Web Services shall be implemented:

`Web Coverage Service (WCS)
<http://www.opengeospatial.org/standards/wcs>`_ (requirement 
`O3S_CAP_001 <https://o3s.eox.at/requirements/ticket/7>`_)

  The Web Coverage Service shall be able to present Earth Observation
  data, e.g. optical satellite imagery, SAR data, etc. The following
  extensions shall be implemented:

  Earth Observation Application Profile for WCS (EO-WCS) (requirement
  `O3S_CAP_100 <https://o3s.eox.at/requirements/ticket/8>`_)

    This application profile is intended to ease access to large
    collections of Earth Observation data.

  Transactional WCS (WCS-T) (requirement
  `O3S_CAP_150 <https://o3s.eox.at/requirements/ticket/198>`_)

    This extension of WCS introduces a Transaction operation that
    supports transfer of data *to* a WCS server.

`Web Map Service (WMS) <http://www.opengeospatial.org/standards/wms>`_
(requirement
`O3S_CAP_220 <https://o3s.eox.at/requirements/ticket/204>`_)

  This service shall be used to give to portrayals of the coverages
  the system presents. The following extension shall be implemented:
  
  WMS Profile for EO Products (EO-WMS) (requirement
  `O3S_CAP_240 <https://o3s.eox.at/requirements/ticket/210>`_)

    The extension allows access to portrayals of large dataset series.

`Web Feature Service (WFS)
<http://www.opengeospatial.org/standards/wfs>`_ (requirement
`O3S_CAP_260 <https://o3s.eox.at/requirements/ticket/214>`_)

  This service shall be used to present vector data.

`Web Processing Service (WPS)
<http://www.opengeospatial.org/standards/wps>`_ (requirement 
`O3S_CAP_200 <https://o3s.eox.at/requirements/ticket/9>`_)

  This service shall be used to make processing resources accessible
  online.

.. _rfc1_req_proc:

Processes
~~~~~~~~~

EOxServer shall present various processes to the public using WPS. The
processes planned for implementation at the moment of writing this RFC
are specific to the use cases to be handled in the course of the O3S
project. The capability to publish a variety of processes on the other
hand is a general requirement for EOxServer. 

Being a project focussing on the EO domain EOxServer concentrates on
the processing of EO coverage (raster) data. So, the considerations
made for coverages regarding the variety of data and metadata
:ref:`formats <rfc1_formats>` are valid for processes as well.

.. _rfc1_req_res:

Resources
~~~~~~~~~

EOxServer shall enable public access to different kinds of geo-spatial
resources in the Earth Observation domain. These are:

* Coverages
* Vector Data
* Processes

Coverages
^^^^^^^^^

Coverages are defined in a very abstract way. What EOxServer focusses on
are coverages dealt with by the Earth Observation Application Profile
for WCS (EO-WCS) which is a draft OGC Best Practice Paper as of writing
this RFC. The main categories of resources defined in that paper are:

Datasets
  Datasets are the atomic components EO-WCS objects are composed of.
  They are coverages that are associated with EO Metadata. EO satellite
  mission scenes are a good example of Datasets. They can be accessed
  individually even when being part of a Stitched Mosaic or Dataset
  Series.

Stitched Mosaics
  Stitched Mosaics are made up from a collection of Datasets that share
  a common range type and grid. Other than Dataset Series they are not
  merely a container for Datasets but coverages themselves. The coverage
  values are generated from the contributing datasets. This process must
  follow some rule to decide what value to take into account in the
  areas where the contributing Datasets overlap. The most common rule
  is "latest-on-top".

Dataset Series
  Dataset Series represent collections of Datasets or Stitched Mosaics.
  They do not impose any constraints on the contained objects, so very
  heterogeneous data can be included in the same series.

.. _rfc1_formats:
  
A major problem for the EOxServer implementation is that raster data
coverages originating from EO satellite missions are very heterogeneous.
They can use a vide variety of data and metadata formats and are often
associated with additional data like bitmasks, etc. that should be
presented by EOxServer as well. Furthermore, the data packaging is
different for every mission.

Vector Data
^^^^^^^^^^^

Support for Vector Data handling is required by O3S Use Case 2. In that
use case road network data shall be generated from Pléiades satellite
data using automated feature detection algorithms. The road network data
shall be presented using WFS and WMS.

.. _rfc1_req_backend:

Backends
~~~~~~~~

EOxServer shall implement various backends to access data it presents
to the public via the OGC Web Services:

* Backend for local data (requirement `O3S_CAP_013
  <https://o3s.eox.at/requirements/ticket/68>`_)
* Backends for remote data (requirements: HMA-FO SR_ODA_IF_070,
  `O3S_CAP_014 <https://o3s.eox.at/requirements/ticket/69>`_)

  * using HTTP/HTTPS
  * using FTP
  * using WCS

* Backend for retrieving data from `rasdaman <http://www.rasdaman.com>`_
  (requirement `O3S_CAP_017
  <https://o3s.eox.at/requirements/ticket/183>`_)

.. _rfc1_req_deploy:

Deployment
~~~~~~~~~~

The only requirements originating from the HMA-FO ODA and O3S projects
regarding deployment concern the implementation of the O3S Use Cases.
Every use case requires one or more instances of EOxServer to be
deployed. The instances have different purposes and thus shall present
different services and different resources.

The fact that EOxServer shall be deployed many times in different
configurations (possibly on the same server) calls for a strict
separation of distribution and instance data.

The ability to activate or deactivate various components of the system
implies not only that the architecture must be modular but also that it
must be configurable to use different combinations of modules.

.. _rfc1_req_summary:

Summary
~~~~~~~

The conclusion of the requirements review is that the EOxServer
Architecture shall be:

* modular
* extensible
* flexible in the sense that it must be possible to select different
  combinations of modules to deploy and activate
* able to present resources using different OGC Web Services
* able to access data from different backends
* able to handle different data, metadata and packaging formats
* separating distribution and instance data

The development of the software architecture will be based on these
considerations.

Architecture Overview
---------------------

The software architecture development for EOxServer does not start at
zero. There are already considerations made in the proposal phase of
the O3S project and there is the status quo of version 0.1.0. Taking
into account this preparational work and the outcomes of the
requirements review, the outlines of the :ref:`rfc1_prop_arch` will be
developed in the last subsection and the following sections.

Draft Architecture
~~~~~~~~~~~~~~~~~~

.. index::
   single: software architecture; draft architecture

The O3S draft Architectural Design Document (ADD/SDD) has already
proposed a software architecture which is, however, outdated in certain
aspects due to changes made in the requirements phase of O3S. Here is an
overview of the O3S draft architecture:

.. figure:: resources/rfc1/O3S_Server_Software_Components.png
   :width: 75%
   :align: center

   *Draft architecture from O3S Proposal*
   
This identifies four servers and extending modules:

* WPS Server
* WCS Server

  * WCS Earth Observation Application Profile Module
  * WCS-T Module
  * WCPS Module (not included in the requirements any more)

* WFS Server

  * WFS-T Module (not included in the requirements any more)

* WMS Server

  * WMS Profile for EO Products Module

Furthermore the architecture proposes to use `PyWPS
<http://pywps.wald.intevation.org/>`_ and `MapServer
<http://www.mapserver.org>`_ as middleware for handling OGC Web Service
requests.

An additional integrating Data Access Layer is foreseen that
shall implement storage patterns such as image pyramids and offer an API
to read and write data that hides the internal details of data storage
from the service and extension modules using it.

`PostgreSQL <http://www.postgresql.org>`_ with its geo-spatial extension
`PostGIS <http://postgis.refractions.net>`_ has been planned as
relational database backend. Finally, the system relies on the local
filesystem as its only storage backend.

During the requirements phase of O3S and the early development of
EOxServer many deviations from this original design have been made
necessary. Most importantly:

* `Django <http://www.djangoproject.com>`_ has been added as dependency
* `GDAL <http://www.gdal.org>`_ has been added as dependency
* the implementation of WCPS has been postponed
* the implementation of WFS-T has been postponed
* Django has made use of different geo-spatial database backends possible
* requirements for remote storage backends have been added

Although the basic concepts of the draft architecture remain valid, an
updated version is needed for EOxServer to fulfill its requirements and
evolve beyond the project horizon of O3S.

Status Quo of Release 0.1.1
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index ::
   single: software architecture; release 0.1.1

As of release 0.1.1 EOxServer is an integrated Django project including
a single Django application and additional modules that support OGC Web
Service (OWS) request handling and data integration.

The data model is contained in the ``eoxserver.server`` application. So
is the ``ows`` view, the central entrance point for OWS requests, and
the administration client view as well as tools for automatic data
ingestion.

Supporting modules are gathered in the ``eoxserver.lib`` module. These
contain the core application logic for OWS request handling, coverage
and metadata manipulation as well as utilities e.g. for XML processing.

EOxServer 0.1.1 includes an extension mechanism already which so far is
restricted to services. The ``eoxserver.lib.registry`` module maintains
a central registry for the concrete implementations of OWS interfaces
which may be published in the ``eoxserver.modules`` namespace. At the
moment there are implementations for WMS 1.0, 1.1 and 1.3, WCS 1.0, 1.1 
and 2.0 as well as a preliminary version of EO-WCS. All these modules
use MapServer MapScript for image manipulation and part of the request
handling in the backend.

This approach fulfills some of the requirements summarized :ref:`above
<rfc1_req_summary>` already, but further development of the architecture
and the code is necessary to be fully compliant. Most
importantly:

* extensibility and flexibility have to be enhanced
* WPS must be implemented
* WFS must be implemented
* support for remote backends is necessary

.. index::
   single: software architecture; layers
   single: dynamic binding
   single: Service Layer
   single: Processing Layer
   single: Data Integration Layer
   single: Data Access Layer
   
.. _rfc1_prop_arch:

Proposed Architecture
~~~~~~~~~~~~~~~~~~~~~

The proposed architecture for EOxServer shall be based on the following
principles:

* **Separation of Instance and Distribution**: instance applications
  shall be separated from EOxServer distribution code in order to
  facilitate deployment of multiple services on the same machine and to
  support flexible configurations of services
* **Layered Architecture of the Distribution**: The software
  architecture shall be structured in layers and a core that contains
  basic common functionality; each layer builds on the capabilities of
  the underlying ones to fulfill its tasks
* **Extensibility**: the EOxServer distribution shall be extensible by
  additional modules and plugins; the distribution core shall provide
  functionality to enable dynamic binding to extending modules
  
The identification of different layers is performed based on the
structuring of the system components underlying the requirements
analysis.

Dependencies
^^^^^^^^^^^^

The implementation of EOxServer shall use the following
dependencies:

* **Python**: `Python <http://www.python.org>`_ shall serve as the
  implementation language; it has been chosen because
  
  * it facilitates rapid development
  * the geospatial libraries used all have Python bindings
  
* **Django**: `Django <http://www.djangoproject.com>`_ has been
  selected as development framework because
  
  * it provides an object-relational mapper that supports various
    database backends
  * it supports geospatial databases and integrates vector data handling
    functionality in the GeoDjango extension
  * it allows for rapid web application development
  
* **Spatial Database Backend**: using GeoDjango, EOxServer shall support
  at least the `SpatiaLite <http://www.gaia-gis.it/spatialite/>`_ and
  `PostGIS <http://postgis.refractions.net>`_ geospatially enabled
  RDBMS backends. 
* **MapServer**: EOxServer shall build on `MapServer
  <http://www.mapserver.org>`_ MapScript in order to facilitate OGC
  Web Service handling
* **GDAL/OGR**: For image processing tasks and vector data manipulation
  the Python binding of the `GDAL/OGR <http://www.gdal.org>`_ libraries
  shall be used
  
Concerning the software architecture, the use of Django enforces a
Model-View-Controller (MVC) substructure of the distribution layers of
EOxServer.

Distribution Core and Layers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The breakdown of the distribution into core and layers is as follows:

Core
  The Core shall contain modules for common use throughout the different
  components of EOxServer. This includes the global configuration data
  model, the implementation of the extension mechanism as well as the
  basic functionality for the EOxServer administration client

Service Layer
  This layer contains the core request handling logic as well as the
  implementation of services and service extensions
  
Processing Layer
  This layer contains the processing models used internally by EOxServer
  as well as the data model and the basic handling routines for
  processes to be published using WPS

Data Integration Layer
  This layer shall provide data models for resources as well as an
  abstraction layer for different data formats and data packaging
  formats
  
Data Access Layer
  This layer shall provide backends for local and remote data access
  
.. figure:: resources/rfc1/EOxServer_Distribution_Breakdown.png
   :width: 75%
   :align: center
   
   *EOxServer Distribution Breakdown*

Each of the four layers shall be sub-structured in:

* data model
* views 

  * for public access (if applicable)
  * for the administration client

* core handling logic
* interface definitions for extensions
* modules implementing the interface definitions
  
Structure of the Architecture Specification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The further specification of the proposed architecture is subdivided
into several sections and separate RFCs. This RFC 1 contains a
description of the different architectural layers and of EOxServer
instances:

* :ref:`rfc1_core`
* :ref:`rfc1_svc_lyr`
* :ref:`rfc1_proc_lyr`
* :ref:`rfc1_dint_lyr`
* :ref:`rfc1_dacc_lyr`
* :ref:`rfc1_inst`

The following RFCs discuss different aspects of the architecture in
further detail:

.. toctree::
   :maxdepth: 1

   rfc2
   rfc3
   rfc4
   rfc5
   rfc6

.. index:: Distribution Core

.. _rfc1_core:

Distribution Core
-----------------

The Core shall act as a "glue" for EOxServer that links the different
parts of the software together and provides functionality used
throughout the EOxServer project.

It defines the core of the configuration data model which is extended
by the layers and implementing modules. The configuration is partly
stored in the database and partly in files. Both parts need to be
easily modifiable and extensible.

Therefore the Core also includes an administration client that can be
used by system operators to edit the part of the configuration
stored in the database. The basic functionality of the administrator,
the entry view and its extension mechanisms shall be part of the Core.

The Core includes modules for common use, for instance utilities for the
handling of spatio-temporal metadata as well as for decoding and
encoding of XML documents.

Most importantly, the Core contains the central logic that enables the
dynamic extension of system functionality. The layers shall provide
interface definitions based on the extension model of the Core that can
be implemented by extending modules and plugins. For more details see
:doc:`rfc2`.

.. index:: Service Layer

.. _rfc1_svc_lyr:

Service Layer
-------------

The Service Layer contains the OWS request handling logic as well as the
implementation of services and service extensions.

It defines a configuration **data model** for OGC Web Services and for
their metadata. The model includes:

* service metadata to be published in the GetCapabilities response
* options to enable or disable a specific service or service extension
  for a given data source
* options to configure the services themselves, e.g. enabling or
  disabling certain non-mandatory features

The Service Layer provides **views** for public access, namely the
central entrance point for OWS requests. It also contains views for the
administration client that allow to configure services and service
metadata.

The **core handling logic** for OGC Web Services is part of the Service
Layer. It implements the behaviour defined by OWS Common and defines
a structured approach to request handling that discerns different
levels:

* services
* service versions
* service extensions
* service operations

The way services and service extensions interact is described in further
detail in :doc:`rfc3`.

The Service Layer defines request handler **interfaces** for each of
these levels that are **implemented** by modules for:

* WPS
* WCS
  
  * EO-WCS
  * WCS-T

* WMS

  * EO-WMS

* WFS

.. index:: Processing Layer

.. _rfc1_proc_lyr:

Processing Layer
----------------

The Processing Layer contains the processing models used internally by
EOxServer as well as the data model and the basic handling routines for
processes to be published using WPS.

In its **data model** it defines the configuration options and metadata
for processes. The model shall also support processing chains as 
described in further detail in :doc:`rfc5`. The Processing Layer
publishes administration client **views** to support the configuration
of processes and processing chains.

The Processing Layer defines **interfaces** for processes. It also
contains implementations of the processes used internally by EOxServer;
these include:

* coverage tiling
* coverage mosaicking

Further processes as required e.g. by the O3S Use Cases will be added as
plugins based on the data model and interface definitions of the
Processing Layer.

.. index:: Data Integration Layer

.. _rfc1_dint_lyr:

Data Integration Layer
----------------------

The Data Integration Layer shall provide data models for resources as
well as an abstraction layer for different data formats and data
packaging formats.

Data packaging formats are explained in greater detail in :doc:`rfc4`.
Roughly speaking, they represent the way data and metadata for an
EO product or derived product are packaged. They shall abstract from the
actual substructure of the packaging format in directories and files
so these resources can be handled transparently by EOxServer.

Its **data model** shall include items common to all types of data as
well as individual models for:

* coverages
* vector data
* metadata

Just as the other layers the Data Integration Layer shall publish
administration client **views** that support adding, modifying and
removal of resources and their respective metadata.

The **interface definitions** of the Data Integration Layer shall
provide an abstraction layer for:

* various data formats
* various metadata formats
* various data packaging formats

The modules **implementing** these interfaces shall support:

* coverage data formats supported by:

  * `GDAL <http://www.gdal.org>`_
  * `NEST <http://www.array.ca/nest>`_ (optional)

* vector data formats supported by `OGR <http://www.gdal.org/ogr/>`_
* metadata formats:

  * EO-GML
  * DIMAP (optional)
  * INSPIRE (optional)
  * GSC-DA (optional)
  
* data packaging formats:

  * directories
  * ZIP archives
  * TAR archives
  * compressed file formats:

    * ZIP
    * GZIP
    * BZ2

.. index:: Data Access Layer

.. _rfc1_dacc_lyr:

Data Access Layer
-----------------

The Data Access Layer shall provide transparent access to local and
remote data using different backends. It constitutes an abstraction
layer for data sources.

Its **data model** therefore provides configuration options for the
backends. It contains **views** for the administration client to
configure different data sources.

The Data Access Layer is built around the **interface definitions** of
backends and data sources stored by them. The following backends need to
be **implemented**:

* local backends:
  
  * file system
  * `rasdaman <http://www.rasdaman.com>`_ backend

* remote backends:

  * using HTTP/HTTPS
  * using FTP
  * using WCS

.. index:: EOxServer instances
  
.. _rfc1_inst:

Instances
---------

EOxServer instances are Django projects that import different EOxServer
modules as Django applications.

Like every Django project they contain a settings file that governs
the Django configuration and in addition the most basic parts of
EOxServer configuration. Specifically:

* the connection details for the database containing the EOxServer
  configuration is defined in the settings file
* the Django ``INSTALLED_APPS`` setting must be used to define the
  parts of the EOxServer data model that shall be loaded
* some EOxServer configuration settings that are needed in the startup
  phase will be appended to the Django settings file

Apart from the settings, every Django project has an "urlconf" that
defines which URLs shall point to the different views of the project.
For using the full EOxServer functionality there have to be URLs
pointing to the Service Layer OWS entrance point and the administration
client entrance point defined by the EOxServer core.

Furthermore the instance contains the Django configuration files whose
content is defined by the configuration data model of the Core and the
layers.

Optionally, the instance directory may include subdirectories for the
data (if stored locally) and the database (if using the file-based
SpatiaLite spatial database backend).

Finally, in a production setting, it shall contain the modules needed to
deploy the instance. The favourite deployment method is WSGI (see
:pep:`333`). These must be configured as well to include the path to the
instance.

The Django project may or may not contain applications itself, which
may or may not use EOxServer functionality. Writing an own application
is not necessary to use EOxServer, though; placing links to EOxServer
views in the urlconf is sufficient.

Voting History
--------------

Moved to ACCEPTED by unanimous consent without a formal vote on July
20th, 2011.

Traceability
------------

:Requirements: HMA-FO SR_ODA_IF_070,
               `O3S_CAP_001 <https://o3s.eox.at/requirements/ticket/7>`_,
               `O3S_CAP_013 <https://o3s.eox.at/requirements/ticket/68>`_,
               `O3S_CAP_014 <https://o3s.eox.at/requirements/ticket/69>`_,
               `O3S_CAP_017 <https://o3s.eox.at/requirements/ticket/183>`_,
               `O3S_CAP_100 <https://o3s.eox.at/requirements/ticket/8>`_,
               `O3S_CAP_150 <https://o3s.eox.at/requirements/ticket/198>`_,
               `O3S_CAP_200 <https://o3s.eox.at/requirements/ticket/9>`_,
               `O3S_CAP_220 <https://o3s.eox.at/requirements/ticket/204>`_,
               `O3S_CAP_240 <https://o3s.eox.at/requirements/ticket/210>`_,
               `O3S_CAP_260 <https://o3s.eox.at/requirements/ticket/214>`_,
               `O3S_QUA_004 <https://o3s.eox.at/requirements/ticket/122>`_
:Tickets: N/A
