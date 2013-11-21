.. RFC 10: SOAP Proxy
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

.. _rfc_10:

RFC 10: SOAP Proxy
==================

:Author:     Milan Novacek
:Created:    2011-05-18
:Last Edit:  2011-05-30
:Status:     ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc10

Introduction
------------

This RFC proposes the design and implementation of the module *soap_proxy*.
Initially *soap_proxy* is for use with WCS services. 
The intent of *soap_proxy* is to provide a soap processing front end for
those WCS services which do not natively accept soap messages.
*Soap_proxy* extracts the xml of a request from an incoming SOAP message
and invokes mapserver or eoxserver in POST mode with the extracted xml.
It then accepts the response from mapserver or eoxserver and repackages
it in a SOAP reply.


Description
-----------

Soap-proxy should implement OGC 09-149 *Web Coverage Service 2.0 
Interface Standard - XML/SOAP Protocol Binding Extension*. See RFC-9
for a proposal to address certain problems with the current revision
of this standard (which is OGC 09-149r1).

Initially it is planned that *soap_proxy* supports WCS 2.0.  WCS 1.1 is
a low priority.
The possibility should be investigated to generalize *soap_proxy* to 
enable support of other protocols such as WPS.

*Soap_proxy* is implemented as a Web Service using the Axis2/C 
framework [AXIS], plugged into a standard Apache HTTP server via its 
mod_axis2 module.

Governance
----------

Source Code Location
^^^^^^^^^^^^^^^^^^^^

The *soap_proxy* code will be located in the subdirectory '*soap_proxy*' at the main
level of the eoxserver repository, i.e. at the same level as the eoxserver directory:
trunk/*soap_proxy*.

Initial Code Base
^^^^^^^^^^^^^^^^^
A first prototype implementing parts of the functionality has been developed under
the O3S project.  The source of this prototype will be copied to the *soap_proxy*
repository and form the basis for further development.

RFCs and Decision Process
^^^^^^^^^^^^^^^^^^^^^^^^^

In the early stages, development surrounding of *soap_proxy* not directly affecting 
eoxserver will be undertaken in a relaxed manner compared to the RFC based decision 
taking that prevails for eoxserver.

All non trivial changes to the *soap_proxy* core will be announced for discussion on 
the eoxserver-dev mailing list, but will not undergo the RFC voting process unless 
there is a direct impact on any actual eoxserver functionality.

Once the transition phase of the integration has been completed, the development of 
*soap_proxy* will follow the standard RFC based decision taking.

License
^^^^^^^
*Soap_proxy* will use either GPL or a MapServer-style license, this is yet TBD.

Wiki, Trac, Tickets
^^^^^^^^^^^^^^^^^^^
*Soap_proxy* will use all of the eoxserver support infrastructure.

References
----------

:[AXIS]: http://axis.apache.org/axis2/c/core/


Voting History
--------------

:Motion: Adopted on 2011-05-30 with +1 Martin Paces, Stephan Meißl, Fabian Schindler, Milan Novacek

Traceability
------------

:Requirements: "N/A"
:Tickets:      "N/A"

