.. RFC 2: Extension Mechanisms for EOxServer

.. _rfc_2:

RFC 2: Extension Mechanism for EOxServer
========================================

:Author: Stephan Krause
:Created: 2011-02-20
:Last Edit: 2011-03-02
:Status: IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc2

This RFC proposes an extension mechanism that allows to integrate
extension modules and plugins dynamically into EOxServer distributions
and instances.

Introduction
------------

* motivation
* addressed problems
* proposed solution

Requirements
------------

* Service Layer

  * services
  * service extensions
  * configurable if enabled/disabled

* Processing Layer

  * processes to be published using WPS
  * configurable if enabled/disabled
  * "pluggable" processing chains see :doc:`rfc5`

* Data Integration Layer

  * data formats
  * metadata formats
  * data packaging formats
  * format autodetection

* Data Access Layer

  * backends

* modules can be combined to build a specific application

  * e.g. O3S Use Case 2: WCS backend - coverage data, metadata,
    packaging formats - feature detection process - WPS, WFS

Extension Mechanism
-------------------

* registry
* interfaces and implementations
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

* deployment of plugins and extensions

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
