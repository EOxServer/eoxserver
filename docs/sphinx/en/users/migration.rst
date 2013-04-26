.. Migration
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Fabian Schindler <fabian.schindler@eox.at>
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
    single: EOxServer Migration
    single: Migration
    single: EOxServer Upgrade
    single: Upgrade

.. _Migration:

Migration
=========

.. contents:: Table of Contents
    :depth: 4
    :backlinks: top

Migrating or upgrading an existing EOxServer instance may require to perform 
several tasks depending on the version numbers. In general upgrading 
versions with changes in the third digit of the version number only e.g. 
from 0.2.3 to 0.2.4 doesn't need any special considerations. For all other 
upgrades please carefully read the relevant sections below.


Migration from 0.2 to 0.3
-------------------------

From version 0.2 to version 0.3 a lot of development effort has been put into
EOxServer. Many new features have been implemented and a couple of bugs are now
eradicated.

However, if you already have an instance running EOxServer 0.2, this requires a
couple of changes to that instance and enables you to configure some new
optional configurations aswell.


Disclaimer
~~~~~~~~~~

Before trying to upgrade EOxServer please make sure to backup your database. 
This step depends on the actual DBMS you are using for your instance.

.. note::

    If you do not have a lot of datasets registered, or can easily reproduce 
    the current status of your instance, a complete newly created instance 
    may be more failsafe than trying to migrate your instance.

.. warning::

    Because of changes in the database schema, the migration of referenceable
    datasets does **not** work. Please re-register them once the instance is
    migrated/re-created.


Preparatory steps
~~~~~~~~~~~~~~~~~

Before you upgrade your software, you will need to perform a database dump. The
dump is required to migrate your registered objects to the new database. It is
performed with the following call::

    python manage.py dumpdata core backends coverages --indent=4 > dump.json

Unfortunately in some versions ``spatialite`` produces some output aswell, which
has to be removed from the top of the created ``dump.json`` file.


Software upgrade
~~~~~~~~~~~~~~~~

Now you are ready to actually perform the software upgrade.


Django & GDAL
^^^^^^^^^^^^^

The most notable changes concern our technology base: Django & GDAL. EOxServer
now relies on features of Django 1.4, so if you still have Django 1.3 or lower
installed, please upgrade to (at least) that version. This step, however,
depends on how you installed Django in the first place. With ``pip`` it should
be easy as pie/py::

    pip install Django --upgrade

If EOxServer is installed via pip, the upgrade of Django should be done
automagically.

Similar to Django, EOxServer now requires at least version 1.7 of the GDAL
library respectively its python bindings. GDAL is not explicitly stated in the
EOxServer dependencies to allow custom builds and OS specific installations. So
you are required to install the minimum required version on your own, via pip,
yum, apt, msi or whatever mechanism you prefer.

Please refer to the :ref:`table_eoxserver_dependencies` table for details on 
dependencies.

EOxServer
^^^^^^^^^

The upgrade of EOxServer is quite similar to :ref:`installing_eoxserver`. For
``pip`` you will need the ``-U`` (``--upgrade``) option:
::

    pip install -U EOxServer==0.3

or

    pip install -U "svn+http://eoxserver.org/svn/branches/0.3"


Instance migration
~~~~~~~~~~~~~~~~~~

Now that you have installed your software, there is a small step to perform 
which requires manual handling to upgrade your instance to the new version of
EOxServer.

Please open the ``conf/eoxserver.conf`` file within your instance directory and
locate the ``modules`` setting of the ``[core.registry]`` setting. The list
entry ``eoxserver.resources.coverages.covmgrs`` must be corrected to
``eoxserver.resources.coverages.managers``.

Now it is time to re-create your database which is done in three steps: deletion
of the old database, creation of a new one, and a synchronization. The deletion
and creation of the database depend on the database backend used. For SQLite,
for example, only the database file needs to be deleted.

The initialization of the database is done via::

    python manage.py syncdb

The old contents of the database can be restored via::

    python manage.py loaddata dump.json


New configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~

Since version 0.2 a couple of new configuration options are available, most
notably for defining output :ref:`formats <FormatsConfiguration>` and
:ref:`CRSs <CRSConfiguration>`. Please have a look at the relevant sections to
see how both are set up.

With Django 1.4, EOxServer allows a much more fine-grained logging mechanism
defined in ``settings.py``. Details can be obtained from the `Django
documentation
<https://docs.djangoproject.com/en/dev/topics/logging/#configuring-logging>`_.
The following is an example of how the logging is set up by default in new
EOxServer instances using version 0.3::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'simple': {
                'format': '%(levelname)s: %(message)s'
            },
            'verbose': {
                'format': '[%(asctime)s][%(module)s] %(levelname)s: %(message)s'
            }
        },
        'handlers': {
            'eoxserver_file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': join(PROJECT_DIR, 'logs', 'eoxserver.log'),
                'formatter': 'verbose',
                'filters': [],
            }
        },
        'loggers': {
            'eoxserver': {
                'handlers': ['eoxserver_file'],
                'level': 'DEBUG' if DEBUG else 'INFO',
                'propagate': False,
            },
        }
    }

Another important feature that was introduced in Django 1.4 is the implicit
support of time-zones. This can be activated in ``settings.py``::

    USE_TZ = True

For a complete list of changes in Django see the official documentation
(`1.4 <https://docs.djangoproject.com/en/dev/releases/1.4/>`_ and
`1.5 <https://docs.djangoproject.com/en/dev/releases/1.5/>`_).
