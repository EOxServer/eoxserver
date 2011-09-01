.. _rfc_12:

RFC 12: Backends for the Data Access Layer
==========================================

:Author: Stephan Krause
:Created: 2011-08-31
:Last Edit: $Date$
:Status: IN PREPARATION
:Discussion: ...

This RFC proposes the implementation of different backends that provide common
interfaces for data stored in different ways. It describes the first version
of the Data Access Layer implementation as well as changes to the Data
Integration Layer that are caused by the changes to the data model.

Introduction
------------

:doc:`rfc1` introduced the Data Access Layer as an abstraction layer for
access to different kinds of data storages. These are most notably:

* data stored on the local file system
* data stored on a remote file system that can be accessed using FTP
* data stored in a rasdaman database

The term *backend* has been coined for the part of the software implementing
data access to different storages.

This RFC discusses an architecture for these backends which is based on the
extension mechanisms discussed in :doc:`rfc2`. After the :ref:`rfc12_reqs`
section the architecture of the Data Access Layer is presented. It is structured
into a section describing the :ref:`rfc12_dal_model` which consists basically
of :ref:`rfc12_dal_storages` and :ref:`rfc12_dal_locations`.

Furthermore, the necessary changes to the Data Integration Layer are explained.
On the one hand these affect the :ref:`Data Model <rfc12_dil_model>` which is
altered considerably. On the other hand new structures
(:ref:`rfc12_dil_data_sources` and :ref:`rfc12_dil_data_packages`) that
provide more flexible solutions for data handling by the Data Integration Layer
and the layers that build on it.

.. _rfc12_reqs:

Requirements
------------

...

.. _rfc12_dal_model:

Data Access Layer Data Model
----------------------------



.. _rfc12_dal_storages:

Storages
--------

.. _rfc12_dal_locations:

Locations
---------

.. _rfc12_dil_model:

Changes to Data Integration Layer Data Model
--------------------------------------------

.. _rfc12_dil_data_sources:

Data Sources
------------

.. _rfc12_dil_data_packages:

Data Packages
-------------

Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
