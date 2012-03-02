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

The 'autotest' instance
=======================

The `autotest` package is a minimal EOxServer instance to run tests against
the basic functionality of EOxServer. It provides test data and expected
results for various components.


Installation
------------

For the `autotest` instance to work, a new EOxServer instance has to be created
with the `eoxserver-admin.py` script which creates a basic directory and file
structure for a new instance:
::

    eoxserver-admin.py create_instance --id autotest

Now it can be filled with its content, downloaded from the `EOxServer project
download page <http://http://eoxserver.org/wiki/Download>`_ and unpacked into
the previously created instance:
::

    wget http://eoxserver.org/export/head/downloads/EOxServer_autotest-0.2-alpha1.tar.gz
    tar xvfz EOxServer_autotest-0.2-alpha1.tar.gz
    cp -Rf EOxServer_autotest-0.2-alpha1/* autotest

The autotest instance is now installed and is ready for some testing!

Running tests
-------------

Most of the tests in EOxServer use the `Django test framework
<https://docs.djangoproject.com/en/1.3/topics/testing/>`_, which itself is
built upon `Python's unittest framework
<http://docs.python.org/library/unittest.html>`_.

To run tests against a component of EOxServer you have to type:
::

    cd autotest
    python manage.py test <component>

where `<component>` is one of `core`, `backends`, `coverages` and `services`.
If all components shall be tested in one pass, just the `<component>` parameter
has to be omitted. Detailed information about running Django tests can be found
in the `according chapter of the Django documentation
<https://docs.djangoproject.com/en/1.3/topics/testing/#running-tests>`_.






