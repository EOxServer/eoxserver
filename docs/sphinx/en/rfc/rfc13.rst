.. RFC 13: WCS-T 1.1 Interface Prototype
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@iguassu.cz>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 Iguassu Software Systems a.s.
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

.. _rfc_13:

RFC 13: WCS-T 1.1 Interface Prototype
=====================================

:Author:     Martin Paces 
:Created:    2011-09-13
:Last Edit:  $Date$
:Status:     ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc13

Introduction
------------

This RFC describes the design and implementation of the interface prototype 
of the *Open Geospatial Consortium* (OGC) `Web Coverage Service - Transaction 
operation extension (WCS-T) [OGC 07-068r4]`_ standard. 
The WCS-T extends the baseline WCS (allowing download of coverages only) by additionally
allowing modifications of the stored coverages, namely, it allows adding,
deleting, or updating of the coverages' data and their metadata. 

WCS Transaction Operation
-------------------------

The WCS-T standard [OGC 07-068r4] defines an additional WCS *transaction* operation 
to perform modifications of the WCS Coverages. A single *transaction* contains one 
or more actions to be performed over coverages (coverage actions). The WCS-T standard 
requires that all WCS-T implementations shall support at least one action per request, 
multiple actions per request are optional.

The possible coverage actions are:

 * Add - inserts new coverage and its metadata (required by all WCS-T implementations)  
 * Delete - removes an existing coverage and its metadata (optional) 
 * UpdateAll - replace data and metadata of an existing coverage (optional)  
 * UpdateMetadata - replace metadata of an existing coverage (optional)  
 * UpdateDataPart - replace data subset of an existing coverage (optional)

The supported optional features (multiple actions per request or optional coverage actions) 
shall be announced in the *ServiceIdentification* section of the WCS *Capabilities* XML document 
using the *Profile* XML element (see [OGC 07-068r4] for a detailed list of the applicable URNs). 

Although not explicitly mentioned by the WCS-T standard, we assume the *transaction* operation
shall be present in the *OperationMetada* section of the WCS *Capabilities*. 

The WCS-T standard allows XML encoded requests submitted as HTTP/POST requests. The KVP encoding
of HTTP/GET requests is not supported by WCS-T since "the KVP encoding appears impractical
without significantly restricting Transaction requests" [OGC 07-068r4].  
Further, the [OGC 07-068r4] introduction mentions that the exchanged XML documents
shall use the SOAP packaging, however, the examples are presented without the SOAP wrapping
leaving this requirement in doubts.

The WCS-T requests can be processed synchronously or asynchronously. 
In the first case, the request is processed immediately and the transaction response 
is returned once actions have been processed successfully. 
In the latter case, the request is validated and accepted by the server returning 
simple acknowledgement XML document. The request is than processed asynchronously
possibly much later than the acknowledgement XML document has been returned to the client. 
The asynchronous operation is triggered by presence of the *responseHandler* element in the 
WCS-T request. This element contains an URL where the response document should be uploaded. 

All the data passed to the server by the WCS-T requests are in form of URL references. 
The support for direct data passing via MIME/multi-part encoded requests is not considered
by the WCS-T standard.

The format of the ingested coverage data is not considered by the WCS-T standard at all. 
Neither it can be annotated by the WCS-T request nor by the WCS-T *OperationMetadata*. Thus 
we assume the format selection is left at discretion of the WCS-T implementation. 

The WCS-T standard requires that certain metadata shall be provided by the client.
These are geo-transformation, coverage description, and coverage summary. Apart 
from this mandatory metadata application specific metadata may be added by the 
implementation.

The WCS-T standard allows clients to submit their request and (created) coverages
identifiers. These identifiers do not need to be used by the WCS-T server as they 
may collide with the identifiers of other requests or coverages, respectively,
or simply not follow the naming convention of the particular WCS server. 
Thus the client provided identifiers are not binding for the WCS server and 
they rather provide a naming hint. As result of this the WCS-T client shall never 
rely on the identifiers provided to the WCS-T server but it shall always read 
the identifier returned by the WCS-T XML response. 


EOxServer Implementation 
~~~~~~~~~~~~~~~~~~~~~~~~

The WCS *transaction* operations is implemented using the service handlers API 
of EOxServer. Since the WCS-T standard requires the version of the *transaction* 
operation to be '1.1' (rather than the '1.1.0' version used by other WCS operations) 
a specific WCS 1.1 version handler must have been employed. 
The operation itself is then implemented as a request handler.

Since the presence of the WCS-T operation needs to be announced by the WCS *Capabilities*
the WCS 1.1.x *getCapabilities* operation request handlers have to be modified.
Since the *Capabilities* XML response is generated by the MapServer (external library)
the only feasible way to introduce the additional information to the *getCapabilities*
XML response is to: i) capture the MapServer's response, ii) modify the XML document, 
and iii) send the modified XML instead of the MapServer's one. 

The *transaction* request or response XML documents do not use the (presumably) required 
SOAP packaging. We have intentionally refused to follow this requirement in 
our implementation as the SOAP packing and unpacking is duty of EOxServer's *SOAP  Proxy* 
component and our own implementation would rather duplicate the functionality 
implemented elsewhere. 

Our implementation, by default, offers the WCS-T core functionality only. All the optional 
features such as multiple coverage actions per request or the optional coverage actions
shall be explicitly enabled by EOxServer's configuration (see following section for 
details). 

Both synchronous and asynchronous modes of operation are available. 
While the synchronous request are processed within the context of the WCS-T request
handler the asynchronous requests are parsed and validated within the context 
of the WCS-T request but the processing itself is performed by the Asynchronous Task 
Processing (ATP) subsystem of EOxServer. Namely, the processing task is enqueued to the 
task queue and than later executed by one of the employed Asynchronous Task Processing
Daemons (ATPD). More details about the ATP can be found in [ATP-RFC]. 

As it was already mentioned, the asynchronous mode of operation is triggered by presence 
of the *responseHandler* element in the WCS-T request and this element contains an URL where 
the response document should be uploaded. Our implementation supports following protocols: 

 * FTP - using the PUT command; username/password FTP authentication is possible 
 * HTTP - using POST HTTP request; username/password FTP authentication is possible

Secured (SSL or TLS) versions of the protocols are currently not supported. 

The username/password required for authentication can be specified directly by the URL 
:: 

  scheme://[username:password@]domain[:port]/path

In case of FTP, when the paths point to a directory a new file will be created taking the 
request ID as the base file-name and adding the '.xml' extension. Otherwise a file given 
by the path will be created or rewritten. 

The WCS-T implementation uses always pairs of identifiers (internal and public) for both 
request and (created) coverage identifiers. The public identifiers are taken from the WCS-T
request, provided they do not collide with identifiers in use. In case of not supplied or colliding 
identifiers the public identifiers are set from the internal ones. 
The public identifiers are used in the client/server communication or for naming of the 
newly created coverages. The internal identifiers are exclusively used for naming 
of the internal server resources (asynchronous tasks, directory and file names, etc.)

Each WCS-T request, internally, gets a *context*, i.e. set of resources assigned to a particular 
request instance. These resources are: i) an isolated temporary workspace (a directory to store 
intermediate files deleted automatically once the request is finished), ii) an isolated permanent
storage (a directory where the inserted coverages and their metadata is stored) and iii) in case of 
asynchronous mode of operation ATP task instance. These resources make use of the internal 
identifiers only. 

EOxServer Configuration
~~~~~~~~~~~~~~~~~~~~~~~

The EOxServer's WCS-T implementation need to be configured prior to the operation. 
The configuration is set in EOxServer's 'eoxserver.conf' file. 
The WCS-T specific options are grouped together in the 'services.ows.wcst11' section. 

The WCS-T options are: 

 * allow_multiple_actions (False|True) - allow multiple actions per single WCS-T request. 
 * allowed_optional_action (Delete,UpdateAll,UpdateMetadata,UpdateDataPart) - 
   comma separated list of enabled optional WCS-T coverage action. Set empty if none. 
 * path_wcst_temp (*path*) - directory to use as temporary workspace 
 * path_wcst_perm (*path*) - directory to use as permanent workspace


Example: 

::

    ...
    # WCS-T 1.1 settings
    [services.ows.wcst11]

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The one and only currently supported format of pixel data is GeoTIFF.

All the necessary meta-data required by the EOxServer are extracted from the GeoTIFF
annotation and (optionally) from the provided EO meta-data (see section below). 

Due to the limitations of the current Coverage Managers' API of the EOxServer 
the current WCS-T implementation has following restrictions:

* only rectified grid coverages can be ingested;
* ``urn:ogc:def:role:WCS:1.1:CoverageDescription`` metadata are ignored and 
  even not required as this information cannot be inserted to EOxServer anyway;
* ``urn:ogc:def:role:WCS:1.1:CoverageSummary`` metadata are ignored 
  as this information cannot be inserted to EOxServer anyway;
* ``urn:ogc:def:role:WCS:1.1:GeoreferencingTransform`` metadata are ignored 
  as this information is relevant to referenced data only 
* ``urn:ogc:def:role:WCS:1.1:OtherSource`` metadata are ignored 
  as this information cannot be inserted to EOxServer anyway.

WCS-T and Earth Observation Application Profile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to be able to ingest additional metadata as defined by the 
*WCS 2.0 - Earth Observation Application Profile* [EO-WCS]
we allow the ingestion of client-defined EO-WCS metadata attached to 
the ingested pixel data. The EO-WCS XML is passed 
as coverage OWS Metadata XML element with 
'xlink:role="http://www.opengis.net/eop/2.0/EarthObservation"'.

Governance
----------

Source Code Location
~~~~~~~~~~~~~~~~~~~~

http://eoxserver.org/svn/sandbox/sandbox_wcst

RFCs and Decision Process
~~~~~~~~~~~~~~~~~~~~~~~~~

*TBD*

License
~~~~~~~

The WCS-T implementation shall be distributed under the terms of :ref:`EOxServer's MapServer-like license <EOxServer Open License>`. 

Wiki, Trac, Tickets
~~~~~~~~~~~~~~~~~~~

*TBD*

References
----------

:[OGC 07-068r4]: http://portal.opengeospatial.org/files/?artifact_id=28506
:[ATP-RFC]: http://eoxserver.org/doc/en/rfc/rfc14.html
:[EO-WCS]:	*TBD* 

Voting History
--------------

:Motion: To accept RFC 13
:Voting Start: 2011-12-15 
:Voting End: 2011-12-22
:Result: +3 for ACCEPTED

Traceability
------------

:Requirements: *N/A*
:Tickets:      *N/A*

.. _Web Coverage Service - Transaction operation extension (WCS-T) [OGC 07-068r4]: http://portal.opengeospatial.org/files/?artifact_id=28506
