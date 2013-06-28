.. soap proxy
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Milan Novacek <milan.novacek@siemens.com>
  #
  #-----------------------------------------------------------------------------
  # Copyright (c) 2011 ANF DATA Spol. s r.o.
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

.. _soap proxy developer:

SOAP Proxy 
==========

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

Architecture
------------

Soap_proxy is an adapter proxy which accepts POST request in XML  ecoded in SOAP
1.2 messages, and passes these on to EOxServer.  The proxy may also be
configured to pass the messages as POST requests to a suitable mapserver
executable instead of an EOxServer, for example for testing purposes.

Supported Interfaces
~~~~~~~~~~~~~~~~~~~~

Soap_proxy uses SOAP 1.2 over HTTP.

EOxServer responds to the following WCS-EO requests through SOAP service interface:

* DescribeCoverage
* DescribeEOCoverageSet
* GetCapabilities
* GetCoverage


Overview
~~~~~~~~
Soap_proxy  uses the axis2/C framework. An important feature of axis2/C is that it correctly handles SOAP 1.2 MTOM
Attachments.

The overall deployment context is shown in the figure below.
Soap_proxy is implemented as an axis2/c service, running
within the apache2 httpd server as a mod_axis2 module.

.. figure:: images/soap_proxy_overview.png
   :align: center

The next figure shows a sequence diagram for a typical request-response
message exchange from a client through the soap_proxy to an instance of
EOxServer.

.. figure:: images/soap_proxy_seq.png
   :align: center

Implementation
--------------

The implementation is provided in the src directory.
The file sp_svc.c is the entry point where the Axis2/c framework calls the
soap_proxy implentation code via rpSvc_invoke(), which calls rp_dispatch_op()
to do most of the work.

