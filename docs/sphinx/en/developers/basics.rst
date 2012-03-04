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

As described thoroughly in RFC 1 and RFC 2, EOxServer separates between
interface and implementation


Models
------

Models are the primary source for the application data. They are an abstraction
for commonly relational database tables (`Object-Relational mapping
<http://en.wikipedia.org/wiki/Object-relational_mapping>`_).

Each model contains a certain amount of fields, storing the necessary
information or describing relations to other models.

Models provide means to create, alter, delete and search for objects of its
type.

However, working with EOxServer and its internal data structures it is *not*
encouraged to work with its models directly, but with higher layers such as
their wrappers and managers. # TODO: references


Wrappers
--------

To ease the use of database models, wrappers provide the functionality to
obtain required information from the models and do specific tasks. Wrappers are
usually afiliated with one model, but in some occasions provide an abstraction
for multiple models.

In EOxServer you obtain a wrapper by using factories or the registry.

Each wrapper type must implement the according interface.


Factories
---------

Factories are objects to create instances of specific types depending on the
given parameters. The parameters may be the type ID or object ID of the object
to be obtained, but can also include filter expressions, to exactly specify
the desired object.

Factories themselves can be obtained through the registry.

Managers
--------

Managers provide high level management utilities for creating, updateing,
synchronizing and deleting database objects. Managers are the preferred way to
manipulate data within EOxServer.

Filters
-------

Filter Expressions
------------------


The Registry
------------






