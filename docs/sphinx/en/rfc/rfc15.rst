.. RFC 15: Access Control Support
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Arndt Bonitz <arndt.bonitz@ait.ac.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 AIT Austrian Institute of Technology GmbH
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

.. _rfc_15:

RFC 15: Access Control Support
==============================

:Author:     Arndt Bonitz
:Created:    2011-11-14
:Last Edit:  2011-02-09
:Status:     ACCEPTED 
:Discussion: http://eoxserver.org/wiki/DiscussionRfc15  

Overview
--------

This RFC describes access control support for the EOxServer. The following 
figure gives an overview of the proposed access control implementation and its 
different components:  

.. figure:: resources/rfc15/IDM_HTTP_Components.png
   :align: center
   
   *EOxServer Access Control Implementation*

The access control implementation relies on the `Shibboleth framework 
<http://shibboleth.internet2.edu/>`_ and parts of the `CHARON framework 
<http://www.enviromatics.net/charon/index.html>`_, namely the CHARON 
Authorisation Service. The components are all released as Open Source. 
Shibboleth is used for the authentication of users; the CHARON Authentication 
Service is responsible for making authorisation decisions if a certain request 
may be performed.

Authentication
-------------- 

Authentication is not handled directly by the EOxServer components, but uses 
the Shibboleth federated identity management system. In order to do this, two 
requirements must be met:

* A Shibboleth Identity Provider (IdP) must be available for authentication
* A Shibboleth Service Provider must be installed and configured in an `Apache 
  HTTP Server <http://httpd.apache.org/>`_ to protect the EOxServer resource.

A user has to authenticate at an IdP in order to perform requests to an 
EOxServer with access control enabled. The IdP issues a SAML token which will 
be validated by the SP.

Is the user valid, the SP adds the user attributes by the IdP to the HTTP 
Header of the original service requests and conveys it to the protected 
EOxServer instance. The whole process ensures, that only authenticated users 
can access the EOxServer.

Authorisation
------------- 

As noted in the previous section, the Shibboleth system provides the underlying 
service and all asserted user attributes. These attributes can be used to make 
an decision if a certain user is allowed to perform an operation on the 
EOxServer. The authorisation decision is not made directly in the EOxServer, 
but relies on the CHARON Authorisation Service. 

The Authorisation Service is responsible for the authorisation of service 
requests. It makes use of `XACML 
<http://www.oasis-open.org/committees/xacml/#XACML20>`_, a XML based language 
for access policies. The Authorisation Service is part of the 
`CHAORN <http://www.enviromatics.net/charon/index.html>`_ project. The 
EOxServer security components are only responsible for performing an 
authorisation decision request on the Authorisation Server and enforcing the 
authorisation decision. 

EOxServer Security Component
-----------------------------

The EOxServer security component is located in the package 
``eoxserver.services.auth.base`` in the EOxServer source code directory. The 
implementation of the ``PolicyDecisionPointInterface`` for the proposed setup 
is included in ``eoxserver.services.auth.charonpdp.py``, which is a wrapper for 
the CHARON Authorisation Service client. Every request for authorisation is 
encoded into a XACML Authorization Query and sent to the Authorisation Service. 
The decision (permit, deny) of the service is then enforced by the EOxServer.

A first implementation can be found in this `EOxServer sandbox 
<http://eoxserver.org/browser/sandbox/sandbox_security>`_ and there's also an 
`e-mail discussion <http://eoxserver.org/pipermail/dev/2011-October/000295.html>`_ 
about this in the dev mailing list archives.

Voting History
--------------

:Motion: Adopted on  2011-02-09 with +1 from Arndt Bonitz, Fabian Schindler, 
         Stephan Meißl and +0 from Milan Novacek, Martin Paces

Traceability
------------

:Requirements: N/A
:Tickets: N/A
