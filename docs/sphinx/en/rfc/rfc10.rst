.. _rfc_10:

RFC 10: SOAP Binding of WCS GetCoverage Response
================================================

:Author:     Milan Novacek
:Created:    2011-05-18
:Last Edit:  2011-05-18
:Status:     IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc10

Introduction
------------

This RFC proposes the design and implementation of the module soap_proxy.
Initially soap_proxy is for use with WCS services. 
The intent of soap_proxy is to provide a soap processing front end for
those WCS services which do not natively accept soap messages.
Soap_proxy extracts the xml of a request from an incoming SOAP message
and invokes mapserver or eoxserver in POST mode with the extracted xml.
It then accepts the response from mapserver or eoxserver and repackages
it in a SOAP reply.


Description
-----------

TBD.


Voting History
--------------

"N/A"

Traceability
------------

:Requirements: "N/A"
:Tickets:      "N/A"

