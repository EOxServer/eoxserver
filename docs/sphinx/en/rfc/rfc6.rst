.. RFC 6: Directory Structure
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 EOX IT Services GmbH
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

.. _rfc_6:

RFC 6: Directory Structure
==========================

:Author: Stephan Krause
:Created: 2011-02-24
:Last Edit: 2011-09-15
:Status: ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc6

This RFC proposes a directory structure for the EOxServer distribution
as well as EOxServer instances.

Introduction
------------

:doc:`rfc1` introduces a layered architecture for EOxServer as well as
a separation of EOxServer distribution and instances. This RFC lays
out a directory structure that is in line with this architecture.

Directory Structure
-------------------

Distribution
~~~~~~~~~~~~

  * ``core``: contains the modules of the Core

    * ``util``: contains utility modules to be used throughout the
      project

  * ``services``: contains the modules of the Service Layer
  
    * ``ows``: contains implementations of OGC Web Services

  * ``processing``: contains the modules of the Processing Layer

    * ``processes``: contains processes

  * ``resources``: contains the modules of the Data Integration Layer
  
    * ``coverages``: contains the modules related to coverage resources
    
      * ``formats``: contains the modules related to coverage formats
    
    * ``vector``: contains the modules related to vector data
    
      * ``formats``: contains the modules related to vector data formats

  * ``contrib``: contains (links to) third party modules
  
  * ``conf``: contains the default configuration
  
Instance
~~~~~~~~

The instance directory contains the three Django project modules:

  * ``settings.py``
  * ``manage.py``
  * ``urls.py``
  
And the following subdirectories

  * ``conf``: configuration files
  
    * ``eoxserver.conf``: the central EOxServer configuration
    * ``template.map``: template MapFile for OWS requests
  
  * ``data``: database files

    * ``config.sqlite``: SQLite database

Voting History
--------------

:Motion: To accept RFC 6
:Voting Start: 2011-07-25
:Voting End: 2011-09-15
:Result: +6 for ACCEPTED

Traceability
------------

:Requirements: N/A
:Tickets: N/A
