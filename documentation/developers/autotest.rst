.. Autotest
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
    single: Autotest

.. _Autotest:


The *autotest* instance
=======================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

The *autotest* instance is a preconfigured EOxServer instance used for 
integration testing. It provides test data and accompanying fixtures, 
integration test procedures and expected results for test comparison.

Technically it is a whole EOxServer instance with an additional Django app that
provides the test code. 

The instance is preconfigured, and fixtures can be 
loaded 


Installation
------------

To use the autotest instance, make sure that EOxServer was installed. You can 
obtain it via git:
::

    git clone git@github.com:EOxServer/autotest.git
    cd autotest

or from the projects release page:

    wget https://github.com/EOxServer/autotest/archive/release-<version>.tar.gz
    tar -xzvf release-<version>.tar.gz
    cd autotest

If you just want to run the tests with the default settings you should be fine 
now and :ref:`can start testing <run_tests>`. If you want to run the instance, 
you have create the database first:
::

    python manage.py syncdb

.. note::

    You can run the ``syncdb`` command with the ``--no-input`` option and run 
    ``python manage.py loaddata auth_data.json`` to load the default admin 
    fixtures. This adds an administrator account for the admin app. The 
    username and password is both ``admin``. This account is, of course, 
    **not** recommended for productive use.


Fixtures
--------

In order to load the actual data fixtures, run the following commands:

For MERIS UInt16 images:
::

    python manage.py loaddata meris_range_type.json meris_coverages_uint16.json

For MERIS RGB images:
::

    python manage.py loaddata range_types.json meris_coverages_rgb.json

For referenceable ASAR images:
::

    python manage.py loaddata asar_range_type.json asar_coverages.json


To load all available fixtures type:
::

    python manage.py loaddata autotest/data/fixtures/*.json


Deployment
----------

The autotest instance can be deployed :ref:`like any other EOxServer instance 
<EOxServer Deployment>`. The fastest way to actually access the data just run:
::

    python manage.py runserver 0.0.0.0:8000


.. _run_tests:

Run tests
---------

Running tests does not require any deployment or even a database 
synchronization. To run all autotest testcases just call:
::

    python manage.py test autotest_services -v2

If you only want to run a specific test case or only a specific test method run
this:
::

    python manage.py test autotest_services.WCS20GetCapabilitiesValidTestCase.testValid


Testing Configuration
~~~~~~~~~~~~~~~~~~~~~

Our basic environment to test EOxServer on is a CentOS 6.5 operating system. On
other systems some tests might produce slightly different results, which is due
to slight variations of dependency software or 64 to 32 bit architecture 
differences. For this reason, the following setting can be adjusted to skip 
binary image comparisons:
::

    [testing]
    binary_raster_comparison_enabled=false


XML Schemas
~~~~~~~~~~~

Many tests of the autotest suite perform XML Schema validation. By default, 
the schemas will be fetched dynamically, but this really slows down the the 
tests. Because of this, we prepared a schemas repository that can be downloaded
and used instead.
::

    wget https://github.com/EOxServer/schemas/archive/<version>.tar.gz
    tar -xzvf <version>.tar.gz 
    export XML_CATALOG_FILES=`pwd`"/schemas-<version>/catalog.xml"

