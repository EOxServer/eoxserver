.. Synchronization
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

.. _Synchronization:

Synchronization
===============

This section describes why and how to synchronize an EOxServer instance with
the file system.

What is synchronization?
------------------------

In the context of EOxServer, synchronization is the process of updating the
database models for container objects (such as RectifiedStitchedMosaics or
DatasetSeries) according to changes in the file system.

Automatic datasets are deleted from the database, when their data files cannot
be found in the file system. Similar, new datasets will be created when new
files matching the search pattern in the subscripted directories are found.

When datasets are added to or deleted from a container object, the metadata
(e.g the footprint of the features of interest or the time extent of the image)
of the container is also likely to be adjusted. 

Reasons for Synchronization
---------------------------

There are several occasions, where synchronization is necessary:

 * A file has been added to a folder associated with a container
 * A file from a folder associated with a container has been removed
 * EO Metadata has been changed
 * A regular check for database consistency

HowTo
-----

Synchronization can be triggered by a custom `Django admin command
<https://docs.djangoproject.com/en/dev/ref/django-admin/>`_, called
``eoxs_synchronize``.

To start the synchronization process, navigate to your instances directory and
type:
::

    python manage.py eoxs_synchronize <IDs>

whereas ``<IDs>`` are the coverage/EO ID of the containers that shall be
synchronized.

Alternatively, with the ``-a`` or ``--all`` option, all container objects in
the database will be synchronized. This option is useful for a dayly cron-job,
ensuring the databases consistency with the file system.
::

    python manage.py eoxs_synchronize --all

The synchronization process may take some time, especially when FTP/Rasdaman
storages are used and also depends on the number of synchronized objects.

