.. Identity Management System
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Arndt Bonitz <arndt.bonitz@ait.ac.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 AIT Austrian Institute of Technology GmbH
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

.. _Identity Management System SOAP:

Identity Management System: SOAP Components
===========================================

.. contents:: Table of Contents
    :depth: 4
    :backlinks: top


Components
----------

The following services are needed for the SOAP security part:

* Security Token Service
* Charon Authorisation Service
* Policy Enforcement Point Service
* SOAP Security Proxy


To install and configure the HTTP secuirty components, you have to follow these 
steps:

#. Install the Charon :ref:`Authorisation_Service`.
#. Install the :ref:`STS`.
#. Install the :ref:`PEP`.
#. Install the :ref:`SecProxy`.


.. _STS:

Security Token Service
-----------------------

The Security Token Service (STS) is responsible for the authentication of users 
and is documented and specified in the OASIS `WS-Trust 
<http://docs.oasis-open.org/ws-sx/ws-trust/200512/ws-trust-1.3-os.html>`_ 
specification. The authentication assertion produced by the STS is formulated 
in the `Security Assertion Markup Language <http://www.oasis-open.org/committees
/download.php/3406/oasis-sstc-saml-core-1.1.pdf>`_. A client trying to access a 
service secured by the IDMS has to embed this assertion in every service 
request.

The STS implementation used by the IDMS is the `HMA Authentication Service 
<http://wiki.services.eoportal.org/tiki-index.php?page=HMA+Authentication+
Service>`_. Please refer to the documentation included in the ``\docs`` folder 
of the HMA Authentication Service package how to compile the service. This 
document will only deal on how to install the service. To deploy the service 
successfully, you first have to install and configure an LDAP service. Then 
proceed with the following steps:

* Put the ``authentication_v2.1.aar`` folder in the 
  ``${AXIS2_HOME}/WEB-INF/services/`` folder. The ``authentication_v2.1.aar`` 
  folder contains all configuration files for the STS.
* The main configuration of the service takes place in the 
  ``authentication-service.properties``.
* Using the ``saml-ldap-attributes-mapping.properties``, you can map your LDAP 
  attributes to SAML attributes if necessary. 
* You may configure the logging behaviour in the Log4J configuration file in 
  ``authentication-service-log4j.properties``.

Following properties can be set in the ``authentication-service.properties`` 
configuration file:

``LDAPURL``
    URL to the LDAP service.
``LDAPSearchContext``
    Search context for users.
``LDAPPrincipal``
    The *"user name"* used by the STS to access the LDAP service.
``LDAPCredentials`` 
    The password used in combination with ``LDAPPrincipal``
``KEYSTORE_LOCATION`` 
    Path to the Keystore file containing the certificate used for signing the 
    SAML tokens.
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



.. _PEP:

Policy Enforcement Point Service
--------------------------------

Before installing the Policy Enforcement Point Service, refer to the 
:ref:`CHARON_Configuration`.

The Policy Enforcement Point enforces the authorisation decisions made by the 
Authorisation Service. 

The next step is deploying the PEP Service, therefore extract the ZIP archive 
into the directory of your ``${AXIS2_HOME}``.

Now you have to configure the service. The configuration files are in the 
``${AXIS2_HOME}/WEB-INF/classes`` folder. Open the ``PEPConfiguration.xml`` to 
configure the service. The configuration file already contains documentation of 
the single elements.


.. _SecProxy:

SOAP Security Proxy
-------------------

Before installing the SOAP Security Proxy, refer to the :ref:`CHARON_Configuration`.
If you want to secure a Web Coverage Service, you can use the provided WCS Security
Proxy. In this case, jump to :ref:`InstallSecProxy`.


.. _GenerateSecProxy:

Generating the Proxy
````````````````````

The SOAP Proxy is used as a proxy for a secured service. This means a user 
client does not communicate directly with a secured service, instead it sends 
all requests to the proxy service.  

First, you have to generate the proxy service. In order to do this, open a 
shell and navigate to the ``${ProxyCodeGen_HOME}/bin`` directory. Run the 
script to generate the proxy service:

* Linux, Unices:

    ``./ProxyGen.sh -wsdl path/to/wsdl``

* Windows:

    ``.\ProxyGen.bat -wsdl path\to\wsdl``

The parameter ``-wsdl`` points to a file with the WSDL of the secured service.
 
After a successful service generation, the folder ``${ProxyCodeGen_HOME}/tmp/
dist`` contains the new proxy service. 


.. _InstallSecProxy:

Installing the Proxy
````````````````````   

Take the service zip and deploy it by unpacking its content to the ``${AXIS2_HOME}`` 
folder. For MTOM support, please make sure that the parameter ``enableMTOM`` in 
the file ``${AXIS2_HOME}/axis2.xml`` is enabled.

Edit the ``ProxyConfiguration_${SERVICE_NAME}.xml`` to configure the service. 
The configuration file already contains documentation of the single elements.





