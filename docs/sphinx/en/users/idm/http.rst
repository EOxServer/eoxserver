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

.. _Identity Management System HTTP:

Identity Management System: HTTP Components
===========================================

.. contents:: Table of Contents
    :depth: 4
    :backlinks: top


The following services are needed for the HTTP security part:

* Charon Authorisation Service
* Shibboleth Service Provider
* Shibboleth Identity Provider
* EOxServer


To install and configure the HTTP secuirty components, you have to follow these 
steps:

#. Install the Charon :ref:`Authorisation_Service`.
#. Install the :ref:`IdP`.
#. Install the :ref:`SP`.
#. Follow the documentation of section :ref:`SP_IdP`.
#. Follow the documentation of section :ref:`EOxServer_SecConfig`.


.. _IdP:

Shibboleth Identity Provider
----------------------------

The Shibboleth IdP is implemented as an Java Servlet, thus it needs an 
installed Servlet container. The Shibboleth project offers `an installation 
manual for the Shibboleth IdP on their website <https://wiki.shibboleth.net/
confluence/display/SHIB2/IdPInstall>`_. This documentation will provide help 
for the basic configuration to get the authentication process working with your 
EOxServer instance and also the installation process for the use with Tomcat 
and Apache HTTPD. Before you begin with your installation, set up your Tomcat 
servlet container and install and configure an LDAP service.

Important URLs for your Shibboleth IDP:
 
- Status message: ``https://${IDPHOST}/idp/profile/Status``
- Information page: ``https://${IDPHOST}/idp/status``
- Metadata: ``https://${IDPHOST}/idp/profile/Metadata/SAML`` 

`Warning: IdP resource paths are case sensitive!`


* `Download <http://shibboleth.internet2.edu/downloads.html>`_ the IdP and 
  unzip the archive.
* Run either ./install.sh (on Linxu/Unix systems) or install.bat (on Windows 
  systems).
* Follow the on-screen instructions of the script. 

Your ``${IDP_HOME}`` directory contains the following directories:

* ``bin``:  This directory contains various tools useful in running, testing, 
  or deploying the IdP
* ``conf``: This directory contains all the configuration files for the IdP
* ``credentials``: This is were the IdP's signing and encryption credential, 
  called idp.key and idp.crt, is stored
* ``lib``: This directory contains various code libraries used by the tools in 
  bin/
* ``logs``: This directory contains the log files for the IdP . **Don't forget 
  to make this writeable for your Tomcat server!** 
* ``metadata``: This is the directory in which the IdP will store its metadata, 
  in a file called idp-metadata.xml. It is recommend you store any other 
  retrieved metadata here as well.
* ``war``: This contains the web application archive (war) file that you will 
  deploy into the servlet container

The next step is to deploy the IdP into your Tomcat:

* Increase the memory reserved for Tomcat. Recommended values are 
  ``-Xmx512m -XX:MaxPermSize=128m``.
* Add the libraries endorsed by the Shibboleth project to your endorsed Tomcat 
  directories: ``-Djava.endorsed.dirs=${IDP_HOME}/lib/endorsed/`` 
* Create a new XML document ``idp.xml`` in ``${TOMCAT_HOME}/conf/Catalina/
  localhost/``.
* Insert the following content:  

    .. code-block:: xml

        <Context docBase="${IDP_HOME}/war/idp.war"
                 privileged="true"
                 antiResourceLocking="false"
                 antiJARLocking="false"
                 unpackWAR="false"
                 swallowOutput="true" />                  

* Dont't forget to replace ``${IDP_HOME}`` with the appropriate path. 

To use the Apache HTTP server as an proxy for your IdP, you have to generate a 
certificate and a key file for SSL/TLS first. 

* Generate a private key:

    ``openssl genrsa -des3 -out server.key 1024``

* Generate a CSR (Certificate Signing Request):

    ``openssl req -new -key server.key -out server.csr``

* Make a copy from the the original server key:

    ``cp server.key copy_of_server.key``

* Remove the Passphrase from your Key:

    ``openssl rsa -in copy_of_server.key -out server.key``

* Generating a Self-Signed Certificate:

    ``openssl x509 -req -days 365 -in server.csr -signkey server.key -out 
    server.crt``

The next step is to configure your Apache HTTP Server:

- First you have to enable ``mod_proxy_ajp``, ``mod_proxy`` and ``mod_ssl``.
- Create a new configuration file for your SSL hosts (for example 
  ``ssl_hosts.conf``).
- Add a new virtual host in your new hosts file. Please note the comments in 
  the virtual host configuration. 

    .. code-block:: apache

        <VirtualHost _default_:443>

            # Set appropriate document root here
            DocumentRoot "/var/www/"
            
            # Set your designated IDP host here    
            ServerName ${IDP_HOST} 

            # Set your designated logging directory here
            ErrorLog logs/ssl_error_log
            TransferLog logs/ssl_access_log
            LogLevel warn

            SSLEngine on

            SSLProtocol all -SSLv2

             # Important: mod_ssl should not verify the provided certificates
            SSLVerifyClient optional_no_ca

            SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW

            # Set the correct paths to your certificate and key here
            SSLCertificateFile    ${IDP_HOST_CERTIFICATE} 
            SSLCertificateKeyFile ${IDP_HOST_CERTIFICATE_KEY} 

            <Files ~ "\.(cgi|shtml|phtml|php3?)$">
                SSLOptions +StdEnvVars
            </Files>
            <Directory "/var/www/cgi-bin">
                SSLOptions +StdEnvVars
            </Directory>

            # AJP Proxy to your IDP servlet
            ProxyPass /idp/ ajp://localhost:8009/idp/ 
            ProxyPassReverse /idp ajp://localhost:8009/idp

            SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown downgrade-1.0 force-response-1.0

            CustomLog logs/ssl_request_log "%t %h %{SSL_PROTOCOL}x %{SSL_CIPHER}x \"%r\" %b"

        </VirtualHost>

- Restart your HTTP server.
 
The next step is to configure our IdP Service with an LDAP service. Please keep 
in mind that this documentation can only give a small insight into all 
configuration possibilities of Shibboleth. 

Open the ``handler.xml``

* Add a new LoginHandler

    .. code-block:: xml

        <LoginHandler xsi:type="UsernamePassword" 
                      jaasConfigurationLocation="file://${IDP_HOME}/conf/login.config">
                      <AuthenticationMethod>urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport</AuthenticationMethod>
        </LoginHandler>

* Remove (or comment out) the LoginHandler element of type RemoteUser.

Open the ``login.config`` and comment out or delete the other entries that 
might exist. Add your own LDAP configuration::

    ShibUserPassAuth {    
      edu.vt.middleware.ldap.jaas.LdapLoginModule required
         host="${LDAP_HOST}"
         port="${LDAP_PORT}"
         serviceUser="${LDAP_ADMIN}"
         serviceCredential="${LDAP_ADMIN_PASSWORD}"
         base="${LDAP_USER_BASE}"
         ssl="false"
         userField="uid"
         subtreeSearch="true";      
    };

Enable your LDAP directory as attribute provider:

* Open the ``attribute-resolver.xml``.
* Add your LDAP: 

    .. code-block:: xml

        <resolver:DataConnector id="localLDAP" xsi:type="LDAPDirectory" 
                  xmlns="urn:mace:shibboleth:2.0:resolver:dc" ldapURL="ldap://${LDAP_HOST}:${LDAP_PORT}" 
                  baseDN="${LDAP_USER_BASE}" principal="${LDAP_ADMIN}" 
                  principalCredential="${LDAP_ADMIN_PASSWORD}">
        <FilterTemplate>
            <![CDATA[ 
                  (uid=$requestContext.principalName) 
            ]]> 
        </FilterTemplate> 
        </resolver:DataConnector>

* Configure the IdP to retrieve the attributes by adding new attribute 
  definitions:

    .. code-block:: xml

        <resolver:AttributeDefinition id="transientId" xsi:type="ad:TransientId">
            <resolver:AttributeEncoder xsi:type="enc:SAML1StringNameIdentifier"
                nameFormat="urn:mace:shibboleth:1.0:nameIdentifier"/>
            <resolver:AttributeEncoder xsi:type="enc:SAML2StringNameID"
                nameFormat="urn:oasis:names:tc:SAML:2.0:nameid-format:transient"/>
        </resolver:AttributeDefinition>

        <resolver:AttributeDefinition id="displayName" xsi:type="Simple"
            xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="displayName">
            <resolver:Dependency ref="localLDAP"/>
            <resolver:AttributeEncoder xsi:type="SAML1String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder"
                name="urn:mace:dir:attribute-def:displayName"/>
            <resolver:AttributeEncoder xsi:type="SAML2String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder"
                name="urn:oid:2.16.840.1.113730.3.1.241" friendlyName="displayName"/>
        </resolver:AttributeDefinition>

        <resolver:AttributeDefinition id="givenName" xsi:type="Simple"
            xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="givenName">
            <resolver:Dependency ref="localLDAP"/>
            <resolver:AttributeEncoder xsi:type="SAML1String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder"
                name="urn:mace:dir:attribute-def:givenName"/>
            <resolver:AttributeEncoder xsi:type="SAML2String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:oid:2.5.4.42"
                friendlyName="givenName"/>
        </resolver:AttributeDefinition>

        <resolver:AttributeDefinition id="description" xsi:type="Simple"
            xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="description">
            <resolver:Dependency ref="localLDAP"/>
            <resolver:AttributeEncoder xsi:type="SAML1String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder"
                name="urn:mace:dir:attribute-def:description"/>
            <resolver:AttributeEncoder xsi:type="SAML2String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:oid:2.5.4.13"
                friendlyName="description"/>
        </resolver:AttributeDefinition>

        <resolver:AttributeDefinition id="cn" xsi:type="Simple"
            xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="cn">
            <resolver:Dependency ref="localLDAP"/>
            <resolver:AttributeEncoder xsi:type="SAML1String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:mace:dir:attribute-def:cn"/>
            <resolver:AttributeEncoder xsi:type="SAML2String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:oid:2.5.4.3"
                friendlyName="cn"/>
        </resolver:AttributeDefinition>

        <resolver:AttributeDefinition id="sn" xsi:type="Simple"
            xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="sn">
            <resolver:Dependency ref="localLDAP"/>
            <resolver:AttributeEncoder xsi:type="SAML1String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:mace:dir:attribute-def:sn"/>
            <resolver:AttributeEncoder xsi:type="SAML2String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:oid:2.5.4.4"
                friendlyName="sn"/>
        </resolver:AttributeDefinition>

        <resolver:AttributeDefinition id="uid" xsi:type="Simple"
            xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="uid">
            <resolver:Dependency ref="localLDAP"/>
            <resolver:AttributeEncoder xsi:type="SAML1String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:mace:dir:attribute-def:uid"/>
            <resolver:AttributeEncoder xsi:type="SAML2String"
                xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="urn:oid:2.5.4.45"
                friendlyName="uid"/>
        </resolver:AttributeDefinition>

Add the new attributes to your ``attribute-filter.xml`` by adding a new 
AttributeFilterPolicy: 

.. code-block:: xml 
   
    <afp:AttributeFilterPolicy id="attribFilter">
        <afp:PolicyRequirementRule xsi:type="basic:ANY"/>

        <afp:AttributeRule attributeID="givenName">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>

        <afp:AttributeRule attributeID="displayName">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>

        <afp:AttributeRule attributeID="description">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>

        <afp:AttributeRule attributeID="cn">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>

        <afp:AttributeRule attributeID="sn">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>

        <afp:AttributeRule attributeID="uid">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>

    </afp:AttributeFilterPolicy>

Now you have to check if the generated metadata is correct. To do this, open 
the ``idp-metadata.xml`` file. Known issues are:

* Incorrect ports: For example port 8443 at the AttributeService Bindings 
  instead of no specific port.
* Wrong X509Certificate for Attribute Resolver. Use your previously generated 
  SSL/TLS ``${IDP_HOST_CERTIFICATE}`` instead.     

After this, restart your Shibboleth IdP.


.. _SP:

Shibboleth Service Provider
---------------------------

The installation procedure for the Shibboleth SP is different for all 
supported Operating Systems. The project describes the different installation 
methods in an `own installation manual <https://wiki.shibboleth.net/confluence/
display/SHIB2/Installation>`_. This documentation will provide help for the 
basic configuration to get the authentication process working with your 
EOxServer instance. 

Important URLs for your Shibboleth SP:
 
- Status page: ``https://${SPHOST}/Shibboleth.sso/Status``
- Metadata: ``https://${SPHOST}/Shibboleth.sso/Metadata``
- Session summary: ``https://${SPHOST}/Shibboleth.sso/Session``
- Local logout: ``https://${SPHOST}/Shibboleth.sso/Logout`` 

`Warning: SP resource paths are case sensitive!`


**STEP 1**

The Shibboleth SP has two relevant configuration files. We begin with the 
``attribute-map.xml`` file, where we configure the mapping of the attributes 
received from the IdP to the secured service (in our case the EOxServer): 

.. code-block:: xml

    <Attributes xmlns="urn:mace:shibboleth:2.0:attribute-map" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    
        <!-- First some useful eduPerson attributes that many sites might use. -->
        
        <Attribute name="urn:mace:dir:attribute-def:eduPersonPrincipalName" id="eppn">
            <AttributeDecoder xsi:type="ScopedAttributeDecoder"/>
        </Attribute>
        <Attribute name="urn:oid:1.3.6.1.4.1.5923.1.1.1.6" id="eppn">
            <AttributeDecoder xsi:type="ScopedAttributeDecoder"/>
        </Attribute>
        
        <Attribute name="urn:mace:dir:attribute-def:eduPersonScopedAffiliation" id="affiliation">
            <AttributeDecoder xsi:type="ScopedAttributeDecoder" caseSensitive="false"/>
        </Attribute>
        <Attribute name="urn:oid:1.3.6.1.4.1.5923.1.1.1.9" id="affiliation">
            <AttributeDecoder xsi:type="ScopedAttributeDecoder" caseSensitive="false"/>
        </Attribute>
        
        <Attribute name="urn:mace:dir:attribute-def:eduPersonAffiliation" id="unscoped-affiliation">
            <AttributeDecoder xsi:type="StringAttributeDecoder" caseSensitive="false"/>
        </Attribute>
        <Attribute name="urn:oid:1.3.6.1.4.1.5923.1.1.1.1" id="unscoped-affiliation">
            <AttributeDecoder xsi:type="StringAttributeDecoder" caseSensitive="false"/>
        </Attribute>
        
        <Attribute name="urn:mace:dir:attribute-def:eduPersonEntitlement" id="entitlement"/>
        <Attribute name="urn:oid:1.3.6.1.4.1.5923.1.1.1.7" id="entitlement"/>
    
        <!-- A persistent id attribute that supports personalized anonymous access. -->
        
        <!-- First, the deprecated/incorrect version, decoded as a scoped string: -->
        <Attribute name="urn:mace:dir:attribute-def:eduPersonTargetedID" id="targeted-id">
            <AttributeDecoder xsi:type="ScopedAttributeDecoder"/>
            <!-- <AttributeDecoder xsi:type="NameIDFromScopedAttributeDecoder" formatter="$NameQualifier!$SPNameQualifier!$Name" defaultQualifiers="true"/> -->
        </Attribute>
        
        <!-- Second, an alternate decoder that will decode the incorrect form into the newer form. -->
        <!--
        <Attribute name="urn:mace:dir:attribute-def:eduPersonTargetedID" id="persistent-id">
            <AttributeDecoder xsi:type="NameIDFromScopedAttributeDecoder" formatter="$NameQualifier!$SPNameQualifier!$Name" defaultQualifiers="true"/>
        </Attribute>
        -->
        
        <!-- Third, the new version (note the OID-style name): -->
        <Attribute name="urn:oid:1.3.6.1.4.1.5923.1.1.1.10" id="persistent-id">
            <AttributeDecoder xsi:type="NameIDAttributeDecoder" formatter="$NameQualifier!$SPNameQualifier!$Name" defaultQualifiers="true"/>
        </Attribute>
    
        <!-- Fourth, the SAML 2.0 NameID Format: -->
        <Attribute name="urn:oasis:names:tc:SAML:2.0:nameid-format:persistent" id="persistent-id">
            <AttributeDecoder xsi:type="NameIDAttributeDecoder" formatter="$NameQualifier!$SPNameQualifier!$Name" defaultQualifiers="true"/>
        </Attribute>
        
        <!--Examples of LDAP-based attributes, uncomment to use these... -->
        <Attribute name="urn:mace:dir:attribute-def:cn" id="cn"/>
        <Attribute name="urn:mace:dir:attribute-def:sn" id="sn"/>
        <Attribute name="urn:mace:dir:attribute-def:givenName" id="givenName"/>
        <Attribute name="urn:mace:dir:attribute-def:mail" id="mail"/>
        <Attribute name="urn:mace:dir:attribute-def:telephoneNumber" id="telephoneNumber"/>
        <Attribute name="urn:mace:dir:attribute-def:title" id="title"/>
        <Attribute name="urn:mace:dir:attribute-def:initials" id="initials"/>
        <Attribute name="urn:mace:dir:attribute-def:description" id="description"/>
        <Attribute name="urn:mace:dir:attribute-def:carLicense" id="carLicense"/>
        <Attribute name="urn:mace:dir:attribute-def:departmentNumber" id="departmentNumber"/>
        <Attribute name="urn:mace:dir:attribute-def:displayName" id="displayName"/>
        <Attribute name="urn:mace:dir:attribute-def:employeeNumber" id="employeeNumber"/>
        <Attribute name="urn:mace:dir:attribute-def:employeeType" id="employeeType"/>
        <Attribute name="urn:mace:dir:attribute-def:preferredLanguage" id="preferredLanguage"/>
        <Attribute name="urn:mace:dir:attribute-def:manager" id="manager"/>
        <Attribute name="urn:mace:dir:attribute-def:seeAlso" id="seeAlso"/>
        <Attribute name="urn:mace:dir:attribute-def:facsimileTelephoneNumber" id="facsimileTelephoneNumber"/>
        <Attribute name="urn:mace:dir:attribute-def:street" id="street"/>
        <Attribute name="urn:mace:dir:attribute-def:postOfficeBox" id="postOfficeBox"/>
        <Attribute name="urn:mace:dir:attribute-def:postalCode" id="postalCode"/>
        <Attribute name="urn:mace:dir:attribute-def:st" id="st"/>
        <Attribute name="urn:mace:dir:attribute-def:l" id="l"/>
        <Attribute name="urn:mace:dir:attribute-def:o" id="o"/>
        <Attribute name="urn:mace:dir:attribute-def:ou" id="ou"/>
        <Attribute name="urn:mace:dir:attribute-def:businessCategory" id="businessCategory"/>
        <Attribute name="urn:mace:dir:attribute-def:physicalDeliveryOfficeName" id="physicalDeliveryOfficeName"/>
    
        <Attribute name="urn:oid:2.5.4.3" id="cn"/>
        <Attribute name="urn:oid:2.5.4.4" id="sn"/>
        <Attribute name="urn:oid:2.5.4.42" id="givenName"/>
        <Attribute name="urn:oid:0.9.2342.19200300.100.1.3" id="mail"/>
        <Attribute name="urn:oid:2.5.4.20" id="telephoneNumber"/>
        <Attribute name="urn:oid:2.5.4.12" id="title"/>
        <Attribute name="urn:oid:2.5.4.43" id="initials"/>
        <Attribute name="urn:oid:2.5.4.13" id="description"/>
        <Attribute name="urn:oid:2.16.840.1.113730.3.1.1" id="carLicense"/>
        <Attribute name="urn:oid:2.16.840.1.113730.3.1.2" id="departmentNumber"/>
        <Attribute name="urn:oid:2.16.840.1.113730.3.1.3" id="employeeNumber"/>
        <Attribute name="urn:oid:2.16.840.1.113730.3.1.4" id="employeeType"/>
        <Attribute name="urn:oid:2.16.840.1.113730.3.1.39" id="preferredLanguage"/>
        <Attribute name="urn:oid:2.16.840.1.113730.3.1.241" id="displayName"/>
        <Attribute name="urn:oid:0.9.2342.19200300.100.1.10" id="manager"/>
        <Attribute name="urn:oid:2.5.4.34" id="seeAlso"/>
        <Attribute name="urn:oid:2.5.4.23" id="facsimileTelephoneNumber"/>
        <Attribute name="urn:oid:2.5.4.9" id="street"/>
        <Attribute name="urn:oid:2.5.4.18" id="postOfficeBox"/>
        <Attribute name="urn:oid:2.5.4.17" id="postalCode"/>
        <Attribute name="urn:oid:2.5.4.8" id="st"/>
        <Attribute name="urn:oid:2.5.4.7" id="l"/>
        <Attribute name="urn:oid:2.5.4.10" id="o"/>
        <Attribute name="urn:oid:2.5.4.11" id="ou"/>
        <Attribute name="urn:oid:2.5.4.15" id="businessCategory"/>
        <Attribute name="urn:oid:2.5.4.19" id="physicalDeliveryOfficeName"/>
    
        <Attribute name="urn:oid:2.5.4.45" id="uid"/>
    </Attributes>

The next step is to edit the ``shibboleth2.xml`` file: Locate the element 
``ApplicationDefaults`` and set the value of the attribute ``entityID`` to  
``${SP_HOST}\Shibboleth``.

**STEP 2**

The next step is to configure your Apache HTTP Server. To do this, you have to 
generate a certificate and a key file for your SSL/TLS Shibboleth SP Host first 
(see Shibboleth IdP section). Then add a virtual host to your Apache HTTP 
Server: 

.. code-block:: apache

     <VirtualHost _default_:443>
     
        # Include the apache22.conf from Shibboleth
        include ${SP_HOME}/apache22.config 
        
        # Set appropriate document root here
        DocumentRoot "/var/www/"
        
        # Set your designated IDP host here    
        ServerName ${IDP_HOST} 

        # Set your designated logging directory here
        ErrorLog logs/ssl_error_log
        TransferLog logs/ssl_access_log
        LogLevel warn
                                        
        SSLEngine on

        SSLProtocol all -SSLv2

         # Important: mod_ssl should not verify the provided certificates
        SSLVerifyClient optional_no_ca

        SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW

        # Set the correct paths to your certificate and key here
        SSLCertificateFile    ${SP_HOST_CERTIFICATE} 
        SSLCertificateKeyFile ${SP_HOST_CERTIFICATE_KEY} 

        <Files ~ "\.(cgi|shtml|phtml|php3?)$">
            SSLOptions +StdEnvVars
        </Files>
        <Directory "/var/www/cgi-bin">
            SSLOptions +StdEnvVars
        </Directory>


        SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown downgrade-1.0 force-response-1.0

        CustomLog logs/ssl_request_log "%t %h %{SSL_PROTOCOL}x %{SSL_CIPHER}x \"%r\" %b"

    </VirtualHost>   


**STEP 3**

Open ``shibboleth2.xml`` and change the ``entityID`` in the element 
``ApplicationDefaults`` to your ``${SP_HOST}``. Restart your SP and try to access 
your SP Metadata ``https://${SPHOST}/Shibboleth.sso/Metadata``


.. _SP_IdP:

Configure Shibboleth SP and IdP
-------------------------------

* Download SP Metadata and store it locally as ``${SP_METADATA_FILE}``.
* Open the ``relying-party.xml`` of the Shibboleth IdP and change the Metadata 
  Provider entry to 

    .. code-block:: xml

        <!-- MetadataProvider the combining other MetadataProviders -->
        <metadata:MetadataProvider id="ShibbolethMetadata" xsi:type="metadata:ChainingMetadataProvider">

            
            <metadata:MetadataProvider id="IdPMD" xsi:type="metadata:ResourceBackedMetadataProvider">
                <!-- This is usually set correctly by the IdP installation script -->
                <metadata:MetadataResource xsi:type="resource:FilesystemResource"
                    file="${IDP_METADATA_FILE}"/>
            </metadata:MetadataProvider>

             <!-- This is the new MetadataProvider for your SP metadata -->
            <MetadataProvider id="URLMD" xsi:type="FilesystemMetadataProvider"
                xmlns="urn:mace:shibboleth:2.0:metadata"
                metadataFile="${SP_METADATA_FILE}">


                <MetadataFilter xsi:type="ChainingFilter" xmlns="urn:mace:shibboleth:2.0:metadata">
                    <MetadataFilter xsi:type="EntityRoleWhiteList"
                        xmlns="urn:mace:shibboleth:2.0:metadata">
                        <RetainedRole>samlmd:SPSSODescriptor</RetainedRole>
                    </MetadataFilter>
                </MetadataFilter>


            </MetadataProvider>

        </metadata:MetadataProvider>

* Add the ``${SP_HOST_CERTIFICATE}`` to your Java Keystore:

    ``keytool -import -file ${SP_HOST_CERTIFICATE} -alias ${SP_HOST}  -keystore ${JAVA_JRE_HOME}\lib\security\cacerts``

* Open ``shibboleth2.xml`` of your Shibboleth SP add a new SessionInitiator to 
  the ``Sessions`` element:

    .. code-block:: xml

        <!-- Default example directs to a specific IdP's SSO service (favoring SAML 2 over Shib 1). -->
        <SessionInitiator type="Chaining" Location="/Login"
                    isDefault="true" id="Intranet" relayState="cookie"
                    entityID="https://{IDP_HOST}/idp/shibboleth">
                    <SessionInitiator type="SAML2" acsIndex="1"
                      template="bindingTemplate.html"/>
                    <SessionInitiator type="Shib1" acsIndex="5"/>
        </SessionInitiator>  

* Then add a new MetadataProvider:

    .. code-block:: xml

        <!-- Chains together all your metadata sources. -->
        <MetadataProvider type="Chaining">
                    <MetadataProvider type="XML"
                                uri="https://{IDP_HOST}/idp/profile/Metadata/SAML"
                                backingFilePath="federation-metadata.xml"
                                reloadInterval="7200">
                    </MetadataProvider>
        </MetadataProvider>     
        
    Alternatively you can reference the metadata from your local IdP:
    
    .. code-block:: xml

        <!-- Chains together all your metadata sources. -->
        <MetadataProvider type="Chaining">
                    <MetadataProvider type="XML"
                                path="${IDP_HOME}/metadata/idp-metadata.xml"
                    </MetadataProvider>
        </MetadataProvider>
        
    
* Restart your IdP, the SP and the Apache HTTPD



.. _EOxServer_SecConfig:

Configure the EOxServer Security Components
-------------------------------------------

This section describes the configuration of the EOxServer security components.


General Configuration Options
`````````````````````````````

The configuration of the EOxServer security components is done in the 
``eoxserver.conf`` configuration file of your EOxServer instance. All security 
related configuration is done in the section ``[services.auth.base]``:

* ``pdp_type``: Determines the Policy Decision Point type; defaults to ``none`` 
  which deactivates authorisation. Currently, only the type ``charonpdp`` is 
  implemented.
* ``authz_service``: The URL of the Authorisation Service.
* ``attribute_mapping``: The file path to a dictionary with a mapping from 
  identity attributes received from the Shibboleth IdP to a 
  XACMLAuthzDecisionQuery. If the key is set to ``default``, a standard 
  dictionary is used.
* ``serviceID``: Identifier for the EOxServer instance to an external 
  Authorisation Service. Is used as resource ID in an XACMLAuthzDecisionQuery. 
  If the key is set to ``default``, the host name will be used.
* ``allowLocal``: If set to ``True``, the security components will alloways allow
  access to requests from the local machine. *Use with care!*


Adding new Subject attributes to the EOxServer Security Components
``````````````````````````````````````````````````````````````````

In order to register new Subject attributes from your LDAP to the IDMS, you 
have to configure the Shibboleth IdP, the Shibboleth SP, and the EOxServer. 
Let's assume we want to add the new attribute `foo`.

**Shibboleth IdP**

Add a new AttributeResolver to your ``attribute-resolver.xml`` configuration 
file:

.. code-block:: xml

    <resolver:AttributeDefinition id="foo" xsi:type="Simple"
        xmlns="urn:mace:shibboleth:2.0:resolver:ad" sourceAttributeID="description">
        <resolver:Dependency ref="localLDAP"/>
        <resolver:AttributeEncoder xsi:type="SAML1String"
            xmlns="urn:mace:shibboleth:2.0:attribute:encoder"
            name="urn:mace:dir:attribute-def:description"/>
        <resolver:AttributeEncoder xsi:type="SAML2String"
            xmlns="urn:mace:shibboleth:2.0:attribute:encoder" name="foo"
            friendlyName="foo"/>
    </resolver:AttributeDefinition>
    
Add or extend a AttributeFilterPolicy in your ``attribute-filter.xml`` 
configuration file: 

.. code-block:: xml

    <afp:AttributeFilterPolicy id="fooFilter">
        <afp:PolicyRequirementRule xsi:type="basic:ANY"/>
    
        <afp:AttributeRule attributeID="foo">
            <afp:PermitValueRule xsi:type="basic:ANY"/>
        </afp:AttributeRule>
        
    </afp:AttributeFilterPolicy>   
          
**Shibboleth SP**

Add the new attribute to the ``attribute-map.xml``

.. code-block:: xml

    <Attribute name="foo" id="foo"/>

**EOxServer**

* Make a copy of the default attribute dictionary 
  (``{$EOXSERVER_CODE_DIRECTORY)/conf/defaultAttributeDictionary``).
* Add the attribute::

    foo=foo

* Register the new dictionary in the EOxServer configuration.

