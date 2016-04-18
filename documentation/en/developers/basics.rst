.. Basics
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
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

.. _Basics:

Basics
======

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

The basic design of EOxServer has been proposed in :doc:`/en/rfc/rfc1` and
:doc:`/en/rfc/rfc2`. Both are worth reading, although some of the concepts
mentioned there have not (yet) been fully implemented.

This is a short description of the basic elements of the EOxServer software
architecture.

Architectural Layout
--------------------

EOxServer is Python software that builds on a handful of external packages.
Most of the description in the following sections is related to the structure
of the Python code, but in this section we present the building blocks used
for EOxServer.

For further information on the dependencies please refer to the
:doc:`/en/users/install` document in the :doc:`/en/users/index`.

Django
~~~~~~

EOxServer is designed as a Django app. It reuses the object-relational mapping
Django provides as an abstraction layer for database access. Therefore, it is
not bound to a specific database application, but can be run with different
backends.

Database
~~~~~~~~

Metadata and part of the EOxServer configuration is stored in a database. A
handful of geospatially enabled database systems is supported, though we
recommend either PostGIS or SpatiaLite.

MapServer
~~~~~~~~~

One of the most important components is `MapServer <http://www.mapserver.org>`_
which EOxServer uses through its Python bindings to handle certain OGC Web
Service requests.

GDAL/OGR
~~~~~~~~

In some cases EOxServer uses the `GDAL/OGR <http://www.gdal.org>`_ library for
access to geospatial data directly (rather than through MapServer).

Software Architecture
---------------------

The basic software architecture of EOxServer's Python code is layed out in
:doc:`/en/rfc/rfc2`. The main intention of the design is to keep EOxServer
modular and extensible.

In order to reach that goal, EOxServer relies on a central registry of
classes that implement certain behaviour. The registry allows to find
appropriate implementations (e.g. for certain OGC Web Service operations)
according to a set of parameters.

* Registry
* Factories
* Wrappers
* Resources
* Records


