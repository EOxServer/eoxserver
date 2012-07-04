OpenGIS(r) WMC schema version 1.1.2 - ReadMe.txt
-----------------------------------------------------------------------

Web Map Context (WMC) Implementation Standard.

More information on the OGC WMC standard may be found at
 http://www.opengeospatial.org/standards/wmc

The most current schema are available at http://schemas.opengis.net/ .

* Latest version is: http://schemas.opengis.net/context/1.1/wmcAll.xsd *

-----------------------------------------------------------------------

2010-11-17  Simon Cox

  * v1.1: Changes to 1.1.0 create WMC 1.1.1
    + created wmc/1.1 version from WMC 1.1.1
    + added wmcAll.xsd as the all-components document (06-135r9 s#14)
    + minor refactoring of the OnlineResourceType definition required 
      to create all-components document. The definition was placed in 
      ort.xsd.  No effect at all otherwise.

2010-01-21  Kevin Stegemoller 
  * update/verify copyright (06-135r7 s#3.2)
  * migrate relative to absolute URLs of schema imports (06-135r7 s#15)
  * updated xsd:schema:@version attribute (06-135r7 s#13.4)
  * add archives (.zip) files of previous versions
  * create/update ReadMe.txt (06-135r7 s#17)

2008-03-10  Kevin Stegemoller
  * context/1.1.0/collection.xml: reverted to original schemaLocation
  * context/1.1.0/context.xml: reverted to original schemaLocation

2007-04-12  Kevin Stegemoller
  * context/1.1.0/collection.xml: fixed schemaLocation caught in OWS-4
    CITE tests
  * context/1.1.0/context.xml: fixed schemaLocation caught in OWS-4
    CITE tests

2005-11-22  Arliss Whiteside

  * v1.1.0, v1.0.0: The XML Schema Documents for OpenGIS(r) Context
    Versions have been edited to reflect the corrigenda to documents
    1.0.0 (OGC 03-036r2) and 1.1.0 (OGC 05-005) which are based on the
    change requests: 
    OGC 05-068r1 "Store xlinks.xsd file at a fixed location"
    OGC 05-081r2 "Change to use relative paths"


-- [ VERSION NOTES ] --------------------------------------------------

  OGC is incrementally changing how schemas will be hosted. A new
  revision of the Specification Best Practice policy document (06-135r7)
  clarifies this practices.

  OGC is moving to host the schemas using a 2 digit version number so
  that dependent documents (schemas) will not have to change each time a
  schema is corrected (by a corrigendum). The schemas actual version
  number will be kept in the version attribute on the schema element
  which will be used to signify that there has been a change to the
  schema. Each previous revision will be available online in a ZIP
  archive.
  
  The LATEST version is the M.N directory where 
   * M is the major version
   * N is the minor version
  The latest bugfix version now is always in the M.N directory and 
  documented in the version attribute on the schema element. The older
  versions are now archived in the -M_N_X.zip files.
  
  Previously the OGC used M.N.X where
   * M is the major version
   * N is the minor version
   * X is the bugfix (corrigendum) version
  These will be left here for historical reasons.

-- 2010-01-21  Kevin Stegemoller 

-----------------------------------------------------------------------

Policies, Procedures, Terms, and Conditions of OGC(r) are available
  http://www.opengeospatial.org/ogc/legal/ .

Copyright (c) 2010 Open Geospatial Consortium, Inc. All Rights Reserved.

-----------------------------------------------------------------------
