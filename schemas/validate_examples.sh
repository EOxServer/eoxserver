#!/bin/sh
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

# Use local xml catalog to import missing schema files:
export XML_CATALOG_FILES="catalog.xml"

echo "########################################################################"
echo "\n"
echo "Validating EO-WCS examples against wcs/wcseo/1.0/wcsEOAll.xsd"
echo "\n"
find wcs/wcseo/1.0/ -iname "*.xml" -exec xmllint --noout --schema http://schemas.opengis.net/wcs/wcseo/1.0/wcsEOAll.xsd {} \;

echo "########################################################################"
echo "\n"
echo "\nValidating EO-WCS examples against wcs/wcseo/1.0/wcsEOSchematron.sch"
echo "\n"
xsltproc schematron_xslt1/iso_dsdl_include.xsl wcs/wcseo/1.0/wcsEOSchematron.sch | xsltproc schematron_xslt1/iso_abstract_expand.xsl - | xsltproc schematron_xslt1/iso_svrl_for_xslt1.xsl - | xsltproc - \
    wcs/wcseo/1.0/examples/wcseo_requestGetCapabilities.xml \
    wcs/wcseo/1.0/examples/wcseo_responseGetCapabilities.xml \
    wcs/wcseo/1.0/examples/wcseo_requestDescribeEOCoverageSet.xml \
    wcs/wcseo/1.0/examples/wcseo_responseDescribeEOCoverageSet_minimal.xml \
    wcs/wcseo/1.0/examples/wcseo_responseDescribeEOCoverageSet.xml \
    wcs/wcseo/1.0/examples/wcseo_requestGetCoverage.xml \
    wcs/wcseo/1.0/examples/wcseo_responseGetCoverage.xml \
    wcs/wcseo/1.0/examples/wcseo_responseGetCoverage_StitchedMosaic.xml

echo "########################################################################"
echo "\n"
echo "Validating EO-WCS examples against wcs/2.0/wcsAll.xsd"
echo "\n"
find wcs/wcseo/1.0/ -iname "*.xml" -exec xmllint --noout --schema http://schemas.opengis.net/wcs/2.0/wcsAll.xsd {} \;

echo "########################################################################"
echo "\n"
echo "Validating EO-WCS examples against http://schemas.xmlsoap.org/soap/envelope/"
echo "\n"
xmllint --noout --schema http://schemas.xmlsoap.org/soap/envelope/ \
    wcs/wcseo/1.0/examples/wcseo_requestGetCoverage_SOAP.xml

## Not backwards compatible like used below:
#echo "########################################################################"
#echo "\n"
#echo "Validating EO-WCS examples against gmlcov/1.0/coverage.xsd"
#echo "\n"
#xmllint --noout --schema http://schemas.opengis.net/gmlcov/1.0/coverage.xsd wcs/wcseo/1.0/examples/wcseo_responseGetCoverage.xml wcs/wcseo/1.0/examples/wcseo_responseGetCoverage_StitchedMosaic.xml


echo "########################################################################"
echo "\n"
echo "Validating WCS examples against wcs/2.0/wcsAll.xsd"
echo "\n"
find wcs/2.0/ -iname "*.xml" -exec xmllint --noout --schema wcs/2.0/wcsAll.xsd {} \;


echo "########################################################################"
echo "\n"
echo "Validating WCS GeoTIFF examples against wcs/geotiff/1.0/wcsGeotiff.xsd"
echo "\n"
find gmlcov/geotiff/ -iname "*.xml" -exec xmllint --noout --schema gmlcov/geotiff/1.0/wcsGeotiff.xsd {} \;


echo "########################################################################"
echo "\n"
echo "Validating GMLCOV examples against gmlcov/1.0/gmlcovAll.xsd"
echo "\n"
find gmlcov/1.0/ -iname "*.xml" -exec xmllint --noout --schema gmlcov/1.0/gmlcovAll.xsd {} \;
