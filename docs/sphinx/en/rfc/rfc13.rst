.. _rfc_13:

RFC 13: WCS-T 1.1 Interface Prototype 
=====================================

:Author:     Martin Paces 
:Created:    2011-09-13
:Last Edit:  2011-10-13
:Status:     DRAFT 
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc13

Introduction
------------

This RFC describes the design and implementation of the interface prototype of the *Open Geospatial Consortium* (OGC) 
*Web Coverage Service - Transaction operation extension* (WCSt) [OGC 07-068r4] standard. 
The WCSt extends the baseline WCS (allowing download of coverages only) by additional interface allowing modification 
of the stored coverages, namely, it allows adding, deleting, or updating of the coverages' data and their meta-data. 

WCS Transaction Operation
-------------------------

The WCSt standard [OGC 07-068r4] defines an additional WCS *transaction* operation which accepts the requests containing at least a single 
action to be performed. (Support for more than one action per request is optional.) The possible actions are: 
	* Add - inserts new coverage and its meta-data (required by all WCSt implementations)  
	* Delete - removes an existing coverage and its metadata (optional) 
	* UpdateAll - replace data and meta-data of an existing coverage (optional)  
	* UpdateMetadata - replace meta-data of an existing coverage (optional)  
	* UpdateDataPart - replace data subset of an existing coverage (optional)

The supported optional actions and the support for mutiple actions per request must be announced in the *ServiceIdentification*
section of the WCS *Capabilities* XML document using the *Profile* XML element (see [OGC 07-068r4] for detailed list of the applicable URNs). 

The *transaction* operation if further listed in the *OperationMetada* section of the WCS *Capabilities* in our implementation, although it is not explicitely mentioned 
by the [OGC 07-068r4] document and thus it is not clear whether this is required by WCSt as in case of the WCS baseline operations. 

The WCSt standart allows XML encoded request submitted as HTTP/POST requests. The KVP encoding of HTTP/GET requests are not supported by the WCSt since 
"the KVP encoding appears impractical without significantly restricting Transaction requests" [OGC 07-068r4].  
Futher, the [OGC 07-068r4] document mentiones that the exchanged XML documents MUST use the SOAP packaging.
We intentionally refused to follow this requirement and our implemetation supports exchange of the plain XML documents only. 
We suggest that the final implementation ot the transaction operatin should use the Soap-proxy wrapper as in case 
of the other WCS operations rather than waste the effort to duplicate the functionality implemented elsewhere.  

The transaction operation request can be processed in synchronous and asyncronous mode. In the first case, 
the request is proccesed immediattely and the transaction response is returned once actions have been processed successfully. 
In the latter case, the request is validated and accepted by the WCS server immediatelly returning simple acknowledgement XML document. 
The request is than processed asynchronously possibly much later than the acknowledgement XML document has been returned to the client. 

The aynchronous operation is trigered by presence of the 'responseHadler' field in the WCS-T request. 
This field contains an URL where the response document should be uploaded. 
Support for FTP upload and HTTP/POST is implemented. 

All the data passed to the server by the WCS-T requets are in form of URL references. 
The support for direct data passing via MIME/multi-part encoded request is not implemented neither required by the WCS-T standard. 
The one and only currently supported format of pixel data is GeoTIFF. 

The WCS-T requires that certain metadata must be provided by the client. These are geo-transformation, coverage description, and coverage summary. 
Since the current EexServer API does not provide means how to ingest this information 
(note that this information is provided by the GeoTIFF format and the EOP meta-data)
we simply ignore presence or absence of these infomration.

Currently only the rectified data-set coverages can be ingested (old Synchronizer API). 

WCS-T and Earth Observation Application Profile
-----------------------------------------------

In order to be able to ingest additional meta-data defined by the  *Earth Observation Application Profile* [ref.TBD]
we allow ingestion of client-defined EOP profile attached to the ingested pixel data. The EOP XML is passed 
as coverage OWS Metadata XML element with 'xlink:role="http://www.opengis.net/eop/2.0/EarthObservation"' . 

References
----------

:[OGC 07-068r4]: https://portal.opengeospatial.org/modules/admin/license_agreement.php?suppressHeaders=0&access_license_id=3&target=http://portal.opengeospatial.org/files/%3fartifact_id=28506


Voting History
--------------

*N/A*

Traceability
------------

:Requirements: "N/A"
:Tickets:      "N/A"
