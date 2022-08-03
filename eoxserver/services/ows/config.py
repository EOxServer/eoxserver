# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

DEFAULT_EOXS_OWS_SERVICE_HANDLERS = [
    'eoxserver.services.ows.wcs.v10.handlers.GetCapabilitiesHandler',
    'eoxserver.services.ows.wcs.v10.handlers.DescribeCoverageHandler',
    'eoxserver.services.ows.wcs.v10.handlers.GetCoverageHandler',
    'eoxserver.services.ows.wcs.v11.handlers.GetCapabilitiesHandler',
    'eoxserver.services.ows.wcs.v11.handlers.DescribeCoverageHandler',
    'eoxserver.services.ows.wcs.v11.handlers.GetCoverageHandler',
    'eoxserver.services.ows.wcs.v20.handlers.GetCapabilitiesHandler',
    'eoxserver.services.ows.wcs.v20.handlers.DescribeCoverageHandler',
    'eoxserver.services.ows.wcs.v20.handlers.DescribeEOCoverageSetHandler',
    'eoxserver.services.ows.wcs.v20.handlers.GetCoverageHandler',
    'eoxserver.services.ows.wcs.v20.handlers.GetEOCoverageSetHandler',

    'eoxserver.services.ows.wms.v10.handlers.WMS10GetCapabilitiesHandler',
    'eoxserver.services.ows.wms.v10.handlers.WMS10GetMapHandler',
    # 'eoxserver.services.ows.wms.v10.handlers.WMS10GetFeatureInfoHandler',
    'eoxserver.services.ows.wms.v11.handlers.WMS11GetCapabilitiesHandler',
    'eoxserver.services.ows.wms.v11.handlers.WMS11GetMapHandler',
    # 'eoxserver.services.ows.wms.v11.handlers.WMS11GetFeatureInfoHandler',
    'eoxserver.services.ows.wms.v13.handlers.WMS13GetCapabilitiesHandler',
    'eoxserver.services.ows.wms.v13.handlers.WMS13GetMapHandler',
    # 'eoxserver.services.ows.wms.v13.handlers.WMS13GetFeatureInfoHandler',

    'eoxserver.services.ows.wps.v10.getcapabilities.WPS10GetCapabilitiesHandler',
    'eoxserver.services.ows.wps.v10.describeprocess.WPS10DescribeProcessHandler',
    'eoxserver.services.ows.wps.v10.execute.WPS10ExecuteHandler',

    'eoxserver.services.ows.wps.v20.getcapabilities.WPS20GetCapabilitiesHandler',
    'eoxserver.services.ows.wps.v20.describeprocess.WPS20DescribeProcessHandler',
    'eoxserver.services.ows.wps.v20.execute.WPS20ExecuteHandler',

    'eoxserver.services.ows.dseo.v10.handlers.GetCapabilitiesHandler',
    'eoxserver.services.ows.dseo.v10.handlers.GetProductHandler',
]

DEFAULT_EOXS_OWS_EXCEPTION_HANDLERS = [
    'eoxserver.services.ows.wcs.v10.exceptionhandler.WCS10ExceptionHandler',
    'eoxserver.services.ows.wcs.v11.exceptionhandler.WCS11ExceptionHandler',
    'eoxserver.services.ows.wcs.v20.exceptionhandler.WCS20ExceptionHandler',
    'eoxserver.services.ows.wms.v13.exceptionhandler.WMS13ExceptionHandler',
]

DEFAULT_EOXS_WCS_ERROR_HTML_TEMPLATE = "wcs/error_template.html"
