.. RFC 11: WPS 1.0.0 Interface Prototype
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

.. _rfc_11:

RFC 11: WPS 1.0.0 Interface Prototype
=====================================

:Author:     Martin Paces 
:Created:    2011-07-20
:Last Edit:  2011-07-21
:Status:     DRAFT 
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc11

Introduction
------------

This RFC describes the design and implementation of the OGC WPS 1.0.0 
Interface prototype.  The WPS (Web Processing Service) interface 
prototype adds the processing functionality to the EOX-Server 
and in capable of invocation of both synchronous ans 
asynchronous processes invoked using either XML or KVP 
encoding as described in  OGC 05-007r7 *OpenGIS Web Processing Service* 
document.

Description
-----------

The implementation extends the set of EOX-Server's OWS service handlers 
by the WPS specific interface. Namely, it ads following handlers

	* WPS service handler
	* WPS 1.0.0 version handler 
	* WPS *GetCapabilities* operation handler 
	* WPS *DescribeProcess* operation handler 
	* WPS *Execute operation* handler 

The added WPS functionality could be split three (currently separated) 
logical parts:

	* WPS interface and operation logic (subject to this RFC)
	* WPS data model and generic process class (loosely based on
	  PyWPS, currently separated from the interface and operation logic) 
	* WPS process instances – user defined processes, ancestors of the generic 
	  service class (completely independent of the EOX-Server, not subject to this RFC)

WPS Interface and Operation Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This part implements the actual OWS service handlers and it is tightly coupled with the EOX-Server. 
It parses and interprets the operation request and generates the operation responses reusing 
existing parts of the EOX-Server (primarily the XML and KVP request decoders). 
This interface has access to the installed WPS process instances (implemented as python modules) 
and it reads their descriptions. In case of the *Execute* operation it fetches the parsed input data 
to the selected process instance, triggers the actual execution of the process, and generates the status 
responses and handles output data XML packing and encoding.

In case of a synchronous execution the WPS processes are executed in context of the EOX-Server's OWS request. 
In case of an asynchronous WPS processes a dedicated OS process is started from the context of the EOX-Server's OWS request.

This part is distributed under the EOX-Server's MapServer-like open source licence.

WPS Data Model and Generic Process Class 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This part (not subject to this RFC) is loosely based on the WPS Process API of the :PyWPS: 
SW. Due to the flaws of the original data model and 
requirements of the EOX-Server integration the the original :PyWPS: code was substantially modified
(practicall rewritten) leaving only traces of the generic (parent) WPS Process class. 

The work is based on the stable :PyWPS: version 3.1.0. The reason we have replaced the original 
data model was that it had several design and implantation flaws 
(e.g., the way how the multiple input and output
data occurrences were handled, bounding box data handling and encoding, the way how input sequences 
were detected). After first initial correcting attempts we gave up and rewrote the model from scratch.
The generic Process class was modified: (i) due to the the changes made to the data model, 
(ii) removing unused parts of code (e.g., useless class reinitialization, Grass integration,
internationalization), (iii) and finally due to the needs of the EOX-Server integration.

Despite the only fragments of the original :PyWPS:, this code was derived from the :PyWPS: and it 
is distributed under the terms of the original GPL licence.

WPS Process Instances
~~~~~~~~~~~~~~~~~~~~~

The process instances are not subject to this RFC and should be written by the WPS users 
to provide the desired functionality. The processes are created as separated python 
modules each containing a single customized sub-class of the generic process class. 
The unique process identifier is the same as the name of python module (file's base name), 
the rest of the process description is defined by an implementer in the class definition.

We provide set of sample demo process samples covering from basic to most advanced cases.
This part is distributed under the terms of PyWPS GPL licence.


Transition to Operation - Issues to be resolved 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The existing prototype has still a couple issues to be resolved before operational deployment. 

	* licence issues - the WPS Process's data model and parent Process's class shall be merged 
	  with the WPS Interface and Operation logic and distributed together under the same licence terms 

	* resource tracker - there should be a resource tracker looking after the used resources, 
	  i.e., stored files and executed asynhronous processes. Each of these resources shall be monitored 
	  and released (deleted in case of unused files, properly killed in case of "zombie" processes) once 
	  is not usefull anymore. 

Governance
----------

Source Code Location
~~~~~~~~~~~~~~~~~~~~

WPS Interface 
^^^^^^^^^^^^^

Currently the Interface code can be downloaded from the WPS sandbox: 

	http://eoxserver.org/svn/sandbox/sandbox_wps

WPS - Data Model and Generic Process Class 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The code derived from the PyWPS (only the parts needed for EOX-Server integration)
can be found at:

	http://o3s.eox.at/svn/deliverables/developments/wps/server

WPS - Demo Processes 
^^^^^^^^^^^^^^^^^^^^

The demo services are available at: 

	https://o3s.eox.at/svn/deliverables/developments/wps/wps_demo_services/


Initial Code Base
~~~~~~~~~~~~~~~~~
A first prototype implementing parts of the functionality has been developed under
the O3S project. 

RFCs and Decision Process
~~~~~~~~~~~~~~~~~~~~~~~~~

*TBD*

License
~~~~~~~

*WPS Interface* prototype shall be distributed under the terms of the EOX-Server's MapServer-like licence. 

The other parts required by the WPS functionality are available under the terms of the [PyWPS] GPL licence. 


Wiki, Trac, Tickets
~~~~~~~~~~~~~~~~~~~

*TBD*

References
----------

:[PyWPS]: http://pywps.wald.intevation.org/


Voting History
--------------

*N/A*

Traceability
------------

:Requirements: "N/A"
:Tickets:      "N/A"

