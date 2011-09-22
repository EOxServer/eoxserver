.. SOAP WCS Access 

SOAP Access to WCS
==================

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
