.. EOxServer English Documentation Index file
  #-----------------------------------------------------------------------------
  # $Id: index.rst 1413 2012-03-02 17:41:31Z krauses $
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
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

.. _Identity Management System:

Identity Management System
===========================

.. contents:: Table of Contents
    :depth: 4
    :backlinks: top

The Identity Management System (IDMS) provides access control capabilities for 
security relevant data. The current IDMS supports EOxServer with a native 
security component for HTTP KVP and POST/XML protocol binding as well as 
external components for SOAP binding. The system is based on other free and 
open software projects, namely the `Charon Project 
<http://www.enviromatics.net/charon/>`_, the `Shibboleth 
framwork <http://shibboleth.internet2.edu/>`_ and  the `HMA Authentication 
Service <http://wiki.services.eoportal.org/tiki-index.php?page=HMA+
Authentication+Service>`_. In the context of EOxServer, the SOAP support in the 
IDMS can be used to provide authentication and authorisation capabilities for 
the `EO-WCS SOAP Proxy <http://eoxserver.org/doc/en/users/soap_proxy.html>`_. 

The IDMS uses two different schemes for authentication: The native EOxServer 
component relies on Shibboleth for Authentication, the SOAP components use the 
Charon framework. 

The approach chosen for the SOAP part of the IDMS follows the OGC best practice 
document `User Management Interfaces for Earth Observation Services 
<http://portal.opengeospatial.org/files/?artifact_id=40677>`_ for the 
authentication concept. The authentication part is following the ideas of the 
`XACML data flow pattern <http://docs.oasis-open.org/xacml/2.0/access_control-
xacml-2.0-core-spec-os.pdf>`_: The IDMS authorisation part consists of a Policy 
Decision Point (PDP, here represented through the Charon Policy Management And 
Authentication Service) and the Policy Enforcement Point (PEP, represented 
through the Charon PEP Service). The following figure gives an overview of the 
IDMS SOAP part:

.. figure:: images/IDM_SOAP_Components.png
   :align: center

   *IDMS SOAP Access Control Overview*

The HMA Authentication Service, or Security Token Service (STS), and the Charon 
PEP components were both modified in order to be compatible. This is a result 
of the ESA project `Open-standard Online Observation Service 
<http://wiki.services.eoportal.org/tiki-index.php?page=O3S>`_ (O3S). The STS 
now also supports SAML 2.0 security tokens, which the PEP components can 
interpret and validate. The IDMS supports trust relationships between identity 
providers and enforcement components on the basis of certificate stores.


The HTTP or native EOxServer part of the IDMS uses exactly the same scheme for 
authorisation as the SOAP part, but uses the Shibboleth federated identity 
management system for authentication.

.. figure:: images/IDM_HTTP_Components.png
   :align: center
   
   *IDMS EOxServer Access Control Overview* 

Two requirements must be met to use the IDMS in this case:

* A Shibboleth Identity Provider (IdP) must be available for authentication
* A Shibboleth Service Provider (SP) must be installed and configured in an 
  `Apache HTTP Server <http://httpd.apache.org/>`_ to protect the EOxServer 
  resource.

A user has to authenticate at an IdP in order to perform requests to an 
EOxServer with access control enabled. The IdP issues a SAML token which will 
be validated by the SP.

Is the user valid, the SP adds the user attributes received from the IdP to the 
HTTP Header of the original service requests and conveys it to the protected 
EOxServer instance. The whole process ensures, that only authenticated users 
can access the data and services provided by EOxServer. The attributes from 
Shibboleth are used by the EOxServer security components to make a 
XACMLAuthzDecisionQuery to the Charon Authorisation Service.

Installation and Configuration
==============================

The following services are needed for the both the HTTP and SOAP security part:

* Charon :ref:`Authorisation_Service`.
* :ref:`LDAP_Directory`.

For the installation and configuration please refere to the SOAP or HTTP specific 
documentation:

.. toctree::
   :maxdepth: 1
   
   http
   soap

   
Prerequisites
-------------

Download locations for the IDMS components:

* Shibboleth: http://shibboleth.internet2.edu/downloads.html
* CHARON Authorisation Service: http://www.enviromatics.net/charon/ or http://eox.at 
* Security Token Service: http://eox.at    
* PEP Service: http://eox.at 
* EOxServer: http://eoxserver.org/wiki/Download


The following software is needed to run the IDMS:  

-  A :ref:`LDAP_Directory`.
- `Java <http://www.oracle.com/technetwork/java/index.html>`_ JDK 6 or higher 
- `Apache Tomcat <http://tomcat.apache.org/>`_ 6 or higher
- `Apache Axis2 <http://axis.apache.org/axis2/java/core/>`_ 1.4.1 or higher
- `MySQL <http://dev.mysql.com/downloads/>`_ 5 
- `Apache HTTP Server <http://httpd.apache.org/>`_ 2.x


The following software is needed to build the IDMS components:

- `Java <http://www.oracle.com/technetwork/java/index.html>`_  SDK 6 or higher
- `Apache Ant <http://ant.apache.org/>`_ 1.6.2 or higher
- `Apache Maven <http://maven.apache.org/>`_ 2 or higher


.. _LDAP_Directory:

LDAP Directory
--------------
The IDMS uses a LDAP directory to store user data (attributes, passwords, etc). 
You can use any directory implementation, supporting the Lightweight Directory 
Access Protocol (v3).

Known working implementations are:

* `Apache Directory Service <http://directory.apache.org/>`_
* `OpenLDAP <http://openldap.org>`_

A good graphical client for LDAP directories is the `Apache Directory Studio 
<http://directory.apache.org/studio/>`_.



.. _Authorisation_Service: 
 
Authorisation Service
---------------------

Before installing the Authorsation Service, refer to the :ref:`CHARON_Configuration`.

The Authorisation Service is responsible for the authorisation of service 
requests. It makes use of `XACML <http://www.oasis-open.org/committees/xacml/
#XACML20>`_, a XML based language for access policies. The Authorisation 
Service is part of the `CHAORN <http://www.enviromatics.net/charon/index.html>`_
project. 

The Authorisation Service relies on a MySQL database to store all XACML 
policies. So in order to install the Authorisation Service, you first need to 
prepare a MySQL database: 

* Install the MySQL database on your system.
* Change the *root* password. You can use the command line for this:

    ``mysqladmin -u root password 'root' -p``

* Run the SQL script bundle with the Authorisation Service in order to create 
  the policy database:

    ``mysql -u root -h localhost -p < PolicyAuthorService.sql``

The Service needs the following additional dependencies in the 
``${AXIS2_HOME}\lib`` folder:

- ``mysql-connector-java-5.1.6.jar``
- ``spring-2.5.1.jar``

The next step is deploying the Authorisation Service, therefore extract the ZIP 
archive into the directory of your ``${AXIS2_HOME}``.

Now you have to configure the service. All configuration files are in the 
``${AXIS2_HOME}/WEB-INF/classes`` folder and its sub-folders.

- Open the ``PolicyAuthorService.properties`` and change the ``axisURL`` 
  parameter to the URL URL where you are actually deploying your service.
- You can change the database connection in the ``config/GeoPDP.xml`` 
  configuration file if necessary. 

To add new XACML policies to the Authorisation Service, refer to the :ref:`XACML `.

.. _XACML:    

XACML Policies for the Authorisation Service
````````````````````````````````````````````

As mentioned before, the Charon Authorisation Service uses a MySQL database
to store all XACML policies. The policies are stored in the database 
``policy_author`` and the table ``policy``. To add new policies, use an SQL client 

.. code-block:: sql

	INSERT INTO policy(policy) VALUES (' your xacml policy')


An XACML policy usually consists of a policy wide target and and several specific rules. 
The three main identifiers are subjects, targets and actions. Subjects (or users) can be
identified through the "asserted user attributes" which are provided by the Shibboleth framework. 
The EOxServer security components also provide an attribute ``REMOTE_ADDR`` for subjects, 
which contains the IP address of the user. The resource is mainly identified through the attribute  
``urn:oasis:names:tc:xacml:1.0:resource:resource-id``, which is the service address of the secured 
service in case of an secured SOAP service and the host name or a ID set in the configuration in case of 
the EOxServer. The EOxServer also provides the atributes serverName (the host name) and serviceType 
(type of the service, i.e. wcs or wms). The action identifies the operation performed on the service, i.e. 
``getcapabilities`` or ``getcoverage``. In the following there are two example policies for the EOxServer 
WMS and WCS. Please note the comments inline.

A XACML policy to permit a user "wms_user" full accesss to the EOxServer WMS:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<Policy 
	    xsi:schemalocation="urn:oasis:names:tc:xacml:2.0:policy:schema:os http://docs.oasis-open.org/xacml/access_control-xacml-2.0-policy-schema-os.xsd" 
	    PolicyId="wms_user_policy" 
	    RuleCombiningAlgId="urn:oasis:names:tc:xacml:1.0:rule-combining-algorithm:permit-overrides" 
	    xmlns="urn:oasis:names:tc:xacml:2.0:policy:schema:os" 
	    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
	    xmlns:ns="http://www.enviromatics.net/WS/PolicyManagementAndAuthorisationService/types /2.0">
	    
	    <Target>
		<Subjects>
		    <Subject>
			<!-- Here we specify the user who has access to the service. Default identifier is the uid attribute -->
			<SubjectMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
			    <AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">wms_user</AttributeValue>
			    <SubjectAttributeDesignator DataType="http://www.w3.org/2001/XMLSchema#string" AttributeId="uid"/>
			</SubjectMatch>
		    </Subject>
		</Subjects>
		<Resources>
		    <Resource>
			<!-- The attribute urn:oasis:names:tc:xacml:1.0:resource:resource-id specifies the protected server (default is the hostname) -->
			<ResourceMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
			    <AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">eoxserver.example.com</AttributeValue>
			    <ResourceAttributeDesignator DataType="http://www.w3.org/2001/XMLSchema#string" AttributeId="urn:oasis:names:tc:xacml:1.0:resource:resource-id"/>
			</ResourceMatch>
			
			<!-- The attribute serviceType specifies the protected service (wms or wcs) -->
			<ResourceMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
			    <AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">wms</AttributeValue>
			    <ResourceAttributeDesignator DataType="http://www.w3.org/2001/XMLSchema#string" AttributeId="serviceType"/>
			</ResourceMatch>                
		    </Resource>
		</Resources>
	    </Target>
	    
	    
	    <!-- 
		In the following rules we allow the specified user to perform selected operations 
		on the service. 
	    -->
	    
	    <!-- 
		GetCapabilities
	    -->
	    
	    
	    <Rule RuleId="PermitGetCapabilitiesCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetCapabilities</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="PermitGetCapabilitiesSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getcapabilities</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		GetMap
	    -->
	    
	    <Rule RuleId="GetMapCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetMap</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="GetMapSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getmap</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		GetFeatureInfo
	    -->
	    
	    <Rule RuleId="GetFeatureInfoCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetFeatureInfo</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="GetFeatureInfoSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getfeatureinfo</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		DescribeLayer
	    -->
	    
	    <Rule RuleId="DescribeLayerCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">DescribeLayer</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="DescribeLayerSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">describelayer</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		GetLegendGraphic
	    -->
	    
	    <Rule RuleId="GetLegendGraphicCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetLegendGraphic</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="GetLegendGraphicSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getlegendgraphic</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		GetStyles
	    -->
	    
	    <Rule RuleId="GetStylesCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetStyles</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="GetStylesSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getstyles</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>

	</Policy>
	

A XACML policy to permit a user "wcs_user" full accesss to the EOxServer WCS:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<Policy 
	    xsi:schemalocation="urn:oasis:names:tc:xacml:2.0:policy:schema:os http://docs.oasis-open.org/xacml/access_control-xacml-2.0-policy-schema-os.xsd" 
	    PolicyId="wcs_user_policy" 
	    RuleCombiningAlgId="urn:oasis:names:tc:xacml:1.0:rule-combining-algorithm:permit-overrides" 
	    xmlns="urn:oasis:names:tc:xacml:2.0:policy:schema:os" 
	    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
	    xmlns:ns="http://www.enviromatics.net/WS/PolicyManagementAndAuthorisationService/types /2.0">
	    
	    <Target>
		<Subjects>
		    <Subject>
			<!-- Here we specify the user who has access to the service. Default identifier is the uid attribute -->
			<SubjectMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
			    <AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">wcs_user</AttributeValue>
			    <SubjectAttributeDesignator DataType="http://www.w3.org/2001/XMLSchema#string" AttributeId="uid"/>
			</SubjectMatch>
		    </Subject>
		</Subjects>
		<Resources>
		    <Resource>		    
			<!-- The attribute urn:oasis:names:tc:xacml:1.0:resource:resource-id specifies the protected server (default is the hostname) -->
			<ResourceMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
			    <AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">eoxserver.example.com</AttributeValue>
			    <ResourceAttributeDesignator DataType="http://www.w3.org/2001/XMLSchema#string" AttributeId="urn:oasis:names:tc:xacml:1.0:resource:resource-id"/>
			</ResourceMatch>
			
			<!-- The attribute serviceType specifies the protected service (wms or wcs) -->
			<ResourceMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
			    <AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">wcs</AttributeValue>
			    <ResourceAttributeDesignator DataType="http://www.w3.org/2001/XMLSchema#string" AttributeId="serviceType"/>
			</ResourceMatch>
		    </Resource>
		</Resources>
	    </Target>
	    
	    
	    
	    <!-- 
		GetCapabilities
	    -->
	    
	    <Rule RuleId="PermitGetCapabilitiesCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetCapabilities</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="PermitGetCapabilitiesSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getcapabilities</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		DescribeCoverage
	    -->
	    
	    <Rule RuleId="DescribeCoverageCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">DescribeCoverage</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="DescribeCoverageSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">describecoverage</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		GetCoverage
	    -->
	    
	    <Rule RuleId="DescribeCoverageCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">GetCoverage</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="GetCoverageSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">getcoverage</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <!-- 
		DescribeEOCoverageSet
	    -->
	    
	    <Rule RuleId="DescribeEOCoverageSetCC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">DescribeEOCoverageSet</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>
	    
	    <Rule RuleId="DescribeEOCoverageSetSC" Effect="Permit">
		<Target>
		    <Actions>
			<Action>
			    <ActionMatch MatchId="urn:oasis:names:tc:xacml:1.0:function:string-equal">
				<AttributeValue DataType="http://www.w3.org/2001/XMLSchema#string">describeeocoverageset</AttributeValue>
				<ActionAttributeDesignator AttributeId="urn:oasis:names:tc:xacml:1.0:action:action" DataType="http://www.w3.org/2001/XMLSchema#string"/>
			    </ActionMatch>
			</Action>
		    </Actions>
		</Target>
	    </Rule>

	</Policy>
 



.. _CHARON_Configuration:

General Configuration for CHARON services
-----------------------------------------

- The Charon services need the ``acs-xbeans-1.0.jar`` dependency in the 
  ``\lib`` folder of your Axis2 installation (presumably the ``webapps/axis2`` 
  of your Apache Tomcat installation).
- Furthermore, you have to activate the EIGSecurityHandler in the 
  **Global Modules** section of your axis2 configuration 
  (``${AXIS2_HOME}/WEB-INF/conf/axis2.xml``).
- You may configure the logging for the services in the Log4J configuration 
  file (``${AXIS2_HOME}/WEB-INF/classes/log4j.properties``).


Both, the Security Token Service and the PEP service make use of Java 
Keystores: The IDMS uses  Keystores to store a) the certificate used by the 
Security Token Service for signing SAML tokens and b) the public keys of those 
authenticating authorities trusted by the Policy Enforcement Point. The 
``keytool`` of the Java distribution can be used to create and manipulate 
Java Keystores:

- The following command creates a new Keystore with the password :secret: and 
  a suitable key pair with the alias :authenticate: for the Security Token 
  Service:
  
    ``keytool -genkey -alias authenticate -keyalg RSA -keystore keystore.jks 
    -storepass secret -validity 360``

- The following command exports the public certificate from a key pair 
  :authenticate: to the file ``authn.crt``:
  
    ``keytool -export -alias authenticate -file authn.crt -keystore 
    keystore.jks``

- The following command imports a certificate to a Keystore:

    ``keytool -import -alias trusted_sts -file authn.crt -keystore 
    keystore.jks``

You can use the Apache HTTP Server as a proxy, it will enable your services 
running in Tomcat to be accessible over the Apache server. This can be useful 
when your services have to be accessible over the HTTP standard port *80*:

- First you have to enable ``mod_proxy_ajp`` and ``mod_proxy``.
- Create a virtual host in your ``httpd.conf``:

    .. code-block:: apache

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

- The ``ProxyPass`` and ``ProxyPassReverse`` directives have to point to your 
  services. Please note that the Tomcat server hosting your services must have 
  the AJP interface enabled.  
