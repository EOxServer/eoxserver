#-------------------------------------------------------------------------------
# $Id$
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

"""
This module provides handlers for WCS 2.0 / EO-WCS GetCapabilities requests.
"""

from xml.dom import minidom

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import DOMtoXML
from eoxserver.core.exceptions import InternalError
from eoxserver.services.owscommon import OWSCommonConfigReader
from eoxserver.services.ows.wcs.common import WCSCommonHandler, \
            getMSOutputFormatsAll,getMSWCSFormatMD,getMSWCSSRSMD
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.services.ows.wcs.wcs20.common import WCS20ConfigReader
from eoxserver.services.ows.wcst.wcst11AlterCapabilities import wcst11AlterCapabilities20


class WCS20GetCapabilitiesHandler(WCSCommonHandler):
    """
    This is the handler for WCS 2.0 / EO-WCS GetCapabilities requests. It
    inherits from :class:`~.WCSCommonHandler`.
    
    As for all handlers, the entry point is the
    :meth:`~.WCSCommonHandler.handle` method. The
    handler then performs a workflow that is described in the
    :class:`~.WCSCommonHandler` documentation.
    
    This handler follows this workflow with adaptations to the
    :meth:`createCoverages`, :meth:`configureMapObj` and :meth:`postprocess`
    methods. The latter one modifies the GetCapabilities response obtained by
    MapServer to contain EO-WCS specific extensions.
    """
    
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 2.0 GetCapabilities Handler",
        "impl_id": "services.ows.wcs20.WCS20GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "updatesequence": {"xml_location": "/@updateSequence", "xml_type": "string", "kvp_key": "updatesequence", "kvp_type": "string"},
        "sections": {"xml_location": "/{http://www.opengis.net/ows/2.0}section", "xml_type": "string[]", "kvp_key": "sections", "kvp_type": "stringlist"}
    }
    
    # TODO: override createCoverages, configureRequest, configureMapObj
    def createCoverages(self):
        """
        This method adds all Rectified Datasets and Rectified Stitched Mosaics
        to the ``coverages`` property of the handler. For each of these
        coverages, a layer will be added to the MapScript :class:`mapObj`.
        """
        self.coverages = self._get_coverages(
            [
                "resources.coverages.wrappers.RectifiedDatasetWrapper",
                "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"
            ]
        ) 
        
    def _get_coverages(self, impl_ids=None):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        if impl_ids:
            return factory.find(
                impl_ids=impl_ids,
                filter_exprs=[visible_expr]
            )
        else:
            return factory.find(filter_exprs=[visible_expr])


    def configureMapObj(self):
        """
        This method extends the :class:`~.WCSCommonHandler.configureMapObj`
        method to include informations on the available output formats as
        well as the supported CRSes.
        """
        super(WCS20GetCapabilitiesHandler, self).configureMapObj()

        # set all the supported formats 
        for output_format in getMSOutputFormatsAll() :  
            self.map.appendOutputFormat(output_format)

        self.map.setMetaData("wcs_formats",getMSWCSFormatMD()) 

        # set supported CRSes 
        self.map.setMetaData( 'ows_srs' , getMSWCSSRSMD() ) 
        self.map.setMetaData( 'wcs_srs' , getMSWCSSRSMD() ) 

    
    def getMapServerLayer(self, coverage):
        """
        This method returns a MapScript :class:`layerObj` for the input
        ``coverage``. It extends the
        :class:`~.WCSCommonHandler.getMapServerLayer` function by configuring
        the input data using the appropriate connectors (see
        :mod:`eoxserver.services.connectors`).
        """
        layer = super(WCS20GetCapabilitiesHandler, self).getMapServerLayer(coverage)
        
        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    coverage.getDataStructureType()
            }
        )
        
        layer = connector.configure(layer, coverage)
        
        return layer


    def postprocess(self, resp):
        """
        This method transforms the standard WCS 2.0 response ``resp`` obtained
        from MapServer into an EO-WCS compliant GetCapabilities response and
        returns the corresponding :class:`~.Response` object.
        
        Specifically,
        
        * the xsi:schemaLocation attribute of the document root is set
          to the EO-WCS schema URL
        * the extensions supported by EOxServer are added to the
          wcs:ServiceMetadata element
        * the supported EO-WCS profiles are added to the
          wcs:ServiceIdentification element
        * the metadata for the DescribeEOCoverageSet operation is added
          to the ows:OperationsMetadata element
        * the wcs:Contents section is replaced by an EO-WCS compliant
          structure
          
        The wcs:Contents section is configured with the coverage summaries of
        all visible Rectified and Referenceable Datasets, of all Rectified
        Stitched Mosaics and the summaries of all Dataset Series. Note that
        the handler is aware of the OWS Common sections parameter which allows
        to deselect all or parts of the wcs:Contents section and acts
        accordingly.
        
        Should MapServer return an exception report in ``resp``, it is
        passed on unchanged except for the xsi:schemaLocation attribute.
        """
        
        dom = minidom.parseString(resp.content)
        
        # add the additional CRS namespace 


        # change xsi:schemaLocation
        schema_location_attr = dom.documentElement.getAttributeNode("xsi:schemaLocation")
        schema_location_attr.nodeValue = "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"

        
        # we are finished if the response is an ows:ExceptionReport
        # proceed otherwise
        if dom.documentElement.localName != "ExceptionReport":
        
            encoder = WCS20EOAPEncoder()

            #TODO: Following part should be handled by the MapServer. 
            #      Remove the code when MapServer really does it. 

            # append SupportedCRSs to ServiceMetadata
            svc_md = dom.getElementsByTagName("wcs:ServiceMetadata").item(0)

            if svc_md is not None : 
                extension = encoder.encodeExtension()
                svc_md.appendChild(extension)
                supported_crss = encoder.encodeSupportedCRSs() 

                for sc in supported_crss : 
                    extension.appendChild( sc )
                
            # append EO Profiles to ServiceIdentification
            svc_identification = dom.getElementsByTagName("ows:ServiceIdentification").item(0)
            
            if svc_identification is not None:
                eo_profiles = encoder.encodeEOProfiles()
                
                profiles = svc_identification.getElementsByTagName("ows:Profile")
                if len(profiles) == 0:
                    for eo_profile in eo_profiles:
                        svc_identification.appendChild(eo_profile)
                else:
                    for eo_profile in eo_profiles:
                        svc_identification.insertBefore(eo_profile, profiles.item(0))
                    
            # append DescribeEOCoverageSet
            op_metadata = dom.getElementsByTagName("ows:OperationsMetadata").item(0)
            
            if op_metadata is not None:
                desc_eo_cov_set_op = encoder.encodeDescribeEOCoverageSetOperation(
                    OWSCommonConfigReader().getHTTPServiceURL()
                )

                op_metadata.appendChild(desc_eo_cov_set_op)
                
                count_default = WCS20ConfigReader().getPagingCountDefault()
                op_metadata.appendChild(encoder.encodeCountDefaultConstraint(count_default))


            # rewrite wcs:Contents
            # adjust wcs:CoverageSubtype and add wcseo:DatasetSeriesSummary
            sections = self.req.getParamValue("sections")
            
            if sections is None or len(sections) == 0 or "Contents" in sections or\
               "CoverageSummary" in sections or\
               "DatasetSeriesSummary" in sections or\
               "All" in sections:
                
                contents_new = encoder.encodeContents()

                # adjust wcs:CoverageSubtype
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "CoverageSummary" in sections or "All" in sections:
                    
                    all_coverages = self._get_coverages()
                    
                    for coverage in all_coverages:
                        cov_summary = encoder.encodeCoverageSummary(coverage)
                        contents_new.appendChild(cov_summary)

                # append dataset series summaries
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "DatasetSeriesSummary" in sections or "All" in sections:
                    
                    extension = encoder.encodeExtension()
                    contents_new.appendChild(extension)
                    
                    dss_factory = System.getRegistry().bind(
                        "resources.coverages.wrappers.DatasetSeriesFactory"
                    )
                    
                    for dataset_series in dss_factory.find():
                        dss_summary = encoder.encodeDatasetSeriesSummary(dataset_series)
                        extension.appendChild(dss_summary)

                contents_old = dom.getElementsByTagName("wcs:Contents").item(0) 

                if contents_old is None:
                    dom.documentElement.appendChild(contents_new)
                else:
                    contents_old.parentNode.replaceChild(contents_new, contents_old)
        
        # rewrite XML and replace it in the response
        resp.content = DOMtoXML(dom)
        
        dom.unlink()
        
        # TODO: integrate WCS Transaction Operation in getcapabilities response
        #return wcst11AlterCapabilities20(resp)
        return resp


class WCS20CorrigendumGetCapabilitiesHandler(WCS20GetCapabilitiesHandler):

    REGISTRY_CONF = {
        "name": "WCS 2.0 GetCapabilities Handler",
        "impl_id": "services.ows.wcs20.WCS20CorrigendumGetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.1",
            "services.interfaces.operation": "getcapabilities"
        }
    }
