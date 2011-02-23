.. RFC 1: Software Architecture

.. index::
   single: RFC; RFC 1
   single: software architecture
   
.. _rfc1:

RFC 1: An Extensible Software Architecture for EOxServer
========================================================

:Author: Stephan Krause
:Created: 2011-02-18
:Last Edit: 2011-02-21
:Status: IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc1

This RFC proposes an extensible software architecture for EOxServer that
is based on the following ideas:

* Separation of instance and distribution code
* Structuring of the distribution in data model, views and a controller
  core plus extending modules
* Extensibility through a plugin system

.. _rfc1_intro:

Introduction
------------

* Motivation
* Problems to address
* Proposed solution

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

Thus, the integration and extension of functionality must be a main
issue in the drafting of the EOxServer software architecture. Digging
deeper into the requirements specifications we will find out more
about what :ref:`rfc1_req_func` is needed, what :ref:`rfc1_req_res`
shall be handled by the software and where it is going to be
:ref:`deployed <rfc1_req_deploy>`.

.. _rfc1_req_func:

Functionality
~~~~~~~~~~~~~

The main goal of EOxServer is to furnish an implementation of `OGC
<http://www.opengeospatial.org>`_ Web Services (OWS) intended for use
within the Earth Observation (EO) domain. These :ref:`services
<rfc1_req_svc>` need access to :ref:`data <rfc1_req_res>`. The
requirements document of HMA-FO cites different :ref:`backends
<rfc1_req_backend>` that the software shall implement in order to allow
access to local and remote content.

.. _rfc1_req_svc:

Services
^^^^^^^^

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

.. _rfc1_req_backend:

Backends
^^^^^^^^

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

Processes
^^^^^^^^^

EOxServer shall present various processes to the public using WPS. The
processes planned for implementation at the moment of writing this RFC
are specific to the use cases to be handled in the course of the O3S
project. The capability to publish a variety of processes on the other
hand is a general requirement for EOxServer. 

Being a project focussing on the EO domain EOxServer concentrates on
the processing of EO coverage (raster) data. So, the considerations
made for coverages regarding the variety of data and metadata
:ref:`formats <rfc1_formats>` are valid for processes as well.

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

Summary
~~~~~~~

The conclusion of the requirements review is that the EOxServer
Architecture shall be:

* modular
* extensible
* able to present resources using different OGC Web Services
* able to access data from different backends
* able to handle different data, metadata and packaging formats
* separating distribution and instance data
* flexible in the sense that it must be possible to select different
  combinations of modules to deploy and activate

In the following sections we will develop a proposed software
architecture based on these considerations.

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

* O3S draft ADD/SDD
* identified components

.. figure:: resources/rfc1/O3S_Server_Software_Components.png
   :width: 75%
   :align: center

   Draft architecture from O3S Proposal


Dependencies
~~~~~~~~~~~~

* Django
* MapServer
* GDAL


.. _rfc1_prop_arch:

Proposed Architecture
~~~~~~~~~~~~~~~~~~~~~

Distribution and Instances
--------------------------

* instance items

  * Django project
  * Django application
  * settings
  * configuration
  * data
  * deployment

* distribution

  * data model
  * views (ows, admin)
  * controller

Structure of the Distribution Code
----------------------------------

* core
* Django applications for coverages, vector data
* extension modules and plugins
* extension mechanism see :doc:`rfc2`

Modules and Plugins
-------------------

* modules: built-in extensions of the core

  * services
  * backends
  * basic data and metadata formats
  * processes used in the ingestion chain see :doc:`rfc5`
  
* plugins: additional extensions of the core or the modules

  * data and metadata formats
  * additional processes
  * ...


Directory Structure
-------------------

* distribution

  * ``core``
  * ``coverage``
  * ``vector``
  * ``services``
  * ``processes``
  * ``formats``
  * ``plugins``
  
* instance

  * ``settings.py``
  * ``manage.py``
  * ``urls.py``
  * ``conf``
  
    * ``eoxserver.conf``
    * ``template.map``
  
  * ``data``
  * ``db``
  * ``plugins``

Voting History
--------------

N/A

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
