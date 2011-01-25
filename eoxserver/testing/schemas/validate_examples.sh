#!/bin/sh

# Use local xml catalog to import missing schema files:
export XML_CATALOG_FILES="catalog.xml"

echo "########################################################################"
echo "\n"
echo "Validating against wcseo/1.0/wcsEOAll.xsd"
echo "\n"
xmllint --noout --schema http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd wcseo/1.0/examples/wcseo_requestGetCapabilities.xml wcseo/1.0/examples/wcseo_responseGetCapabilities.xml wcseo/1.0/examples/wcseo_requestDescribeEOCoverageSet.xml  wcseo/1.0/examples/wcseo_responseDescribeEOCoverageSet_minimal.xml wcseo/1.0/examples/wcseo_responseDescribeEOCoverageSet.xml
echo "\n"
echo "\nValidating against wcseo/1.0/wcsEOSchematron.sch"
echo "\n"
xsltproc schematron_xslt1/iso_dsdl_include.xsl wcseo/1.0/wcsEOSchematron.sch | xsltproc schematron_xslt1/iso_abstract_expand.xsl - | xsltproc schematron_xslt1/iso_svrl_for_xslt1.xsl - | xsltproc - wcseo/1.0/examples/wcseo_requestGetCapabilities.xml wcseo/1.0/examples/wcseo_responseGetCapabilities.xml wcseo/1.0/examples/wcseo_requestDescribeEOCoverageSet.xml  wcseo/1.0/examples/wcseo_responseDescribeEOCoverageSet_minimal.xml wcseo/1.0/examples/wcseo_responseDescribeEOCoverageSet.xml

echo "########################################################################"
echo "\n"
echo "Validating against wcs/2.0/wcsAll.xsd"
echo "\n"
xmllint --noout --schema http://schemas.opengis.net/wcs/2.0/wcsAll.xsd wcseo/1.0/examples/wcseo_requestGetCapabilities.xml wcseo/1.0/examples/wcseo_responseGetCapabilities.xml

echo "########################################################################"
echo "\n"
echo "Validating against gmlcov/1.0/coverage.xsd"
echo "\n"
xmllint --noout --schema http://schemas.opengis.net/gmlcov/1.0/coverage.xsd wcseo/1.0/examples/wcseo_responseGetCoverage.xml
echo "\n"
echo "Validating against wcseo/1.0/wcsEOSchematron.sch"
echo "\n"
xsltproc schematron_xslt1/iso_dsdl_include.xsl wcseo/1.0/wcsEOSchematron.sch | xsltproc schematron_xslt1/iso_abstract_expand.xsl - | xsltproc schematron_xslt1/iso_svrl_for_xslt1.xsl - | xsltproc - wcseo/1.0/examples/wcseo_responseGetCoverage.xml

echo "########################################################################"
echo "\n"
echo "Validating against wcseo/1.0/wcsEOGetCoverage.xsd"
echo "\n"
xmllint --noout --schema http://schemas.opengis.net/wcseo/1.0/wcsEOGetCoverage.xsd wcseo/1.0/examples/wcseo_responseGetCoverage.xml
