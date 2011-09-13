.. Architecture

Architecture
============

TBD Architecture goes here.

The protocol is SOAP 1.2 over HTTP.

EOxServer responds to the following WCS-EO requests via its SOAP service interface:

* DescribeCoverage
* DescribeEOCoverageSet
* GetCapabilities
* GetCoverage

 -- TBD --


Implementation
--------------

Soap_proxy  uses the axis2/C framework.

One notable feature of axis2/C is that it correctly handles SOAP 1.2 MTOM
Attachments.

 -- TBD --


