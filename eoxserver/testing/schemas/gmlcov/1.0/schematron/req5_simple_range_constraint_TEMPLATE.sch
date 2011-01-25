<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
    <sch:title>Requirement 5</sch:title>
    <sch:ns uri="http://www.opengis.net/swe/2.0" prefix="swe"/>
    <sch:ns uri="http://www.opengis.net/gmlcov/1.0" prefix="gmlcov"/>
    <sch:ns uri="http://www.w3.org/1999/xlink" prefix="xlink"/>
    <sch:ns uri="http://www.opengis.net/gml/3.2" prefix="gml"/>
    <sch:pattern>
        <sch:title>Req 5</sch:title>
        <sch:rule context="//gml:rangeSet">
            <sch:let name="low1" value="number(subsequence(tokenize(normalize-space(../gml:domainSet//gml:low[1]), '\s+'),1,1))" />
            <sch:let name="low2" value="number(subsequence(tokenize(normalize-space(../gml:domainSet//gml:low[1]), '\s+'),2,1))" />
            <sch:let name="lowi" value="number(subsequence(tokenize(normalize-space(../gml:domainSet//gml:low[1]), '\s+'),i,1))" />

            <sch:let name="high1" value="number(subsequence(tokenize(normalize-space(../gml:domainSet//gml:high[1]), '\s+'),1,1))"/>
            <sch:let name="high2" value="number(subsequence(tokenize(normalize-space(../gml:domainSet//gml:high[1]), '\s+'),2,1))"/>
            <sch:let name="highi" value="number(subsequence(tokenize(normalize-space(../gml:domainSet//gml:high[1]), '\s+'),i,1))"/>

            <sch:let name="band" value="count(../swe:dataRecord/swe:field)"/>

            <sch:assert test="count(tokenize(normalize-space(//Datablock/tuplelist[1]), '\s+')) = ($high1 - $low1 + 1) * ($high2 - $low2 + 1) * ... * ($highi - $lowi + 1) * $band">
            	For each coordinate contained in the domain set description of a coverage there shall be exactly one range value in the coverage range set.
                (This rule is a template which, due to the iteration symbolized, does not execute as is.)
            </sch:assert>
        </sch:rule>
    </sch:pattern>
</sch:schema>
