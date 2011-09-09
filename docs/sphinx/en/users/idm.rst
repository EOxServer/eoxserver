Identity Management System
==========================

The Identity Management System (IDMS) provides access control capabilities for  security relevant data. The current IDMS supports SOAP Services and is based on other free and open software projects, namely the `Charon Project <http://www.enviromatics.net/charon/>`_ and the `HMA Authentication Service <http://wiki.services.eoportal.org/tiki-index.php?page=HMA+Authentication+Service>`_. The approach follows the OGC best practise document `User Management Interfaces for Earth Observation Services <http://portal.opengeospatial.org/files/?artifact_id=40677>`_ for the authentication concept. The authentication part is following the ideas of the `XACML <http://docs.oasis-open.org/xacml/2.0/access_control-xacml-2.0-core-spec-os.pdf>`_ data flow pattern: The IDMS authorisation part consists of a Policy Decision Point (PDP, here represented through the Charon Policy Management And Authentication Service) and the Policy Enforcement Point (PEP, represented through the Charon PEP Service). The following figure gives an overview of the IDMS SOAP part:

.. figure:: img/IDM_SOAP_Components.png
   :align: center

   *IDMS SOAP Access Control Overview*


The HMA Authentication Service, or Security Token Service (STS), and the Charon PEP components were both modified in order to be compatible. This is a result of the ESA project `Open-standard Online Observation Service <http://wiki.services.eoportal.org/tiki-index.php?page=O3S>`_ (O3S). The STS now also supports SAML 2.0 security tokens, which the PEP components can interprete and validate. The IDMS supports trust relationships between identity providers and enforecement components on the basis of certificate stores.   

Prerequisites
-------------

The following software is needed to run the IDMS:  
 
- `Java <http://www.oracle.com/technetwork/java/index.html>`_ JDK 6 or higher 
- `Apache Tomcat <http://tomcat.apache.org/>`_ 6 or higher
- `Apache Axis2 <http://axis.apache.org/axis2/java/core/>`_ 1.4.1 or higher
- `MySQL <http://dev.mysql.com/downloads/>`_ 5 
- `Apache HTTP Server <http://httpd.apache.org/>_` 2.x


The following software is needed to build the IDMS components:

- `Java <http://www.oracle.com/technetwork/java/index.html>`_  SDK 6 or higher
- `Apache Ant <http://ant.apache.org/>`_ 1.6.2 or higher
- `Apache Maven <http://maven.apache.org/>`_ 2 or higher


General Configuration for CHARON services:

- The Charon services need the ``acs-xbeans-1.0.jar`` dependency in the ``\lib`` folder of your  Axis2 installation (presumably the ``webapps/axis2`` of your Apache Tomcat installation). 
- Furthermore, you have to activate the EIGSecurityHandler in the **Global Modules** section of your axis2 configuration (``${AXIS2_HOME}/WEB-INF/conf/axis2.xml``) 
- You may configure the logging for the services in the Log4J configuration file (``${AXIS2_HOME}/WEB-INF/classes/log4j.properties``)  


Both, the Security Token Service and the PEP service make use of Java Keystores: The IDMS uses  Keystores to store a) the certificate used by the Security Token Service for signing SAML tokens and b) the public keys of those authenticating authorities trusted by the Policy Enforcement Point. The ``keytool`` of the Java distribution can be used to create and manipulate Java Keystores:

-  The following command creates a new Keystore with the password :secret: and a suitable key pair with the alias :authenticate: for the Security Token Service:
    ``keytool -genkey -alias authenticate -keyalg RSA -keystore keystore.jks -storepass secret -validity 360``
- The following command exports the public certificate from a key pair :authenticate: to the file ``authn.crt``
    ``keytool -export -alias authenticate -file authn.crt -keystore keystore.jks``
- The following command imports a certificate to a Keystore:
    ``keytool -import -alias trusted_sts -file authn.crt -keystore keystore.jks``
    
You can use the Apache HTTP Server as a proxy, it will enable your services running in Tomcat to be accessible over the Apache server. This can be usefull when your services have to be accessible over the HTTP standard port *80*:

- First you have to enable ``mod_proxy_ajp`` and ``mod_proxy``.
- Create a virtual host in your ``httpd.conf`` ::

    <VirtualHost *:80>
       ServerName server.example.com
    
       <Proxy *>
         AddDefaultCharset Off
         Order deny,allow
         Allow from all
       </Proxy>
    
       ProxyPass /services/AuthenticationService ajp://localhost:8009/axis2/services/AuthenticationService
       ProxyPassReverse /services/AuthenticationService ajp://localhost:8009/axis2/services/AuthenticationService 
       
    </VirtualHost>
  The ``ProxyPass`` and ``ProxyPassReverse`` have to point to your services. Please note that the Tomcat server hosting your services must have the AJP interface enabled.  
 

 
LDAP Directory
--------------
The IDMS uses a LDAP directory to store user data (attributes, passwords, etc). ou can use any directory implementation, supporting the Lightweight Directory Access Protocol (v3).

Known working implementations are:

* `Apache Directory Service <http://directory.apache.org/>`_
* `OpenLDAP <http://openldap.org>`_

A good graphical client for LDAP directories is the `Apache Directory Studio <http://directory.apache.org/studio/>`_.


Security Token Service
-----------------------

The Security Token Service (STS) is responsible for the authentication of users  and  is documented and specified in the OASIS `WS-Trust <http://docs.oasis-open.org/ws-sx/ws-trust/200512/ws-trust-1.3-os.html>`_ specification. The authentication assertion produced by the STS is formulated in the `Security Assertion Markup Language <http://www.oasis-open.org/committees/download.php/3406/oasis-sstc-saml-core-1.1.pdf>`_. A client trying to access a service secured by the IDMS has to embed this assertion in every service request.

The STS implementation used by the IDMS is the `HMA Authentication Service <http://wiki.services.eoportal.org/tiki-index.php?page=HMA+Authentication+Service>`_. Please refer to the documentation included in the ``\docs`` folder of the HMA Authentication Service package how to compile the service. This document will only deal on how to install the service. To deploy the service successfully, you first have to install and confugure an LDAP service. Then proceed with the following steps:

* Put the ``authentication_v2.1.aar`` folder in the ``${AXIS2_HOME}/WEB-INF/services/`` folder. The ``authentication_v2.1.aar`` folder contains all configuration files for the STS.
* The main configuration of the service takes place in the ``authentication-service.properties``
* Using the ``saml-ldap-attributes-mapping.properties``, you can map your LDAP attributes to SAML attributes if necessary. 
* You may configure the logging behaviour in the Log4J configuration file in ``authentication-service-log4j.properties``

Following properties can be set in the ``authentication-service.properties`` configuration file:

``LDAPURL``
    URL to the LDAP service.
``LDAPSearchContext``
    Search context for users.
``LDAPPrincipal``
    The *"user name"* used by the STS to access the LDAP service.
``LDAPCredentials`` 
    The password used in combination with ``LDAPPrincipal``
``KEYSTORE_LOCATION`` 
    Path to the Keystore file containing the certificate used for signing the SAML tokens.     
``KEYSTORE_PASSWORD``
    The keystore password. 
``AUTHENTICATION_CERTIFICATE_ALIAS``
    Alias of the keystore entry wich is used for signing the SAML tokens. 
``AUTHENTICATION_CERTIFICATE_PASSWORD``
    Password corresponding to the ``AUTHENTICATION_CERTIFICATE_ALIAS``
``CLIENT_CERTIFICATE_ALIASES`` 
    Comma serperated list with keystore aliases of trusted clients.
``SAML_TOKEN_EXPIRY_PERIOD`` 
    Defines how long a SAML token is valid.
``SAML_ASSERTION_ISSUER`` 
    SAML Token issure.
``SAML_ASSERTION_ID_PREFIX`` 
    SAML Token prefix.
``SAML_ASSERTION_NODE_NAMESPACE``
    Namespace for attribute assertions.
``ENCRYTION_ENABLE`` 
    Enables or disables encryption of SAML tokens.
``INCLUDE_CERTIFICATE``
    Enables or disables inclusion of SAML tokens.
``LOG4J_CONFIG_LOCATION`` 
    Path to the Log4J configuration file.


Authorisation Service
---------------------

The Authorisation Service is responsible for the authorisation of service requests. It makes use of `XACML <http://www.oasis-open.org/committees/xacml/#XACML20>`_, a XML based language for access policies. The Authorisation Service is part of the `CHAORN <http://www.enviromatics.net/charon/index.html>`_ project. 

The Authorisation Service relies on a MySQL database to store all XACML policies. So in order to install the Authorisation Service, you first need to prepare a MySQL database: 

* Install the MySQL database on your system
* Change the *root* password. You can use the command line for this:
    ``mysqladmin -u root password 'root' -p``  
* Run the SQL script bundel with the Authorisation Service in order to create the policy database 
    ``mysql -u root -h localhost -p < PolicyAuthorService.sql``

The Service needs the following additional dependencies in the ``${AXIS2_HOME}\lib`` folder:

- ``mysql-connector-java-5.1.6.jar``  
- ``spring-2.5.1.jar``

The next step is deploying the Authorisation Service, therefore extract the ZIP archive into the directory of your ``${AXIS2_HOME}``.

Now you have to configure the service. All configuration files are in the  ``${AXIS2_HOME}/WEB-INF/classes`` folder and its subfolders.

- Open the ``PolicyAuthorService.properties`` and change the ``axisURL`` parameter to the URL URL where you are actually deploying your service.
- You can change the database connection in the ``config/GeoPDP.xml`` configuration file if necessary. 
                          

Policy Enforcement Point Service
--------------------------------

The Policy Enforcement Point enforces the authorisation decisions made by the Authorisation Service. 

The next step is deploying the PEP Service, therefore extract the ZIP archive into the directory of your ``${AXIS2_HOME}``.

Now you have to configure the service. The configuration files are in the  ``${AXIS2_HOME}/WEB-INF/classes`` folder. Open the ``PEPConfiguration.xml`` to configure the service. The configuration file already contains documentation of the single elements.


SOAP Proxy
----------

The SOAP Proxy is used as a proxy for a secured service. This means a user client does not communicate directly with a secured service, instead it sends all requests to the proxy service.  

First, you have to generate the proxy service. In order to do this, open a shell and navigate to the ``${ProxyCodeGen_HOME}/bin`` directory. Run the script to generate the proxy service:

* Linux, Unices:
    ``./ProxyGen.sh -wsdl path/to/wsdl``
* Windows:
    ``.\ProxyGen.bat -wsdl path\to\wsdl``

The parameter ``-wsdl`` points to a file with the WSDL of the secured service.
 
After a successful service generation, the folder ``${ProxyCodeGen_HOME}/tmp/dist`` contains the new proxy service. Take the service zip and deploy it by unpacking its content to the ``${AXIS2_HOME}`` folder. 

Edit the ``ProxyConfiguration_${SERVICE_NAME}.xml`` to configure the service. The configuration file already contains documentation of the single elements.
 