Identity Management System
==========================

Prerequisites
-------------

The following software is needed to run the IDMS:   
- Java JDK 6 or higher 
- Apache Tomcat 6 or higher
- Apache Axis2 1.4

The following software is needed to build the IDMS components:
- Java SDK 6 or higher
- Apache Ant 1.6.2 or higher
- Apache Maven2 or higher


 
LDAP Directory
--------------
The IDMS uses a LDAP directory to store user data (attributes, passwords, etc). 
You can use any directory implementation, supporting the Lightweight Directory Access 
Protocol (v3).

Tested implementations are:
- `Apache Directory Service`_

.. _Apache Directory Service http://directory.apache.org/


Security Token Service
-----------------------

The authentication service used for identity management is the HMA Authentication 
Service, a free and open source implementation of the WS-Trust Security Token 
Service (STS)). 

Please refer to the documentation inncluded in the  \docs folder of the HMA 
Authentication Service package how to compile and install the service.


Authorisation Service
---------------------

will be updated 
                          

Policy Enforcement Point Service
--------------------------------

will be updated

SOAP Proxy
----------

will be updated