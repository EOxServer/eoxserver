GML 3.1.1 profile gmlsfProfile 1.0.0 ReadMe.txt
======================================================================

OGC(r) GML 3.1.1 simple features profile
-----------------------------------------------------------------------

The GML 3.1.1 simple features profile is an OGC Standard.

More information may be found at
 http://www.opengeospatial.org/standards/gml

The most current schema are available at http://schemas.opengis.net/ .

-----------------------------------------------------------------------

2012-07-21  Kevin Stegemoller
  * v1.0.0.2 WARNING XLink change is NOT BACKWARD COMPATIBLE.
  * changed OGC XLink (xlink:simpleLink) to W3C XLink (xlink:simpleAttrs)
  per an approved TC and PC motion during the Dec. 2011 Brussels meeting.
  see http://www.opengeospatial.org/blog/1597
  * implement 11-025: retroactively require/add all leaf documents of an
  XML namespace shall explicitly <include/> the all-components schema
  * v1.0.0: updated xsd:schema/@version to 1.0.0.2 (06-135r7 s#13.4)

2008-05-20  Kevin Stegemoller

  * gmlsfProfile/1.0.0/examples/exampleHydrographySchema.xsd: one
    non-content-changing bug fix for GML 3.1.1 location
  * gmlsfProfile/1.0.0/examples/exampleRoads_BtsSchema.xsd: three
    non-content-changing bug fixes including fix GML 3.1.1 location; fix close
    complexType start tag found by David Valentine (valentin at sdsc.edu); fix
    case on extension type definition
  * gmlsfProfile/1.0.0/examples/exampleReporterSchema.xsd: four
    non-content-changing bug fixes including fix close appinfo start tag; fix
    GML 3.1.1 location; fix close complexType start tag; fix case on extension
    type definition

-----------------------------------------------------------------------

Policies, Procedures, Terms, and Conditions of OGC(r) are available
  http://www.opengeospatial.org/ogc/legal/ .

OGC and OpenGIS are registered trademarks of Open Geospatial Consortium.

Copyright (c) 2007-2008 Open Geospatial Consortium

-----------------------------------------------------------------------
