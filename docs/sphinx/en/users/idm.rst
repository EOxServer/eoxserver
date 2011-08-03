Identity Management System
==========================

Prerequisites
-------------

The following software is needed to run the IDMS:  
 
- `Java <http://www.oracle.com/technetwork/java/index.html>`_ JDK 6 or higher 
- `Apache Tomcat <http://tomcat.apache.org/>`_ 6 or higher
- `Apache Axis2 <http://axis.apache.org/axis2/java/core/>`_ 1.4
- `MySQL <http://dev.mysql.com/downloads/>`_ 5 

The following software is needed to build the IDMS components:

- `Java <http://www.oracle.com/technetwork/java/index.html>`_  SDK 6 or higher
- `Apache Ant <http://ant.apache.org/>`_ 1.6.2 or higher
- `Apache Maven <http://maven.apache.org/>`_ 2 or higher


 
LDAP Directory
--------------
The IDMS uses a LDAP directory to store user data (attributes, passwords, etc). ou can use any directory implementation, supporting the Lightweight Directory Access Protocol (v3).

Tested implementations are:

* `Apache Directory Service <http://directory.apache.org/>`_



Security Token Service
-----------------------

The Security Token Service (STS) is responsible for the authentication of users  and  is documented and specified in the OASIS `WS-Trust <http://docs.oasis-open.org/ws-sx/ws-trust/200512/ws-trust-1.3-os.html>`_ specification. The authentication assertion produced by the STS is formulated in the `Security Assertion Markup Language <http://www.oasis-open.org/committees/download.php/3406/oasis-sstc-saml-core-1.1.pdf>`_. A client trying to access a service secured by the IDMS has to embed this assertion in every service request.

The STS implementation used by the IDMS is the `HMA Authentication Service <http://wiki.services.eoportal.org/tiki-index.php?page=HMA+Authentication+Service>`_. Please refer to the documentation inncluded in the  \docs folder of the HMA Authentication Service package how to compile and install the service.


Authorisation Service
---------------------

The Authorisation Service is responsible for the authorisation of service requests. It makes use of `XACML <http://www.oasis-open.org/committees/xacml/#XACML20>`_, a XML based language for access policies. The Authorisation Service is part of the `CHAORN <http://www.enviromatics.net/charon/index.html>`_ project. 

will be updated 
                          

Policy Enforcement Point Service
--------------------------------

The Policy Enforcement Point enforces the authorisation decisions made by the Authorisation Service. 

will be updated

SOAP Proxy
----------

The SOAP Proxy is used as a proxy for a secured service. This means a user client does not communicate directly with a secured service, instead it sends all requests to the proxy service.  

will be updated