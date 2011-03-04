.. RFC 2: Extension Mechanisms for EOxServer

.. _rfc_2:

RFC 2: Extension Mechanism for EOxServer
========================================

:Author: Stephan Krause
:Created: 2011-02-20
:Last Edit: 2011-03-03
:Status: IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc2

This RFC proposes an extension mechanism that allows to integrate
extension modules and plugins dynamically into the EOxServer
distribution and instances.

Introduction
------------

* motivation
* addressed problems
* proposed solution

Requirements
------------

:doc:`rfc1` proposes an extension mechanism for EOxServer. It shall
assure extensibility by additional modules and plugins and provide
functionality to enable dynamic binding to extending modules.

In the layered architecture of RFC 1 the :ref:`rfc1_core` shall be the
place where the central logic that enables the dynamic extension of
system functionality resides. The layers shall provide interface
definitions based on the extension model of the Core that can be
implemented by extending modules and plugins.

Now which extensions are needed and which requirements do they impose on
the extension mechansims? Digging deeper we have a look at the four
architectural layers of EOxServer and analyze the interfaces and
implementations needed by each of them.

The :ref:`rfc1_svc_lyr` defines a structured approach to OGC Web Service
(OWS) request handling that discerns different levels:

* services
* service versions
* service extensions
* service operations

For all of these levels interfaces are defined that are implemented by
extending modules for specific OWS and their different versions and
extensions.

The :ref:`rfc1_proc_lyr` defines interfaces for processes and processing
chains (see :doc:`rfc5`). Some of these are used internally and
integrated into the distribution, most will be provided by plugins.
While the process interface needs to be generic in order to make the
implementation of many different processes possible, it must be concise
enough to allow binding between processes in a processing chain. So,
this must be sustained by the extension mechanism as well.

The :ref:`rfc1_dint_lyr` shall provide an abstraction layer for
different data formats, metadata formats and data packaging formats.
This shall be achieved using common interfaces for coverage data, vector
data and metadata respectively.

Data and packaging formats are often not known by the system before
ingesting a dataset. Thus, some kind of autodetection of formats is
necessary. This is provided partly by the underlying
libraries such as `GDAL <http://www.gdal.org>`_, but shall also be
considered for the design of the extension mechanism: it must be
possible to dynamically bind to the right data, metadata and data
packaging format based on evaluations of the data. These tests should be
implemented by format extensions and supported by the extension 
mechansim.

The :ref:`rfc1_dacc_lyr` is built around the interface definitions of
backends and data sources stored by them. 

In addition to modularity and extensibility RFC 1 states that the
system shall be

  flexible in the sense that it must be possible to select different
  combinations of modules to deploy and activate
  
Modules can be combined to build a specific application. From a user
perspective it is essential to be able to activate and deactivate
services, service versions and service extensions globally 
and/or separately for each resource or process. The same applies for
other extensible parts of the system such as backends.

The O3S Use Case 2 for instance requires a server setup that consists of:

* local and WCS backends in the Data Access Layer
* a specific combination of coverage, vector data, metadata and
  packaging formats in the Data Integration Layer
* a feature detection process in the Processing Layer
* WPS and WFS implementations in the Service Layer

All other backends, services and processes shall be disabled.

Summarizing the requirements the extension mechanism shall support:

* extensibility by additional modules and plugins 
* dynamic binding
* interface definitions for extensions
* implementations that can be enabled or disabled

  * globally
  * per resource or per process

* modules that can be configured dynamically to build an application
* autodetection of data, metadata and data packaging formats

Extension Mechanism
-------------------

* interfaces and implementations
* registry
* dynamic binding
* hooks
* extension names
* registry keys, registry values
* conventions
* conflicts
* default implementations
* dependencies
* service extensions see :doc:`rfc3`
* processing chains see :doc:`rfc5`
* enabling and disabling using the admin

  * global settings
  * settings on a per-resource basis
  * configuration data model

* deployment of plugins and extensions

The basic questions for the design of the extension mechanism are:

* how to define extensible interfaces
* how to design implementations of these interfaces
* how to detect them
* how to bind to them


Interfaces and Implementations
------------------------------

* ExtensibleInterface base class

  * extending modules and plugins derive from the base class
  * class variables for hooks, ...

    * customizable
    * fixed

* abstract classes
* hooks
* extension names
* keys, values
* naming conventions
* settings for conflict resolution
* settings for enabling / disabling

::

    class ServiceInterface(ExtensibleInterface):
        NAME = "Abstract Service Interface"
        HOOK = "services.owscommon.ServiceInterface"
        ABSTRACT = True
        REGISTRY_KEYS = {
            "services.owscommon.service": {"mandatory": True}
        }
        
        # ...

:: 

    class WxSServiceImplementation(ServiceInterface):
        NAME = "WxS"
        ABSTRACT = False
        REGISTRY_VALUES = {"services.owscommon.service": "WXS"}
        
        # ...

::

    def bind(service_name):
        service = Registry.getImplementation(
            hook = "services.owscommon.ServiceInterface",
                "services.owscommon.service": service_name
            }
        )
        
        # ...

Registry and Dynamic Binding
----------------------------

* checks directories for classes derived from ExtensibleInterface base
  class
  
    * layer root directory
    * layer directories for implementations
    * plugins directory of distribution
    * plugins directory of instance

* registers implementations, i.e. non-abstract derived classes

    * only valid implementations, i.e.:

      * all mandatory key-value-pairs provided
      * valid values for all class variables

* enables search for implementations using:

  * the interface hook
  * the registry key-value-pairs stored with the request
  * a test() function that returns if the implementation is applicable,
    e.g. for data, metadata and packaging formats

* tries to resolve conflicts

  * based on subclass and superclass settings

Dependencies and Conflicts
--------------------------

* dependencies

  * service extensions may depend on the service implementation and
    other service extensions, see :doc:`rfc3`

* conflict:

  * more than one implementation for the same hook and
    key-value-combination
  * more than one implementation is applicable for testing
    implementations
  * default, recessive, dominant, levels
  * more than on service extension may be applicable see :doc:`rfc3`

* conflict resolution

Configuration Data Model and Admin Client Actions
-------------------------------------------------

* enabling and disabling using the admin

  * global settings
  * settings on a per-resource basis

Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
