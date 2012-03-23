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

The *autotest* package is a minimal EOxServer instance to run tests against
the basic functionality of EOxServer. It provides test data and expected
results for various components.


Installation
------------

For the *autotest* instance to work, a new EOxServer instance has to be created
with the ``eoxserver-admin.py`` script which creates a basic directory and file
structure for a new instance:
::

    eoxserver-admin.py create_instance --id autotest

Use the ``--init_spatialite`` to initialize a SQLite database needed for 
:ref:`running <Running the autotest instance>` the *autotest* instance:
::

    eoxserver-admin.py create_instance --id autotest --init_spatialite

Now it can be filled with its content, downloaded from the `EOxServer project
download page <http://http://eoxserver.org/wiki/Download>`_ and unpacked into
the previously created instance (say yes if asked to overwrite):
::

    wget http://eoxserver.org/export/head/downloads/EOxServer_autotest-0.2-beta1.tar.gz
    tar xvfz EOxServer_autotest-0.2-beta1.tar.gz
    cp -Rf EOxServer_autotest-0.2-beta1/* autotest

Currently there are two configuration directives which influence the testing
procedure and allow to skip certain test cases know to be problematic on some
systems. Please refer to the :ref:`corresponding section in the configuration
options documentation <config-testing>`.

The autotest instance is now installed and is ready for some testing!


Running tests
-------------

Most of the tests in EOxServer use the `Django test framework
<https://docs.djangoproject.com/en/1.3/topics/testing/>`_, which itself is
built upon `Python's unittest framework
<http://docs.python.org/library/unittest.html>`_.

To run tests against a component of EOxServer simply run:
::

    cd autotest
    python manage.py test <component>

where `<component>` is one of `services`, `core`, `backends`, `coverages` and 
`processes`. If all components shall be tested in one pass, just the 
`<component>` parameter has to be omitted. Detailed information about running 
Django tests can be found in the `according chapter of the Django documentation 
<https://docs.djangoproject.com/en/1.3/topics/testing/#running-tests>`_.

Due to some behaviour of underlying software such as GEOSS the tests for the 
`services` component need to be split up. The following splitting is known to 
work:
::

    python manage.py test services.WCS1
    python manage.py test services.WCS20GetCap
    python manage.py test services.WCSVersion
    python manage.py test services.WCS20DescribeCoverage
    python manage.py test services.WCS20DescribeEOCoverageSet
    python manage.py test services.WCS20GetCoverage
    python manage.py test services.WCS20Post
    python manage.py test services.WMS
    python manage.py test services.Sec


Running single tests
~~~~~~~~~~~~~~~~~~~~

Single tests or groups of tests can be run by appending the test name or 
beginning of the test name to the component:
::

    python manage.py test services.WCS20GetCapabilities


XML Validation
~~~~~~~~~~~~~~

In order to speed up the tests and also to pass certain tests it is highly 
recommended to make usage of locally stored schemas via XML Catalog:
::

    wget http://eoxserver.org/export/head/downloads/EOxServer_schemas-0.2-beta1.tar.gz
    tar xvfz EOxServer_schemas-0.2-beta1.tar.gz
    export XML_CATALOG_FILES=`pwd`"/EOxServer-0.2-beta1/schemas/catalog.xml"

This allows the underlying libxml2 to vastly improve the performance of parsing
schemas and the validation of XML trees against them. Also, several schemas
contain small errors which makes it impossible to correctly use them in a real
validation scenario. The self contained schemas package provides only
useable schemas.


.. _Running the autotest instance:

Running the *autotest* instance
-------------------------------

First the configuration of the instance has to be finalized. After the 
successful :ref:`Database Setup` it needs to be initialized:
::

    cd autotest
    python manage.py syncdb

Either a Django superuser needs to be defined while running the command or the 
``auth_data.json`` loaded as described in the next section.

Loading test data 
~~~~~~~~~~~~~~~~~

Test data is provided as fixtures plus image files. To register all available 
test data simply run:
::

    cd autotest
    python manage.py loaddata auth_data.json initial_rangetypes.json \
                              testing_base.json testing_coverages.json \
                              testing_asar_base.json testing_asar.json 

The following fixtures are provided:

* initial_data.json - Base data to enable components. Loaded with syncdb.
* auth_data.json - An administration account.
* initial_rangetypes.json - Range types for RGB and gray-scale coverages.
* testing_base.json - Range type for the 15 band uint16 test data.
* testing_coverages.json - Metadata for the MERIS test data.
* testing_asar_base.json - Range type for the ASAR test data.
* testing_asar.json - Metadata for the ASAR test data.
* testing_rasdaman_coverages.json - Use this fixtures in addition when
  rasdaman is installed and configured.
* testing_backends.json - This fixtures are used for testing the backend
  layer only and shouldn't be loaded in the test instance.


Running the development web server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django provides a `lightweight development web server <https://docs.djangoproje
ct.com/en/dev/ref/django-admin/#runserver-port-or-address-port>`_ which can be 
used to run the *autotest* instance:
::

    cd autotest
    python manage.py runserver

The *autotest* instance is now available via a standard web browser at 
http://localhost:8000/

The :ref:`ops_admin` is available at http://localhost:8000/admin or via the 
*Admin Client* link from the start page. Note that if the ``auth_data.json`` 
has been loaded there is a superuser login available with username and password 
"login".

Sample service requests are described in the :ref:`Demonstration` section.


Selenium
--------

The `Selenium testing framework <http://seleniumhq.org/>`_
is a powerful tool to create and run GUI test cases for any browser and HTML
based application. It uses low-level mechanisms, such as simulating simple user
input, to automate the browser and to test the application.

Currently the only browser supported is `Firefox <http://www.mozilla.org/en-US/
firefox/new/>`_ using the `Selenium IDE <http://seleniumhq.org/projects/ide/>`_
plugin. It is basically a tool to record and play test cases and it also
supports exporting the test scripts to several scripting languages as Java,
Ruby, Python and *Selenese*, a basic HTML encoding.

.. _fig_selenium-ide:
.. figure:: images/selenium-ide.png
   :align: center

Before the test cases can be run, ensure that the databases `backends` and
`coverages` are empty and the EOxServer is run by either its developement
server or within a webserver environment. To clear the databases in question
type:
::

    python manage.py reset coverages backends

and confirm the deletion. But be aware that this deletes all data previously
entered in the database.

The *autotest* instance provides two test suites, one for the :ref:`Admin
interface <ops_admin>` and one for the :ref:`Webclient interface
<webclient>`. To open a testsuite with Selenium IDE navigate to
`File->Open Test Suite...` and open the suite of your choice.

To start the test run click on the `Play entire test suite` button.
Alternatively, you can choose a single test case by double clicking it and then
press the `Play current test case button`. Note: especially in the admin test
suite several test cases have dependencies on other test cases to be run first,
so many test cases will fail when its dependencies are not fullfilled. The best
option is to play the entire test suite as a whole and view the results
afterwards.

Note that the test speed should be decreased in order to allow enough time to 
fill the pages and thus pass the tests.

Don't forget to adjust the base URL when the *autotest* instance is not run 
locally.

Note that when testing the admin interface, before the tests can be rerun,
the database has to be emptied, as explained in the example above.
