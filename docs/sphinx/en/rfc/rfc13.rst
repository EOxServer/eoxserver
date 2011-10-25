.. _rfc_13:

RFC 13: WCS-T 1.1 Interface Prototype 
=====================================

:Author:     Martin Paces 
:Created:    2011-09-13
:Last Edit:  2011-10-25
:Status:     DRAFT 
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc13

Introduction
------------

This RFC describes the design and implementation of the interface prototype 
of the *Open Geospatial Consortium* (OGC) *Web Coverage Service - Transaction 
operation extension* (WCSt) [OGC 07-068r4] standard. 
The WCSt extends the baseline WCS (allowing download of coverages only) by additional
interface allowing modification of the stored coverages, namely, it allows adding,
deleting, or updating of the coverages' data and their meta-data. 

WCS Transaction Operation
-------------------------

The WCSt standard [OGC 07-068r4] defines an additional WCS *transaction* operation 
to perform modification of the WCS Coverages. A single *transaction* contains one 
or more actions to be performed over coverages (coverage actions). WCSt standard 
requires that all WCSt implementation shall support at least one action per request
and multiple actions per request are optional. 
The possible coverage actions are : 
	* Add - inserts new coverage and its meta-data (required by all WCSt implementations)  
	* Delete - removes an existing coverage and its metadata (optional) 
	* UpdateAll - replace data and meta-data of an existing coverage (optional)  
	* UpdateMetadata - replace meta-data of an existing coverage (optional)  
	* UpdateDataPart - replace data subset of an existing coverage (optional)

The supported optional features (multiple actions per request or optional coverage actions) 
shall announced in the *ServiceIdentification* section of the WCS *Capabilities* XML document 
using the *Profile* XML element (see [OGC 07-068r4] for detailed list of the applicable URNs). 

Although not explicitly mentioned by the WCSt standard, we assume the *transaction* operation
shall be present in the *OperationMetada* section of the WCS *Capabilities*. 

The WCSt standard allows XML encoded request submitted as HTTP/POST requests. The KVP encoding
of HTTP/GET requests are not supported by the WCSt since "the KVP encoding appears impractical
without significantly restricting Transaction requests" [OGC 07-068r4].  
Further, the [OGC 07-068r4] introduction mentions that the exchanged XML documents
shall use the SOAP packaging, however, the examples are presented without the SOAP wrapping
leaving this requirement in doubts. 

The WCSt requests can be processed synchronously or asynchronously. 
In the first case, the request is processed immediately and the transaction response 
is returned once actions have been processed successfully. 
In the latter case, the request is validated and accepted by the server returning 
simple acknowledgement XML document. The request is than processed asynchronously
possibly much later than the acknowledgement XML document has been returned to the client. 
The asynchronous operation is triggered by presence of the *responseHadler* element in the 
WCSt request. This element contains an URL where the response document should be uploaded. 

All the data passed to the server by the WCSt requests are in form of URL references. 
The support for direct data passing via MIME/multi-part encoded requests is not considered
by the WCSt standard.

The format of the ingested coverage data is not considered by the WCSt standard at all. 
Neither it can be annotated by the WCSt request or by the WCSt *OperationMetadata*. Thus 
we assume the format selection is left at discretion of the WCSt implementation. 

The WCSt standard requires that certain metadata shall be provided by the client.
These are geo-transformation, coverage description, and coverage summary. Apart 
from this mandatory metadata application specific metadata may be added by the 
implementation.

The WCSt standard allows clients to submit their request and (created) coverages
identifiers. These identifiers does not need to be used by the WCSt server as they 
may collide with the identifiers of the other requests or coverages, respectively,
or simply not follow the naming convention of the particular WCS server. 
Thus the client provided identifiers are not binding for the WCS server and 
they provider rather naming hint. As result of this WCSt client shall never 
relay on the identifiers provided to the WCSt server but it shall always read 
the identifier returned by the WCSt XML response. 


EOxServer Implementation 
~~~~~~~~~~~~~~~~~~~~~~~~

The WCS *transaction* operations is implemented using the service handlers API 
of the EOxServer.  Since the WCSt standard requires the version of the *transaction* 
operation to be '1.1' (rather than the '1.1.0' version used by other WCS operations) 
a specific WCS 1.1 version handler must have been employed. 
The operation itself is then implemented as an request handler.

Since the presence of the WCSt operation needs to be announced by the WCS *Capabilities*
the WCS 1.1.x *getCapabilities* operation request handler must have been modified.
Since the *Capabilities* XML response is generated by the MapServer (external library)
the only feasible way to introduce the additional information to the *getCapabilities*
XML response is to: i) capture the MapServer's response, ii) modify the XML document, 
and iii) fetch the modified XML instead of the MapServer's one. 

The *transaction* request or response XML documents do not use the (presumably) required 
SOAP packaging. We have intentionally refused to follow this requirement in 
our implementation as the SOAP packing and unpacking is duty of the *SOAP-proxy* EOxServer's 
component and our own implementation would rather duplicate the functionality 
implemented elsewhere. 

Our implementation, by default, offers the WCSt core functionality only. All the optional 
features such as multiple coverage actions per request or the optional coverage actions
shall be explicitly enabled by the EOxServer's configuration (see following section for 
details). 

Both synchronous and asynchronous modes of operation are available. 
While the synchronous request are processed within the context of the WCSt request
handler the asynchronous requests are parsed and validated within the context 
of the WCSt request but the processing is self is performed by the Asynchronous Task 
Processing (ATP) subsystem of the EOxServer. Namely, the processing task is enqueued to the 
task queue and than later executed by one of the employed Asynchronous Task Processing
Daemons (ATPD). More details about the ATP can be found in [ATP-RFC]. 

As it was already mentioned, the asynchronous mode of operation is triggered by presence 
of the *responseHadler* element in the WCSt request and this element contains an URL where 
the response document should be uploaded. Our implementation supports following protocols: 

	* FTP - using the PUT command; username/password FTP authentication is possible 
	* HTTP - using POST HTTP request; username/password FTP authentication is possible

Secured (SSL or TLS) versions of the protocols are currently not supported. 

The username/password required for authentication can be specified directly by the URL 
:: 

	scheme://[username:password@]domain[:port]/path

In case of FTP, when the paths point to a directory a new file will be created taking the 
request ID as the base file-name and adding the '.xml' extension. Other wise a file given 
by the path will be created or rewritten. 

The WCSt implementation uses always pair of identifiers (internal and public) for both 
request and (created) coverage identifiers. The public identifiers taken from the WCSt
request, provided they do not collide with identifiers in use. In case no or colliding 
identifiers the public identifiers are set from the internal ones. 
The public identifiers are used in the client/server communication or for naming of the 
newly created coverages. The internal identifiers are exclusively used for naming 
of the internal server resources (asynchronous tasks, directory and file names, etc.)

Each WCSt request, internally, gets a *context*, i.e. set of resources assigned to a particular 
request instance. These resources are: i) an isolated temporary workspace (a directory to store 
intermediate files deleted automatically once the request is finished), ii) an isolated permanent
storage (a directory where the inserted coverages and their metadata is stored) and iii) in case of 
asynchronous mode of operation ATP task instance. These resources make use of the internal 
identifiers only. 

EOxServer Configuration
~~~~~~~~~~~~~~~~~~~~~~~

The EOxServer's WCSt implementation need to be configured prior the operation. 
The configuration is set in the EOxServer's 'eoxserver.conf' file. 
The WCSt specific option are grouped to 'service.ows.wcst11' section. 

The WCSt options are: 

	* allow_multiple_actions (False|True) - allow multiple actions per single WCSt request. 
	* allowed_optional_action (Delete,UpdateAll,UpdateMetadata,UpdateDataPart) - 
		comma separated list of enabled optional WCSt coverage action. Set empty if none. 
	* path_wcst_temp (*path*) - directory to use as temporary workspace 
	* path_wcst_perm (*path*) - directory to use as permanent  workspace


Example: 

::

	...
	# WCS-T 1.1 settings
	[service.ows.wcst11]	

	# enble disable multiple actions per request 
	allow_multiple_actions=False

	# list enabled optional actions {Delete,UpdateAll,UpdateMetadata,UpdateDataPart}
	allowed_optional_actions=Delete,UpdateAll 

	# temporary storage 
	path_wcst_temp=/home/test/o3s/sandbox_wcst_instance/wcst_temp

	# permanent data storage 
	path_wcst_perm=/home/test/o3s/sandbox_wcst_instance/wcst_perm
	...


Coverages, Data and Metadata
~~~~~~~~~~~~~~~

Currently only the rectified data-set coverages can be ingested (old Synchronizer API). 

The one and only currently supported format of pixel data is GeoTIFF. 

As mentioned in the introduction the WCS-T requires that certain metadata must be
provided by the client. These are geo-transformation, coverage description, 
and coverage summary.  Since the current EOxServer API does not provide means 
how to ingest this information (note that this information is provided by the 
GeoTIFF format and the EOP meta-data) we simply ignore presence or absence 
of these meta-data. 


WCS-T and Earth Observation Application Profile
~~~~~~~~~~~~~~~

In order to be able to ingest additional meta-data defined by the 
*Earth Observation Application Profile* [EOP]
we allow ingestion of client-defined EOP profile attached to 
the ingested pixel data. The EOP XML is passed 
as coverage OWS Metadata XML element with 
'xlink:role="http://www.opengis.net/eop/2.0/EarthObservation"' . 

Governance
----------

Source Code Location
~~~~~~~~~~~~~~~~~~~~

http://eoxserver.org/svn/sandbox/sandbox_wcst

Initial Code Base
~~~~~~~~~~~~~~~~~
A first prototype implementing parts of the functionality has been developed under
the O3S project. 

RFCs and Decision Process
~~~~~~~~~~~~~~~~~~~~~~~~~

*TBD*

License
~~~~~~~

The WCSt implementation shall be distributed under the terms of the EOX-Server's MapServer-like licence. 

Wiki, Trac, Tickets
~~~~~~~~~~~~~~~~~~~

*TBD*

References
----------

:[OGC 07-068r4]: https://portal.opengeospatial.org/modules/admin/license_agreement.php?suppressHeaders=0&access_license_id=3&target=http://portal.opengeospatial.org/files/%3fartifact_id=28506
:[ATP-RFC]: *TBD*
:[EOP]:	*TBD* 

Voting History
--------------

*N/A*

Traceability
------------

:Requirements: "N/A"
:Tickets:      "N/A"
