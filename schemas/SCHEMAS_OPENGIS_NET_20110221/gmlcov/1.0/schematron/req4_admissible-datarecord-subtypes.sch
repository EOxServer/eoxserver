<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
    <sch:title>Requirement 4</sch:title>
    <sch:ns uri="http://www.opengis.net/swe/2.0" prefix="swe"/>
    <sch:ns uri="http://www.opengis.net/gmlcov/1.0" prefix="gmlcov"/>
    <sch:ns uri="http://www.w3.org/1999/xlink" prefix="xlink"/>
    <sch:pattern>
        <sch:title>Req 4</sch:title>
        <sch:rule context="swe:DataRecord">
            <sch:assert test="descendant-or-self::*[name()='swe:DataRecord' or name()='swe:Vector']">
                Wherever the SWE Common XML schema allows an AbstractDataComponent in a coverage range type the concrete instance shall be one of the AbstractDataComponent subtypes DataRecord and Vector.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
</sch:schema>
