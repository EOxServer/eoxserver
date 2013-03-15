.. Upgrade
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Meissl <stephan.meissl@eox.at>
  #                  Fabian Schindler <fabian.schindler@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2013 EOX IT Services GmbH
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
    single: EOxServer Upgrade
    single: Upgrade

.. _Upgrade:

Upgrade
=======

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

Upgrading an existing EOxServer instance may require to perform several 
tasks depending on the version numbers. In general upgrading versions with 
changes in the third digit of the version number only e.g. from 0.2.3 to 
0.2.4 doesn't need any special considerations. For all other upgrades please 
carefully read the relevant sections below.


0.2 to 0.3
----------

TODO:

* Changes in database models: How to migrate existing database? 
* New/altered config parameters e.g. foramts.conf
* New/altered settings in settings.py e.g. logging. Check  Django 1.4 release notes!
* Dropped support for Django 1.3 and GDAL 1.6
