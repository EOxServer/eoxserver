OpenGIS(r) O&M 1.0.0 - ReadMe.txt
=================================

GML Application Schema version of the O&M 1.0.0 model. (OGC 07-022r1)

The general models and XML encodings for observations and measurements,
including but not restricted to those using sensors.  The Observations and
Measurements schema are defined in the OGC document 07-022r1.

More information may be found at 
 http://www.opengeospatial.org/standards/om

The most current schema are available at http://schemas.opengis.net/ .

-----------------------------------------------------------------------

2010-02-15  Simon Cox
  * reverted xsd:schema/@version attribute to 1.0.0 to align version with path 
    and documentation.  The @version attribute for 1.0.1 will not be used.

2010-01-29  Kevin Stegemoller 
  * v1.0.0: update/verify copyright (06-135r7 s#3.2)
  * v1.0.0: update relative schema imports to absolute URLs (06-135r7 s#15)
  * v1.0.0: updated xsd:schema:@version attribute (06-135r7 s#13.4)
  * v1.0.0: add archives (.zip) files of previous versions
  * v1.0.0: create/update ReadMe.txt (06-135r7 s#17)

2008-02-07  Simon Cox

  * extensions/observationSpecialization_constraint.xsd: fix namespace
    for swe in sch namespace prefix binding
  * extensions/om_extended.xsd: fix om namespace (unused)
  * see attached unified diff

2007-10-05  Simon Cox

  * Published om/1.0.0 schemas from 07-022r1

-----------------------------------------------------------------------

Policies, Procedures, Terms, and Conditions of OGC(r) are available
  http://www.opengeospatial.org/ogc/legal/ .

Copyright (c) 2010 Open Geospatial Consortium, Inc. All Rights Reserved.

-----------------------------------------------------------------------

# 2008-02-07 unified diff fix
Index: extensions/om_extended.xsd
===================================================================
--- extensions/om_extended.xsd	(revision 3013)
+++ extensions/om_extended.xsd	(working copy)
@@ -1,5 +1,5 @@
 <?xml version="1.0" encoding="UTF-8"?>
-<schema xmlns="http://www.w3.org/2001/XMLSchema" xmlns:om="http://www.opengis.net/om/1.0.1" targetNamespace="http://www.opengis.net/om/1.0" elementFormDefault="qualified" attributeFormDefault="unqualified" version="1.0.0">
+<schema xmlns="http://www.w3.org/2001/XMLSchema" xmlns:om="http://www.opengis.net/om/1.0" targetNamespace="http://www.opengis.net/om/1.0" elementFormDefault="qualified" attributeFormDefault="unqualified" version="1.0.0">
 	<annotation>
 		<documentation>om.xsd
 
Index: extensions/observationSpecialization_constraint.xsd
===================================================================
--- extensions/observationSpecialization_constraint.xsd	(revision 3013)
+++ extensions/observationSpecialization_constraint.xsd	(working copy)
@@ -11,7 +11,7 @@
 			<sch:title>Schematron validation</sch:title>
 			<sch:ns prefix="gml" uri="http://www.opengis.net/gml"/>
 			<sch:ns prefix="om" uri="http://www.opengis.net/om/1.0"/>
-			<sch:ns prefix="swe" uri="http://www.opengis.net/swe/1.0"/>
+			<sch:ns prefix="swe" uri="http://www.opengis.net/swe/1.0.1"/>
 			<sch:ns prefix="xlink" uri="http://www.w3.org/1999/xlink"/>
 			<sch:ns prefix="xs" uri="http://www.w3.org/2001/XMLSchema"/>
 			<sch:ns prefix="xsi" uri="http://www.w3.org/2001/XMLSchema-instance"/>

