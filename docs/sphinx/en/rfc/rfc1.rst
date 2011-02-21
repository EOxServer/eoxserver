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
deeper into the requirements specifications we will found out more
about what :ref:`rfc1_req_func` is needed, what :ref:`rfc1_req_res`
shall be handled by the software and where it is going to be `deployed
<rfc1_req_deploy>`_.

.. _rfc1_req_func:

Functionality
~~~~~~~~~~~~~

Services
^^^^^^^^

* WCS

  * EO-WCS

* WMS

  * EO-WMS

* WFS

  * WFS-T

* WPS

Backends
^^^^^^^^

* Local
* Remote

  * HTTP
  * FTP

.. _rfc1_req_res:

Resources
~~~~~~~~~

* Coverages

  * Formats: a whole bunch

* Vector Data
* Processes

.. _rfc1_req_deploy:

Deployment
~~~~~~~~~~

* O3S Use Cases
* thinking further

Draft Architecture
------------------

* O3S draft ADD/SDD
* identified components
* complementary considerations

  * separation of distribution and instances

Dependencies
------------

* Django
* MapServer
* GDAL

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
  * processes used in the ingestion chain see :doc:`rfc4`
  
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

:Requirements: `O3S_QUA_004
                <https://o3s.eox.at/requirements/ticket/122>`_,
:Tickets: N/A
