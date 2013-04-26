.. CentOSInstallation
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
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
    single: Recommendations for Operational Installation

.. _OperationalInstallation:

Recommendations for Operational Installation
============================================

This section provides a set of recommendations and a step-by-step guideline 
for installation and configuration of the EOxServer on an operational system. 
This guide goes beyond the basic installation presented in previous sections. 

Unless stated otherwise this guide considers installation on CentOS GNU/Linux
operating system although the guide is applicable for other distributions as well. 

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

.. seealso:: 

    * :ref:`Installation`
            generic installation procedure for GNU/Linux operating systems 
    * :ref:`CentOSInstallation`
            for specific installation on CentOS.
    * :ref:`InstanceCreation` 
            to configure a service instance after the EOxServer has been
            installed successfully.

.. _OperationalInstallation_user:


Introduction EOxServer   
----------------------

When installing and configuring the EOxServer a clear distinction should be made
between the common EOxServer installation (the installed code implementing 
the SW functionality) and the EOxServer service instances. An instance is 
a collection of data and configuration files that enables deployment of 
a specific service. A single server will typically
contain a single SW installation and one or more specific service instances. 

While the EOxServer installation is straightforward and typically does not
require much effort (see the :ref:`generic <Installation>` and
:ref:`CentOS<CentOSInstallation>` installation guides) the service
:ref:`configuration<InstanceCreation>` requires more attention of the 
administrator and a bit of planning as well. 

Closely related to the EOxServer are the (possibly large) served EO data.
It should be borne in mind, that the EOxServer as such is not data a management
system, i.e., it can register the stored data but itself does neither control
nor require any specific data storage locations. Where and how the data are 
stored is thus responsibility of the administrator. 

The EOxServer registers the EO data keeps only the essential meta-data (data
and full meta-data location, geographic extent, acquisition time, etc.)
in a database.

Directory Structure  
-------------------

First, the administrator has to decide where in which directory the instances 
should be located. Each of the EOxServer instances is represented by a dedicated
directory. 

For system wide installation we recommend to create a single specific directory 
to hold all instances in location compliant with the `filesystem hierarchy
standard
<http://www.pathname.com/fhs/pub/fhs-2.3.html#SRVDATAFORSERVICESPROVIDEDBYSYSTEM>`_::

    /srv/eoxserver

Optionally, for user defined instances a folder in the user's home directory is 
acceptable as well::

    ~/eoxserver

We **strongly discourage** to keep the instance configuration in system
locations not suited for this purpose such as ``/root`` or ``/tmp``!

A dedicated directory should also be considered for the served EO data, e.g.::

    /srv/eodata 

or::

    ~/eodata 


User Management
---------------

The EOxServer administrator has to deal with four different user management 
subsystems:  

    * system user (operating system),
    * database user (SQL server),
    * django user (DJango user management),
    * application user (e.g., Single Sign On authentication).

Each of them is described hereafter. 


Operating System Users 
~~~~~~~~~~~~~~~~~~~~~~

On a typical mutli-user operating system several users exist each of them owning
some files and each of them is given some right to access other files and run
executables.
In a typical EOxServer setup, the installed executables are owned by the *root* 
user and when executed they are granted the rights of the invoking process owner.
When executed as a WGSI application, the running EOxServer executables run with
the same ID as the web server (for Apache server this is typically *apache* or
*www-data* system user). This need to be considered when specifying right for
the files which are expected to be changed by a running application.  

The data database back-end has usually its own dedicated system user (for 
PostgreSQL this is typically *posgress*).

Coming back the EOxServer service instances' configuration we recommend 
both instance the data be owned one or
(preferably) two distinct system or ordinary users. These users can already
exist (e.g., the *apache* user) or new dedicated users can be created.


We **strongly discourage** to keep the EOxService service instances 
(i.e., configuration data) and the served EO data owned by the system
administrator (*root*). 

Database User  
~~~~~~~~~~~~~

DJango framework (the EOxSerevr is build upon) requires access to a Database
Management System (DBMS) which is typically protected by user-name/password 
based authentication. Specification of these DBMS credential is part of 
the service instance :ref:`configuration <InstanceCreation_DBSetup>`.

The sole purpose of the DBMS credentials is to access the database.

It should be mentioned the user-name/password is not the only possible way how
to secure the database access. The various authentication options for PosgreSQL
are covered, e.g., `here
<http://www.postgresql.org/docs/devel/static/auth-pg-hba-conf.html>`_.

DJango Sysadmin   
~~~~~~~~~~~~~~~

DJango framework (the EOxServer is build upon) provides own user management
subsystem. The EOxServer uses the DJango user management system for logging of
the system administrator to the low level :ref:`Admin Web GUI. <ops_admin>`.   
DJango user management is neither used to protect access to the provided 
Web Service interfaces nor to restrict access via the command line tools. 

Application User Management    
~~~~~~~~~~~~~~~~~~~~~~~~~~~

EOxServer is based on assumption that the authentication and authorisation of
an operational system would be performed by an external security system (such
as Shibboleth based :ref:`Single Sign On<Identity Management System>`
infrastructure). This access control would be transparent from the 
EOxServer's point of view. 

Is is beyond the scope of this document to explain how to configure the Single
Sign On (SSO) but principally the configuration does not differ from securing
plain apache web server.

It is worth to mention that in case of EOxServer the granularity of the SSO 
policy is the whole web service access point (i.e., one service instance). 
In order to setup different access policies for different subsets of the served
EO data multiple (independent) EOxServer instances must be setup. 

EOxServer Configuration Step-by-step 
------------------------------------

The guideline presented in this section assumes successful installation of the
EOxServer and of the essential dependencies performed either from the available 
RPM packages (see CentOS :ref:`CentOSInstallation_repos` and 
:ref:`CentOSInstallation_repos`) or via the Python Package Index 
(see :ref:`CentOSInstallation_pip`). 

In case of installation from RPM repositories it is necessary to install the
required repositories first::

    sudo rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
    sudo rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
    sudo rpm -Uvh http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm

and then install the EOxServer's package::

    sudo yum install EOxServer

Step 1 - Web Server Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The EOxServer is a DJango based web service application and as such it need as a
web server (the simple DJango provided server is not an option for an 
operational system). Any instance of the EOxServer is receives HTTP requests 
via the WSGI interface. 
The EOxServer is tested to work with the `Apache <http://www.apache.org/>`_ 
web server with the 
`WSGI <http://en.wikipedia.org/wiki/Web_Server_Gateway_Interface>`_ 
module enabled. The server can be installed as by:: 

    sudo yum install httpd mod_wsgi

The EOxServer itself is not equipped by any authentication or authorisation
mechanism. In order to secure the resources an external tool must be used to
control the access to the resources (e.g., Shibboleth Apache module).
as Shibboleth based :ref:`Single Sign On<Identity Management System>`

Step 2 - Database Backend  
~~~~~~~~~~~~~~~~~~~~~~~~~

The EOxServer requires Database Management System (DBMS) for storage of its
internal data. For an operational system local or remote installation of 
`PostgreSQL <http://www.postgresql.org/>`_
with `PostGIS <http://postgis.net/>`_ extension is recommended over the simple 
file-based SQLite backend. To install the DBMS run following command:: 

    sudo yum install postgresql postgresql-server postgis python-psycopg2

The PostgreSQL comes with reasonable default settings which are often sufficient.
For details on more advanced configuration (like changing the default database
location) see, e.g., PosgreSQL's
`wiki <http://wiki.postgresql.org/wiki/Main_Page>`_

On some Linux distribution like recent RHEL and its clones such as CentOS, 
the PostgreSQL database must be initialized manually by::

    sudo service postgresql initdb 

To start the service automatically at boot time run::

    sudo chkconfig postgresql on

You can check if the PostgreSQL database is running or not by::

    sudo service postgresql status 

If not start the PostgreSQL server::

    sudo service postgresql start

Once the PostgreSQL is running we have to setup a database template for the
required PostGIS extension::

    sudo -u postgres createdb template_postgis
    sudo -u postgres createlang plpgsql template_postgis
    PG_SHARE=/usr/share/pgsql
    sudo -u postgres psql -q -d template_postgis -f $PG_SHARE/contrib/postgis.sql
    sudo -u postgres psql -q -d template_postgis -f $PG_SHARE/contrib/spatial_ref_sys.sql

Please note that the ``PG_SHARE`` directory can vary for each Linux distribution
or custom PostgreSQL installations. For CentOS it has just happen to be
``/usr/share/pgsql`` the default location. The proper path can be found, e.g.,
by::

    locate contrib/postgis.sql

Step 3 - Creating Instance and Data Users and Directories 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create the users and directories for the EOxData instances and the served EO
Data run following command:: 

    sudo groupadd -r eoxserver
    sudo groupadd -r eodata  
    sudo useradd -r -m -g eoxserver -d /srv/eoxserver -c "EOxServer's administrator" eoxserver
    sudo useradd -r -m -g eodata -d /srv/eodata -c "EO data provider" eodata  

For meaning of the used options see documentation of  
`useradd <http://unixhelp.ed.ac.uk/CGI/man-cgi?useradd+8>`_ and 
`groupadd <http://unixhelp.ed.ac.uk/CGI/man-cgi?groupadd+8>`_ commands.

Step 4 - Instance Creation 
~~~~~~~~~~~~~~~~~~~~~~~~~~

Now is time to setup a sample instance of the EOxServer.  Create a new instance 
named ``instance00`` using the ``eoxserver-admin.py`` command:: 

    sudo -u eoxserver eoxserver-admin.py create_instance instance00 -d /srv/eoxserver

Now our first bare instance exists and needs to be configured. 

Step 5 - Database Setup
~~~~~~~~~~~~~~~~~~~~~~~

As the first to animate the instance is necessary to  setup a database.
Assuming the Postgress DBMS is up an running, we start by creating a 
database user (replace ``<db_username>`` by user-name of your own choice):: 

    sudo -u postgres createuser --no-createdb --no-superuser --no-createrole --encrypted --password <db_username>

The user's password is requested interactively. Once we have the database user 
we can create database for our instance:: 

    sudo -u postgres createdb --ownner <db_username> --template template_postgis --encoding UTF-8 eoxs_instance00

Where ``eoxs_instance00`` is the name of the new database. As there may be more
EOxServer instances, each of them having own database, it is a good practice 
to set a DB name containing the name of the instance. 

In addition the PostgreSQL access policy must be set to allow access to the
newly created DB. To get an access to the database, insert 
following lines  (replace ``<db_username>`` by your actual DB user-name)::

    local eoxs_instance00 <db_username> md5

to file :: 

    /var/lib/pgsql/data/pg_hba.conf

Note that this allows *local* DB access. 
When inserting the line make sure you put this line **before** the default 
access policy::

   local all all ident

In case of an SQL server running on a separate machine) see PosgreSQL 
`documentation <http://www.postgresql.org/docs/devel/static/auth-pg-hba-conf.html>`_. 

The location of the ``pg_hba.conf`` file varies from one system to another.
In case of trouble to locate this file try, e.g.::

    sudo locate pg_hba.conf

Once we created and configured the database we need to update the EOxServer
settings stored, in our case, in file::

    /srv/eoxserver/instance00/instance00/settings.py 

Make sure the database is configured in the ``settings.py`` as follows::

    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'eoxs_instance00',
            'USER': '<db_username>',
            'PASSWORD': '<bd_password>',
            'HOST': '', # keep empty for local DBMS
            'PORT': '', # keep empry for local DBMS 
        }
    }
As in our previous examples replace ``<db_username>`` and ``<bd_password>`` by
the proper database user's name and password.

Finally it is time to initialize the database of your first instance by running
following command:: 

    sudo -u eoxserver python /srv/eoxserver/instance00/manage.py syncdb

The command interactively asks for creation of the DJango system administrator.
It is safe to say no and create the administrator's account later by::

   sudo -u eoxserver python /srv/eoxserver/instance00/manage.py createsuperuser

The ``manage.py`` is the command-line proxy for management of the EOxServer. To
avoid repeated writing of this fairly long command make shorter alias such as::

    alias eoxsi00 ="sudo -u eoxserver python /srv/eoxserver/instance00/manage.py"
    eoxsi00 createsuperuser


Step 6 - Web Server Integration 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*TBD*

Step 7 - Start Operating the Instance 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now we have a running instance of the EOxServer. For different oprations such as
the data registration see :ref:`EOxServer Operators' Guide`.


