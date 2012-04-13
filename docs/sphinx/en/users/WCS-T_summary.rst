.. wcst_sum 
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (c) 2012 EOX IT Services GmbH 
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

.. _wcst_sum:

Web Coverage Service - Transaction Extension  
============================================

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

Introduction 
------------
This text describes the *Web Coverage Service - Transaction* (WCS-T) extension
as implemented in the *EOxServer*. The WCS-T interface is based on 
*Open Geospatial Consortium* (OGC) Web Coverage Service - Transaction operation 
extension (WCS-T) `[OGC 07-068r4]`_ standard which describe in detail
the invocation of the service. The WCS-T functionality is closely related to the
the data model of the WCS 2.0 *Earth Observation Application Profile* (EO-AP)
employed by the *EOxServer* and allows specification of EO-AP metadata for the
newly inserted EO datasets. 

Implementation Details 
----------------------

The *EOxServer* provides to option to insert (*Add* action) and delete
(*Delete*)coverages (datasets in EO-AP jargon) via the WCS-T service
invocation. 

Configuration 
^^^^^^^^^^^^^

For details on WCS-T configuration see ":ref:`ConfigurationOptionsWCST11`"

Adding New Coverages
^^^^^^^^^^^^^^^^^^^^
Currently, it is possible to insert only *Rectified* and *Referenceable*
datasets. It is beyond the capabilities of the WCS-T service to assign
datasets to container coverage types such as the *Rectified Stitched Mosaic* or 
*Dataset Series*. Neither it is possible to create plain (non-EO-AP) coverages.

The input image data must in valid GeoTIFF file format. No other file format is
currently supported. The input is passed to WCS-T service as a reference (URL, e.g.,
the *GetCoverage* KVP encoded request). It is not possible to embed the input image
data in the WCS-T request. 

The creation of a new EO-AP dataset requires specification of the EO metadata.
These metadata can be either passed by the user (recommended way) as a reference 
using the ``ows:medatata`` XML element, or generated automatically by the WCS-T
service guessing some of the parameters from the GeoTIFF annotation. 

The user provided EO-AP metadata can be either in form of an EOM-XML document or
arbitrary XML document with embedded EOM-XML fragment (such as the *DescribeCoverage*
response). 

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <wcst:Transaction service="WCS" version="1.1"
      xmlns:wcst="http://www.opengis.net/wcs/1.1/wcst"
      xmlns:ows="http://www.opengis.net/ows/1.1"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
        <wcst:InputCoverages>
            <wcst:Coverage>
                <!-- optional coverage identifier -->
                <ows:Identifier>CoverageId</ows:Identifier>
                <!-- reference to image data -->
                <ows:Reference 
                    xlink:href="http://foo.eox.at/ows?service=WCS&amp;version=2.0.0&amp;request=getCoverage&amp;format=image/tiff&amp;coverageid=CoverageId" 
                    xlink:role="urn:ogc:def:role:WCS:1.1:Pixels"/>
                <!-- optional reference to EO metadata -->
                <ows:Metadata 
                    xlink:href="http://foo.eox.at/ows?service=WCS&amp;version=2.0.0&amp;request=describeCoverage&amp;coverageid=CoverageId" 
                    xlink:role="http://www.opengis.net/eop/2.0/EarthObservation"/>
                <wcst:Action codeSpace="http://schemas.opengis.net/wcs/1.1.0/actions.xml">Add</wcst:Action>
            </wcst:Coverage>
        </wcst:InputCoverages>
    </wcst:Transaction>

The coverage identifier specified by the ``ows:Identifier`` element is optional.
When not specified or the identifier cannot be used (most likely because it is
already in use by another coverage) a new, unique identifier is generated
automatically. Thus the WCS-T service is not bound by the user provided
identifier and the actual identifier shall be always read from the transaction
response:

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <TransactionResponse 
      xmlns="http://www.opengis.net/wcs/1.1/wcst"
      xmlns:ows="http://www.opengis.net/ows/1.1"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
        <RequestId>wcstReq_btjiFfo4aOvT1BQL-ki5</RequestId>
        <ows:Identifier>wcstCov_LoEYNGm3d10ZhUUGdlmm</ows:Identifier>
    </TransactionResponse>

Unless the there is a need for specific coverage identifier we recommend to
leave the identifier selection to be performed by the WCS-T service and omit the
``ows:Identifier`` element in case of WCS-T coverage inserts. 


Deleting Existing Coverages 
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The coverages inserted via the WCS-T Add action can be removed by means of the
WCS-T Delete action. For security reasons, only the coverages inserted via the
WCS-T can be actually removed via the WCS-T. The only parameter required by the
removal request is the coverage (dataset) identifier (``wcst:InputCoverages``
XML element): 

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <wcst:Transaction service="WCS" version="1.1"
      xmlns:wcst="http://www.opengis.net/wcs/1.1/wcst"
      xmlns:ows="http://www.opengis.net/ows/1.1"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
        <wcst:InputCoverages>
            <wcst:Coverage>
                <!-- required coverage identifier -->
                <ows:Identifier>wcstCov_LoEYNGm3d10ZhUUGdlmm</ows:Identifier>
                <wcst:Action codeSpace="http://schemas.opengis.net/wcs/1.1.0/actions.xml">Delete</wcst:Action>
            </wcst:Coverage>
        </wcst:InputCoverages>
    </wcst:Transaction>

Asynchronous Operation
^^^^^^^^^^^^^^^^^^^^^^
EOxServer supports asynchronous WCS-T request as specified by the standard `[OGC
07-068r4]`_ . Asynchronous request processing can be invoked by any WCS-T
request including the ``wcst:ResponseHandler`` element. This element shall
contain an URL of the remote response handler where the response shall be sent
when the asynchronous processing is finished: 

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <wcst:Transaction service="WCS" version="1.1"
      xmlns:wcst="http://www.opengis.net/wcs/1.1/wcst"
      xmlns:ows="http://www.opengis.net/ows/1.1"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
        <wcst:InputCoverages>
            ...
        </wcst:InputCoverages>
        <wcst:RequestId>RequestId</wcst:RequestId>
        <!-- XML element enabling the asynchronous WCS-T processing -->
        <wcst:ResponseHandler>http://foo.eox.at/WCSTResponseHandler</wcst:ResponseHandler>
    </wcst:Transaction>

Currently, WCS-T implementaition supports HTTP and FTP URL schemas for the
response handler. In the first case the response is delivered using HTTP/POST.
In the latter case, the response is uploaded to a remote FTP server. In case of
FTP, the user may specify a full filename of the delivered file or target
directory. If the FTP target is a directory the file-name of the stored response
is generated from the request ID returned by the acknowledgement response:

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <Acknowledgement 
      xmlns="http://www.opengis.net/wcs/1.1/wcst"
      xmlns:ows="http://www.opengis.net/ows/1.1"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
        <TimeStamp>2012-04-13T16:00:07Z</TimeStamp>
        <RequestId>wcstReq_6syhsJbO2TtYwVxFHOur</RequestId>
    </Acknowledgement>

It is worth to mention that request identifier can be specified in the WCS-T
request however this identifier provides only hint to the WCS-T server and the
server may change it to another value. Thus it is recommended to rely on the
request identifier written the WCS-T response and better omit the optional 
``wcst:RequestId`` XML element in the WCS-T request. 

It is possible to specify user/password for the response handler for both HTTP
and FTP using the typical URL structure:: 

    <schema>://[<username>@<password>]<host>/<path>

No other authentication is currently supported. 

The asynchronous WCS-T operation requires the ATP (Asynchronous Task Processing)subsystem and, in particular,
an ATPD (ATP Daemon) running. For more info on the ATP subsystem see ":ref:`atp_sum`".

References
----------

:[OGC 07-068r4]: http://portal.opengeospatial.org/files/?artifact_id=28506


.. _[OGC 07-068r4]: http://portal.opengeospatial.org/files/?artifact_id=28506
