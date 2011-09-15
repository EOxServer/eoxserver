.. RFC 6: Directory Structure

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
