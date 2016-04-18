.. Data Schema
  #-----------------------------------------------------------------------------
  # $Id: data_model.rst 1533 2012-03-15 13:00:53Z martin.paces $
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Martin Paces <martin.paces@eox.at>
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

Data Migrations
===============

Over the time, the data models and thus the underlying database schema is 
changing to adapt new features or resolve bugs. Unfortunately Django cannot 
automatically detect and resolve those changes and upgrade existing instances 
for us.

To solve this problem, EOxServer uses `South <http://south.aeracode.org/>`_ for 
schema and data migration management.


What are migrations?
--------------------

.. pull-quote::

    For the uninitiated, migrations (also known as ‘schema evolution’ or
    ‘mutations’) are a way of changing your database schema from one version 
    into another. Django by itself can only do this by adding new models, but 
    nearly all projects will find themselves changing other aspects of models - 
    be it adding a new field to a model, or changing a database column to have 
    null=True.

    -- from the `South documentation 
    <http://south.readthedocs.org/en/latest/whataremigrations.html>`_


Setup
-----

`South` needs to be initialized in every instance that wants to make use of the 
migration features. 

Setting up `South` is quite easy, as all you need to do is install `South` (most
easily via ``pip`` or ``easy_install``), add it to the ``INSTALLED_APPS`` 
setting in ``settings.py`` and run ``python manage.py syncdb``:
::

    INSTALLED_APPS = (
        ...
        'eoxserver.testing',
        'eoxserver.webclient',
        'south'
    )

A complete guide on all installation and configuration options can be found 
`here <http://south.readthedocs.org/en/latest/installation.html>`__.


Creating Migrations
-------------------

To benefit from `South` it is important that `every` change in the data models
concerning the actual database structure is tracked by a migration definition. 
Fortunately, for most of the small changes these can be created automatically by
using `Souths` command ``python manage.py schemamigration`` and passing the 
app names which have changes in their models.

A very good tutorial for `South` can be found `here 
<http://south.readthedocs.org/en/latest/tutorial/part1.html>`__.


Performing a Migration
----------------------

To use `South` for data migrations only one command needs to be executed: 
``python manage.py migrate``. This applies all necessary database schema changes
to your database and converts all included data from the original schema to the
new one. This command effectively replaces ``syncdb`` (apart from the initial 
call to setup `South`).
