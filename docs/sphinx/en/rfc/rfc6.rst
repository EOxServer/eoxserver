.. RFC 6: Directory Structure

.. _rfc_6:

RFC 6: Directory Structure
==========================

:Author: Stephan Krause
:Created: 2011-02-24
:Last Edit: 2011-07-20
:Status: IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc6

<short description of the RFC>

Introduction
------------

<Mandatory. Overview of motivation, addressed problems and proposed
 solution>
 
Directory Structure
-------------------

* distribution

  * ``core``
  * ``resources``
  
    * ``coverages``
    
      * ``formats``
    
    * ``vector``
    
      * ``formats``

  * ``processing``

    * ``processes``

  * ``services``
  
    * ``ows``

  * ``contrib``
  * ``plugins``
  
* instance

  * ``settings.py``
  * ``manage.py``
  * ``urls.py``
  * ``conf``
  
    * ``eoxserver.conf``
    * ``template.map``
  
  * ``data``
  * ``db``
  * ``plugins``

Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
