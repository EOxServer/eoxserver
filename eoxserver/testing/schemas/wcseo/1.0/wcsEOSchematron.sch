<?xml version="1.0" encoding="UTF-8"?>
<sch:schema
    xmlns="http://purl.oclc.org/dsdl/schematron"
    xmlns:sch="http://purl.oclc.org/dsdl/schematron"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    queryBinding="xslt">
    <sch:title>Additional validation rules for EO-WCS XML instances.</sch:title>
    <sch:ns prefix="gmlcov" uri="http://www.opengis.net/gmlcov/1.0"/>
    <sch:ns prefix="wcs" uri="http://www.opengis.net/wcs/2.0"/>
    <sch:ns prefix="wcseo" uri="http://www.opengis.net/wcseo/1.0"/>
    <sch:ns prefix="eop" uri="http://www.opengis.net/eop/2.0"/>
    <sch:ns prefix="om" uri="http://www.opengis.net/om/2.0"/>
    <sch:pattern>
        <sch:title>Requirement 2</sch:title>
        <sch:rule context="eop:EarthObservation">
            <sch:assert test="om:featureOfInterest/eop:Footprint">
                eop:EarthObservation shall always have one eop:Footprint in the om:featureOfInterest child element.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
<!-- Req 5 -->
    <sch:pattern>
        <sch:title>Requirement 6</sch:title>
        <sch:rule context="gmlcov:RectifiedGridCoverage">
            <sch:assert test="gml:boundedBy/gml:Envelope[@srsName = 'http://www.opengis.net/def/crs/EPSG/0/4326']">
                WCSEO::RectifiedEOCoverage instances shall contain a gml:boundedBy element with a gml:Envelope containing a srsName attribute value identifying WGS84.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
    <sch:pattern>
        <sch:title>Requirement 6</sch:title>
        <sch:rule context="gmlcov:ReferenceableGridCoverage">
            <sch:assert test="gml:boundedBy/gml:Envelope[@srsName = 'http://www.opengis.net/def/crs/EPSG/0/4326']">
                WCSEO::ReferenceableEOCoverage instances shall contain a gml:boundedBy element with a gml:Envelope containing a srsName attribute value identifying WGS84.
            </sch:assert>
        </sch:rule>
    </sch:pattern>


    <sch:pattern>
        <sch:title>Req </sch:title>
        <sch:rule context="wcs:CoverageDescription">
            <sch:assert test="gmlcov:metadata">
                wcs:CoverageDescription shall always have one gmlcov:metadata child element.
                Rule used in wcs:CoverageDescription elements in DescribeEOCoverageSet and DescribeCoverage responses.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
    <sch:pattern>
        <sch:title>Req </sch:title>
        <sch:rule context="gmlcov:RectifiedGridCoverage">
            <sch:assert test="gmlcov:metadata">
                gmlcov:RectifiedGridCoverage shall always have one gmlcov:metadata child element.
                Rule used in gmlcov:RectifiedGridCoverage elements in GetCoverage responses.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
    <sch:pattern>
        <sch:title>Req </sch:title>
        <sch:rule context="gmlcov:ReferencableGridCoverage">
            <sch:assert test="gmlcov:metadata">
                gmlcov:ReferencableGridCoverage shall always have one gmlcov:metadata child element.
                Rule used in gmlcov:ReferencableGridCoverage elements in GetCoverage responses.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
    <sch:pattern>
        <sch:title>Req </sch:title>
        <sch:rule context="gmlcov:metadata">
            <sch:assert test="wcseo:EOMetadata">
                gmlcov:metadata shall always have one wcseo:EOMetadata child element.
                Rule used in gmlcov:RectifiedGridCoverage and gmlcov:ReferencableGridCoverage elements in GetCoverage responses and
                wcs:CoverageDescription elements in DescribeEOCoverageSet and DescribeCoverage responses.
            </sch:assert>
        </sch:rule>
    </sch:pattern>
<!-- TODO: Ensure wcseo:EOCoverageSubType is available in CoverageSummary and CoverageDescription but for EO Coverages only... Is this possible? -->
</sch:schema>
