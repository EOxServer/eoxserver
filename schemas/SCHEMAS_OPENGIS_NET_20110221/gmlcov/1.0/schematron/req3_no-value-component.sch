<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
    <sch:title>Requirement 3</sch:title>
    <sch:ns uri="http://www.opengis.net/swe/2.0" prefix="swe"/>
    <sch:ns uri="http://www.opengis.net/gmlcov/1.0" prefix="gmlcov"/>
    <sch:ns uri="http://www.w3.org/1999/xlink" prefix="xlink"/>
    <sch:pattern>
        <sch:title>Req 3</sch:title>
        <sch:rule context="//swe:Quantity | //swe:QuantityRange |//swe:Count|//swe:CountRange | //swe:Time | //swe:TimeRange | //swe:Boolean | //swe:Category | //swe:CategoryRange | //swe:Text">
            <sch:assert test="count(//swe:value)=0">
                For all SWE Common AbstractSimpleComponent subtypes in a range type, instance multiplicity of the value component shall be zero.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
</sch:schema>
