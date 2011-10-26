.. _soap proxy:

SOAP Proxy
==========

SOAP Access to WCS
------------------

SOAP access to services provided by EOxServer is possible if the functionality
is installed by the service provider. The protocol is SOAP 1.2 over HTTP.

EOxServer responds to the following WCS-EO requests via its SOAP service interface:

* DescribeCoverage
* DescribeEOCoverageSet
* GetCapabilities
* GetCoverage

To access the EOxServer by means of SOAP requests, you need to obtain the
access ULR from the service provider.
For machine readable configuration the SOAP service exposes the WSDL
configuration file: given a service address of 'http://example.org/eo_wcs' the
corresponding WSDL file may be downloaded at the URL
'http://example.org/eo_wcs?wsdl'.

Installation
------------


A quick-intall quide is provided below.  For a full installation guide see the
INSTALL file in the source tree.

Quick installation guide
~~~~~~~~~~~~~~~~~~~~~~~~

0. Prerequisites:
.................
The following is required before you can proceed with installing soap_proxy:

* ``mapserver`` installed & configured.
* Apache ``httpd2`` server installed and running


1. Install and configure axis2/c.
.................................
Download from http://ws.apache.org/axis2/c/download.cgi

Make a directory for the code::

    cd someplace
    mkdir axis2c
    setenv AXIS2C_HOME /path/to/someplace/axis2c

Follow the instructions in 'doc' to compile, and use something like the
following configure line to get ``mod_axis2`` configured for compiling at the same
time::

   ./configure --with-apache2="/usr/include/apache2" \
     --with-apr="/usr/include/apr-1" --prefix=${AXIS2C_HOME}

Execute the standard sequence::

   make
   make install

Copy ``lib/libmod_axis2.so.0.6.0``  to ``<apache2 modules directory>``  as
``mod_axis2.so``. 

Edit the file ``${AXIS2C_HOME}/axis2.xml`` and ensure that the parameter
enableMTOM has the value ``true``.

Check that the following directory exits, if not create it:
   ``${AXIS2C_HOME}/services``


2. Deploy axis2 via your webserver
..................................

Configure ``mod_axis2`` in the apache server config file. On Suse Linux one might
edit the file ``/etc/apache2/default-server.conf``.

Set up a proxy::

  <IfModule mod_proxy.c>
    ProxyRequests Off
    ProxyPass         /sp_wcs   http://127.0.0.1/o3s_axis/services/soapProxy
    ProxyPassReverse  /sp_wcs   http://127.0.0.1/o3s_axis/services/soapProxy
    ...
    <Proxy *>
      Order deny,allow
      Deny from all
      ...
    </Proxy>
  </IfModule>

and deploy axis2::

    LoadModule axis2_module  /usr/lib64/apache2/mod_axis2.so
    Axis2RepoPath /path/to/AXIS2C_HOME
    Axis2LogFile /tmp/ax2logs
    Axis2MaxLogFileSize 204800
    Axis2LogLevel info
    <Location /o3s_axis>
        SetHandler axis2_module
    </Location>


3. Verify the deployment of axis2
.................................

Resart the webserver (``httpd2``) and open the following page::

 http://127.0.0.1/o3s_axis/services

You should get a page that displays the text "Deployed Services" and is otherwise blank.


4. Configure and Compile Soap Proxy.
....................................

Change your working directory to the service directory in the soap_proxy source
code::

 cd <...>/soap_proxy/service

In ``soapProxy.wsdl`` set ``<soap:address location=.../>``.  Copy
TEMLATE_services.xml to ``services.xml``.
In ``services.xml`` set ``BackendURL`` to the address of eoxserver.

Now change to the src directory::

 cd src

In your environment or in the ``Makefile`` set ``AXIS2C_HOME`` appropriately, and
execute::

 make inst

Restart you httpd server and check that http://127.0.0.1/o3s_axis/services
shows the soapProxy service offering the four EO-WCS operations.

