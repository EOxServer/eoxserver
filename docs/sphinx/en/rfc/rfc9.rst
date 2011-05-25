.. _rfc_9:

RFC 9: SOAP Binding of WCS GetCoverage Response
===============================================

:Author:     Milan Novacek
:Created:    2011-05-17
:Last Edit:  2011-05-18
:Status:     PENDING
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc9

Introduction
------------

The current/draft OGC specifications for the SOAP binding for a WCS GetCoverage
Response are inconsistent with the SOAP spec if the GetCoverage response
includes a binary file.
This RFC proposes an update to OGC 09-149r1 to resolve the inconsistencies:  
Requirements 5 and 6 should be changed to use SOAP MTOM where the entire
coverage response comprises the attachment.  This coverage attachment is
referred to from within a new element 'Coverage' which is also defined as part
of this RFC.


Problem Description
-------------------

In OGC 09-149r1, Requirement 5 mandates that a GetCoverage SOAP response
shall be encoded as "SOAP with Attachments" as defined in [W3C Note 11],
but using SOAP 1.2 rather than SOAP 1.1. Requirement 6 says, rather
imprecisely, that in a GetCoverage response, the SOAP Envelope shall
contain one Body element which contains the Coverage as its single
element.

For binary attachments to SOAP 1.2  messages, W3C recommends the usage of MTOM
instead of SwA (see [1] and [2]).
According to the guidance in [1],  the SOAP 1.2 MTOM standard requires the use
of the xop:Include element to refer to binary attachments.
The difficulty arises because the "gml:rangeSet" element, which according to
OGC 09-110r is mandated for a GetCoverage response, does not have a provision
for using the xop:Include element to refer to an attached file.  For this
reason one cannot include a reference to an MTOM SOAP attachment in the
GetCoverage response.


Proposed Changes to OGC 09-149r1
--------------------------------

To resolve the problem, we propose to update two requirements of OGC 09-149r1
as follows:

  **Requirement 5:**
  A GetCoverage SOAP response **shall** be encoded according to the W3C SOAP 1.2
  standard [http://www.w3.org/TR/soap12-part1/] using MTOM
  [http://www.w3.org/TR/soap12-mtom/].

  **Requirement 6:**                                                                                                                         
  In a GetCoverage response, the SOAP Body **shall** contain one element,
  "Coverage" of type "SoapCoverageType", defined in the namespace 
  http://www.opengis.net/wcs/2.0, according to the schema definition
  in http://www.opengis.net/wcs/2.0/wcsSoapCoverage.xsd.

Schema Location
^^^^^^^^^^^^^^^
For discussion purposes of this RFC, the proposed schema *wcsSoapCoverage.xsd* is available
in the sandbox [3].
For convenience, *wcsCommon.xsd* in the same directory has been modified to include
*wcsSoapCoverage.xsd*.


References
----------

:[1]: http://www.w3.org/TR/soap12-part0/
:[2]: http://www.w3.org/TR/soap12-mtom/
:[3]: sandbox/sandbox_wcs_soap_proxy/schemas/wcs/2.0/wcsSoapCoverage.xsd

Voting History
--------------

"N/A"

Traceability
------------

:Requirements: "N/A"
:Tickets:      "N/A"

