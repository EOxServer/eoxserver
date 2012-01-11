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

from osgeo.osr import SpatialReference
from datetime import datetime
from xml.dom import minidom

from django.contrib.gis.geos import Polygon

from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.core.util.timetools import isotime
from eoxserver.processing.mosaic import MosaicContribution

def _adjustPrecision(string, is_projected=False):
    return string.replace("%f", "%.3f" if is_projected else "%.8f")

class GMLEncoder(XMLEncoder):
    def _initializeNamespaces(self):
        return {
            "gml": "http://www.opengis.net/gml/3.2"
        }
    
    def encodeLinearRing(self, ring, srid):
        sr = SpatialReference()
        sr.ImportFromEPSG(srid)
        
        frmt = _adjustPrecision("%f %f", sr.IsProjected())
        
        if srid == 4326:
            pos_list = " ".join([frmt % (point[1], point[0]) for point in ring])
        else:
            pos_list = " ".join([frmt % point for point in ring])
        
        return self._makeElement(
            "gml", "LinearRing", [
                ("gml", "posList", pos_list)
            ]
        )

    def encodePolygon(self, poly, base_id):
        ext_element = self.encodeLinearRing(poly[0], poly.srid)
        
        if len(poly) > 1:
            int_elements = [("gml", "interior", [(self.encodeLinearRing(ring, poly.srid),)]) for ring in poly[1:]]
        else:
            int_elements = []
        
        sub_elements = [
            ("@gml", "id", "polygon_%s" % base_id),
            ("gml", "exterior", [(ext_element,)])
        ]
        sub_elements.extend(int_elements)

        return self._makeElement(
            "gml", "Polygon", sub_elements
        )

    def encodeMultiPolygon(self, geom, base_id):
        if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
            polygons = [self.encodePolygon(geom[c], "%s_%d" % (base_id, c+1)) for c in range(0, geom.num_geom)]
        elif geom.geom_type == "Polygon":
            polygons = [self.encodePolygon(geom, base_id)]
        
        
        
        sub_elements = [
            ("@gml", "id", "multisurface_%s" % base_id),
            ("@", "srsName", "EPSG:4326")
        ]
        sub_elements.extend([
            ("gml", "surfaceMember", [
                (poly_element,)
            ]) for poly_element in polygons
        ])
        
        return self._makeElement(
            "gml", "MultiSurface", sub_elements
        )

class EOPEncoder(GMLEncoder):
    def _initializeNamespaces(self):
        ns_dict = super(EOPEncoder, self)._initializeNamespaces()
        ns_dict.update({
            "om": "http://www.opengis.net/om/2.0",
            "eop": "http://www.opengis.net/eop/2.0"
        })
        return ns_dict

    def encodeFootprint(self, footprint, eo_id):
        return self._makeElement(
            "eop", "Footprint", [
                ("@gml", "id", "footprint_%s" % eo_id),
                ("eop", "multiExtentOf", [
                    (self.encodeMultiPolygon(footprint, eo_id),)
                ])
            ]
        )
    
    def encodeMetadataProperty(self, eo_id, contributing_datasets=None):
        sub_elements =  [
            ("eop", "identifier", eo_id),
            ("eop", "acquisitionType", "NOMINAL"), # TODO
            ("eop", "status", "ARCHIVED") # TODO
        ]
        
        if contributing_datasets is not None:
            sub_elements.append(
                ("eop", "composedOf", contributing_datasets)
            )
        
        return self._makeElement(
            "eop", "metaDataProperty", [
                ("eop", "EarthObservationMetaData", sub_elements)
            ]
        )
    
    def encodeEarthObservation(self, eo_metadata, contributing_datasets=None, poly=None):
        eo_id = eo_metadata.getEOID()
        begin_time_iso = isotime(eo_metadata.getBeginTime())
        end_time_iso = isotime(eo_metadata.getEndTime())
        result_time_iso = isotime(eo_metadata.getEndTime()) # TODO isotime(datetime.now())
        
        footprint = None
        if eo_metadata.getType() == "eo.rect_stitched_mosaic":
            for ds in eo_metadata.getDatasets():
                if footprint is None:
                    footprint = ds.getFootprint()
                else:
                    footprint = ds.getFootprint().union(footprint) 
            
        else:
            footprint = eo_metadata.getFootprint()
            
        if poly is not None:
            footprint = footprint.intersection(poly)
        
        return self._makeElement(
            "eop", "EarthObservation", [
                ("@gml", "id", "eop_%s" % eo_id),
                ("om", "phenomenonTime", [
                    ("gml", "TimePeriod", [
                        ("@gml", "id", "phen_time_%s" % eo_id),
                        ("gml", "beginPosition", begin_time_iso),
                        ("gml", "endPosition", end_time_iso)
                    ])
                ]),
                ("om", "resultTime", [
                    ("gml", "TimeInstant", [
                        ("@gml", "id", "res_time_%s" % eo_id),
                        ("gml", "timePosition", result_time_iso)
                    ])
                ]),
                ("om", "procedure", []),
                ("om", "observedProperty", []),
                ("om", "featureOfInterest", [
                    (self.encodeFootprint(footprint, eo_id),)
                ]),
                ("om", "result", []),
                (self.encodeMetadataProperty(eo_id, contributing_datasets),)
            ]
        )

class CoverageGML10Encoder(XMLEncoder):
    def _initializeNamespaces(self):
        return {
            "gml": "http://www.opengis.net/gml/3.2",
            "gmlcov": "http://www.opengis.net/gmlcov/1.0",
            "swe": "http://www.opengis.net/swe/2.0"
        }
    
    def _getGMLId(self, id):
        if str(id)[0].isdigit():
            return "gmlid_%s" % str(id)
        else:
            return id
    
    def encodeDomainSet(self, coverage):
        if coverage.getType() == "eo.ref_dataset":
            return self._makeElement("gml", "domainSet", [
                (self.encodeReferenceableGrid(
                    coverage.getSize(),
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])
        else:
            return self._makeElement("gml", "domainSet", [
                (self.encodeRectifiedGrid(
                    coverage.getSize(),
                    coverage.getExtent(),
                    coverage.getSRID(),
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])
    
    def encodeSubsetDomainSet(self, coverage, srid, size, extent):
        if coverage.getType() == "eo.ref_dataset":
            return self._makeElement("gml", "domainSet", [
                (self.encodeReferenceableGrid(
                    size,
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])
        else:
            return self._makeElement("gml", "DomainSet", [
                (self.encodeRectifiedGrid(
                    size,
                    extent,
                    srid,
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])

    
    def encodeRectifiedGrid(self, size, extent, srid, id):
        sr = SpatialReference()
        sr.ImportFromEPSG(srid)
        
        if sr.IsProjected():
            axisLabels = "x y"
        else:
            axisLabels = "long lat"
        
        # TODO make precision adjustable (3 decimal digits for projected axes)
        pos_format = _adjustPrecision("%f %f", sr.IsProjected())
        
        grid_element = self._makeElement("gml", "RectifiedGrid", [
            ("", "@dimension", 2),
            ("@gml", "id", self._getGMLId(id)),
            ("gml", "limits", [
                ("gml", "GridEnvelope", [
                    ("gml", "low", "0 0"),
                    ("gml", "high", "%d %d" % (size[0]-1, size[1]-1))
                ])
            ]),
            ("gml", "axisLabels", axisLabels),
            ("gml", "origin", [
                ("gml", "Point", [
                    ("", "@srsName", "http://www.opengis.net/def/crs/EPSG/0/%s" % srid),
                    ("@gml", "id", self._getGMLId("%s_origin" % id)),
                    ("gml", "pos", _adjustPrecision("%f %f", sr.IsProjected()) % (extent[0], extent[3])) 
                ])
            ])
        ])
        
        grid_element.appendChild(self._makeElement("gml", "offsetVector", [
            ("", "@srsName", "http://www.opengis.net/def/crs/EPSG/0/%s" % srid),
            ("", "@@", _adjustPrecision("%f 0.0", sr.IsProjected()) % ((extent[2] - extent[0]) / float(size[0])))
        ]))
        grid_element.appendChild(self._makeElement("gml", "offsetVector", [
            ("", "@srsName", "http://www.opengis.net/def/crs/EPSG/0/%s" % srid),
            ("", "@@", _adjustPrecision("0.0 %f", sr.IsProjected()) % ((extent[1] - extent[3]) / float(size[1])))
        ]))
                    
        return grid_element
    
    def encodeReferenceableGrid(self, size, id):
        axisLabels = "x y" # TODO
        
        grid_element = self._makeElement("gml", "ReferenceableGrid", [
            ("", "@dimension", 2),
            ("@gml", "id", self._getGMLId(id)),
            ("gml", "limits", [
                ("gml", "GridEnvelope", [
                    ("gml", "low", "0 0"),
                    ("gml", "high", "%d %d" % (size[0]-1, size[1]-1))
                ])
            ]),
            ("gml", "axisLabels", axisLabels)
        ])
        
        return grid_element
    
    def encodeBoundedBy(self, minx, miny, maxx, maxy):
        #bbox = grid.getBBOX()
        
        #minx, miny, maxx, maxy = bbox.transform(4326, True).extent
        
        return self._makeElement("gml", "boundedBy", [
            ("gml", "Envelope", [
                ("", "@srsName", "http://www.opengis.net/def/crs/EPSG/0/4326"),
                ("", "@axisLabels", "lat long"),
                ("", "@uomLabels", "deg deg"),
                ("", "@srsDimension", 2),
                ("gml", "lowerCorner", _adjustPrecision("%f %f") % (miny, minx)),
                ("gml", "upperCorner", _adjustPrecision("%f %f") % (maxy, maxx))
            ])
        ])

    def encodeRangeType(self, coverage):
        range_type = coverage.getRangeType()
        
        return self._makeElement("gmlcov", "rangeType", [
            ("swe", "DataRecord", [
                (self.encodeRangeTypeField(range_type, band),)
                for band in range_type.bands
            ])
        ])
    
    def encodeRangeTypeField(self, range_type, band):
        return self._makeElement("swe", "field", [
            ("", "@name", band.name),
            ("swe", "Quantity", [
                ("", "@definition", band.definition),
                ("swe", "description", band.description),
# TODO: Not in sweCommon anymore
#                ("swe", "name", band.name),
                ("swe", "nilValues", [(self.encodeNilValue(nil_value),) for nil_value in band.nil_values]),
                ("swe", "uom", [
                    ("", "@code", band.uom)
                ]),
                ("swe", "constraint", [
                    ("swe", "AllowedValues", [
                        ("swe", "interval", "%s %s" % range_type.getAllowedValues()),
                        ("swe", "significantFigures", range_type.getSignificantFigures())
                    ])
                ])
            ])
        ])
    
    def encodeNilValue(self, nil_value):
        return self._makeElement("swe", "NilValues", [
            ("swe", "nilValue", [
                ("", "@reason", nil_value.reason),
                ("", "@@", nil_value.value)
            ])
        ])


class WCS20Encoder(CoverageGML10Encoder):
    def _initializeNamespaces(self):
        ns_dict = super(WCS20Encoder, self)._initializeNamespaces()
        ns_dict.update({
            "wcs": "http://www.opengis.net/wcs/2.0",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        })
        return ns_dict
    
    def encodeCoverageDescription(self, coverage):
        return self._makeElement("wcs", "CoverageDescription", [
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(*coverage.getWGS84Extent()),),
            ("wcs", "CoverageId", coverage.getCoverageId()),
            (self.encodeDomainSet(coverage),),
            (self.encodeRangeType(coverage),),
            ("wcs", "ServiceParameters", [
                ("wcs", "CoverageSubtype", coverage.getCoverageSubtype()),
            ])
        ])
    
    def encodeCoverageDescriptions(self, coverages, is_root=False):
        if is_root:
            sub_nodes = [("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd")]
        else:
            sub_nodes = []
            
        sub_nodes.extend([(self.encodeCoverageDescription(coverage),) for coverage in coverages])
        return self._makeElement("wcs", "CoverageDescriptions", sub_nodes)

class WCS20EOAPEncoder(WCS20Encoder):
    def _initializeNamespaces(self):
        ns_dict = super(WCS20EOAPEncoder, self)._initializeNamespaces()
        ns_dict.update({
            "ows": "http://www.opengis.net/ows/2.0",
            "wcseo": "http://www.opengis.net/wcseo/1.0",
            "xlink": "http://www.w3.org/1999/xlink"
        })
        return ns_dict
    
    def encodeContributingDatasets(self, coverage, poly=None):
        eop_encoder = EOPEncoder()
        
        contributions = MosaicContribution.getContributions(coverage, poly)
        
        return [
            (self._makeElement(
                "wcseo", "dataset", [
                    ("wcs", "CoverageId", contribution.dataset.getCoverageId()),
                    ("wcseo", "contributingFootprint", eop_encoder.encodeFootprint(contribution.contributing_footprint, contribution.dataset.getEOID()))
                ]
            ),)
            for contribution in contributions
        ]
    
    def encodeEOMetadata(self, coverage, req=None, include_composed_of=False, poly=None): # TODO include_composed_of and poly are currently ignored
        poly_intersection = None
        if poly is not None:
            poly_intersection = coverage.getFootprint().intersection(poly)
        
        eop_encoder = EOPEncoder()
        
        if coverage.getEOGML():
            dom = minidom.parseString(coverage.getEOGML())
            earth_observation = dom.documentElement
            if poly_intersection is not None:
                new_footprint = eop_encoder.encodeFootprint(poly_intersection, coverage.getEOID())
                old_footprint = dom.getElementsByTagNameNS(eop_encoder.ns_dict["eop"], "Footprint")[0]
                old_footprint.parentNode.replaceChild(new_footprint, old_footprint)
        else:
            earth_observation = eop_encoder.encodeEarthObservation(coverage, poly=poly_intersection)
        
        if req is None:
            lineage = None
        else:
            if req.getParamType() == "kvp":
                lineage = self._makeElement(
                    "wcseo", "lineage", [
                        ("wcseo", "referenceGetCoverage", [
                            ("ows", "Reference", [
                                ("@xlink", "href", req.http_req.build_absolute_uri().replace("&", "&amp;"))
                            ])
                        ]),
                        ("gml", "timePosition", isotime(datetime.now()))
                    ]
                )
            elif req.getParamType() == "xml":
                post_dom = minidom.parseString(req.params)
                post_xml = post_dom.documentElement
                
                lineage = self._makeElement(
                    "wcseo", "lineage", [
                        ("wcseo", "referenceGetCoverage", [
                            ("ows", "ServiceReference", [
                                ("@xlink", "href", req.http_req.build_absolute_uri()),
                                ("ows", "RequestMessage", post_xml)
                            ])
                        ]),
                        ("gml", "timePosition", isotime(datetime.now()))
                    ]
                )
            else:
                lineage = None
        
        if lineage is None:
            return self._makeElement("gmlcov", "metadata", [
                ("wcseo", "EOMetadata", [
                    (earth_observation,),
                ]),
            ])
        else:
            return self._makeElement("gmlcov", "metadata", [
                ("wcseo", "EOMetadata", [
                    (earth_observation,),
                    (lineage,)
                ]),
            ])

    def encodeContents(self):
        return self._makeElement("wcs", "Contents", [])

    def encodeCoverageSummary(self, coverage):
        return self._makeElement("wcs", "CoverageSummary", [
            ("wcs", "CoverageId", coverage.getCoverageId()),
            ("wcs", "CoverageSubtype", coverage.getEOCoverageSubtype()),
        ])

    def encodeCoverageDescription(self, coverage):
        return self._makeElement("wcs", "CoverageDescription", [
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(*coverage.getWGS84Extent()),),
            ("wcs", "CoverageId", coverage.getCoverageId()),
            (self.encodeEOMetadata(coverage),),
            (self.encodeDomainSet(coverage),),
            (self.encodeRangeType(coverage),),
            ("wcs", "ServiceParameters", [
                ("wcs", "CoverageSubtype", coverage.getEOCoverageSubtype()),
            ])
        ])
    
    def encodeSubsetCoverageDescription(self, coverage, srid, size, extent):
        poly = Polygon.from_bbox(extent)
        poly.srid = srid
        poly.transform(4326)
        
        wgs84_extent = poly.extent
        
        return self._makeElement("wcs", "CoverageDescription", [
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(*wgs84_extent),),
            ("wcs", "CoverageId", coverage.getCoverageId()),
            (self.encodeEOMetadata(coverage),),
            (self.encodeSubsetDomainSet(coverage, srid, size, extent),),
            (self.encodeRangeType(coverage),),
            ("wcs", "ServiceParameters", [
                ("wcs", "CoverageSubtype", coverage.getEOCoverageSubtype()),
            ])
        ])
    
    def encodeDatasetSeriesDescription(self, dataset_series):
        return self._makeElement("wcseo", "DatasetSeriesDescription", [
            ("@gml", "id", self._getGMLId(dataset_series.getEOID())),
            (self.encodeBoundedBy(*dataset_series.getWGS84Extent()),),
            ("wcseo", "DatasetSeriesId", dataset_series.getEOID()),
            (self.encodeTimePeriod(dataset_series),),
#            ("wcseo", "ServiceParameters", [
# TODO: Include all referenced EO Coverages:            
#                ("wcseo", "rectifiedDataset", datasetseries.getCoverageSubtype()),
#                ("wcseo", "referenceableDataset", datasetseries.getCoverageSubtype()),
#                ("wcseo", "rectifiedStitchedMosaic", datasetseries.getCoverageSubtype()),
#                ("wcseo", "referenceableStitchedMosaic", datasetseries.getCoverageSubtype()),
#            ])
        ])

    def encodeDatasetSeriesDescriptions(self, datasetseriess):
        return self._makeElement("wcseo", "DatasetSeriesDescriptions", [
            (self.encodeDatasetSeriesDescription(datasetseries),) for datasetseries in datasetseriess
        ])
        
    def encodeEOCoverageSetDescription(self, datasetseriess, coverages, numberMatched=None, numberReturned=None):
        if numberMatched is None:
            numberMatched = len(coverages)
        if numberReturned is None:
            numberReturned = len(coverages)
            
        root_element = self._makeElement("wcseo", "EOCoverageSetDescription", [
            ("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"),
            ("", "@numberMatched", str(numberMatched)),
            ("", "@numberReturned", str(numberReturned)),
        ])
        
        if coverages is not None and len(coverages) != 0:
            root_element.appendChild(self.encodeCoverageDescriptions(coverages))
        if datasetseriess is not None and len(datasetseriess) != 0:
            root_element.appendChild(self.encodeDatasetSeriesDescriptions(datasetseriess))
        
        return root_element

    def encodeEOProfiles(self):
        return [self._makeElement("ows", "Profile", "http://www.opengis.net/spec/WCS_application-profile_earth-observation/1.0/conf/eowcs"),
                self._makeElement("ows", "Profile", "http://www.opengis.net/spec/WCS_application-profile_earth-observation/1.0/conf/eowcs_get-kvp")]

    def encodeDescribeEOCoverageSetOperation(self, http_service_url):
        return self._makeElement("ows", "Operation", [
            ("", "@name", "DescribeEOCoverageSet"),
            ("ows", "DCP", [
                ("ows", "HTTP", [
                    ("ows", "Get", [
                        ("@xlink", "href", "%s?" % http_service_url),
                        ("@xlink", "type", "simple")
                    ]),
                    ("ows", "Post", [
                        ("@xlink", "href", "%s?" % http_service_url),
                        ("@xlink", "type", "simple"),
                        ("ows", "Constraint", [
                            ("@", "name", "PostEncoding"),
                            ("ows", "AllowedValues", [
                                ("ows", "Value", "XML")
                            ])
                        ])
                    ])
                ])
            ])
        ])
    
    def encodeWGS84BoundingBox(self, dataset_series):
        minx, miny, maxx, maxy = dataset_series.getWGS84Extent()
        
        return self._makeElement("ows", "WGS84BoundingBox", [
            ("ows", "LowerCorner", _adjustPrecision("%f %f") % (minx, miny)),
            ("ows", "UpperCorner", _adjustPrecision("%f %f") % (maxx, maxy))
        ])
    
    def encodeTimePeriod(self, dataset_series):
        return self._makeElement("gml", "TimePeriod", [
            ("@gml", "id", self._getGMLId("%s_timeperiod" % dataset_series.getEOID())),
            ("gml", "beginPosition", dataset_series.getBeginTime().strftime("%Y-%m-%dT%H:%M:%S")),
            ("gml", "endPosition", dataset_series.getEndTime().strftime("%Y-%m-%dT%H:%M:%S"))
        ])

    def encodeDatasetSeriesSummary(self, dataset_series):
        return self._makeElement("wcseo", "DatasetSeriesSummary", [
            (self.encodeWGS84BoundingBox(dataset_series),),
            ("wcseo", "DatasetSeriesId", dataset_series.getEOID()),
            (self.encodeTimePeriod(dataset_series),)
        ])

    def encodeRectifiedDataset(self, dataset, req=None, nodes=None, poly=None):
        root_element = self._makeElement("wcseo", "RectifiedDataset", [
            ("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"),
            ("@gml", "id", dataset.getCoverageId())
        ])
        
        if nodes is not None:
            for node in nodes:
                root_element.appendChild(node.cloneNode(deep=True))
        #else: TODO
                
        root_element.appendChild(self.encodeEOMetadata(dataset, req, poly=poly))
        
        return root_element
        
    def encodeRectifiedStitchedMosaic(self, mosaic, req=None, nodes=None, poly=None):
        root_element = self._makeElement("wcseo", "RectifiedStitchedMosaic", [
            ("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"),
            ("@gml", "id", mosaic.getCoverageId())
        ])

        if nodes is not None:
            for node in nodes:
                root_element.appendChild(node.cloneNode(deep=True))
        #else: TODO
        
        root_element.appendChild(self.encodeEOMetadata(mosaic, req, poly=poly))
        
        root_element.appendChild(self._makeElement(
            "wcseo", "datasets", self.encodeContributingDatasets(mosaic, poly)
        ))
        
        return root_element
    def encodeCountDefaultConstraint(self, count):
        return self._makeElement("ows", "Constraint", [
            ("", "@name", "CountDefault"),
            ("ows", "NoValues", ""),
            ("ows", "DefaultValue", count)
        ])
