#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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
This module contains XML encoders for WCS metadata based on GML, EO O&M,
GMLCOV, WCS 2.0 and EO-WCS.
"""


from datetime import datetime
from xml.dom import minidom

from django.contrib.gis.geos import Polygon

from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.core.util.timetools import isotime
from eoxserver.processing.mosaic import MosaicContribution

from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss 

# TODO make precision adjustable (3 decimal digits for projected axes)

PPREC1=("%.8f","%.3f") 
PPREC2=("%s %s"%(PPREC1[0],PPREC1[0]),"%s %s"%(PPREC1[1],PPREC1[1])) 

def _getUnitLabelAndFormat( epsg ) : 
    """ auxiliary function """

    is_projected = crss.isProjected( epsg )
    is_reversed  = crss.hasSwappedAxes( epsg ) 

    if is_projected : 
        axes = "y x" if is_reversed else "x y" 
        unit = "m m" 
    else:
        axes = "lat long" if is_reversed else "long lat" 
        unit = "deg deg" 

    return unit , axes , PPREC2[is_projected] , is_reversed , is_projected 


class GMLEncoder(XMLEncoder):
    """
    This encoder provides methods for encoding basic GML objects.

    Note that the axis order for the input point coordinates used in
    geometry representations is always
    (x, y) or (lon, lat). The axis order in the output coordinates on the
    other hand will be the order as mandated by the EPSG definition of
    the respective spatial reference system. This may be (y, x) for some
    projected CRSes (e.g. EPSG:3035, the European Lambert Azimuthal Equal
    Area projection used for many datasets covering Europe) and (lat,lon)
    for most geographic CRSes including EPSG:4326 (WGS 84).
    """
    def _initializeNamespaces(self):
        return {
            "gml": "http://www.opengis.net/gml/3.2"
        }
    
    def encodeLinearRing(self, ring, srid):
        """
        Returns a :mod:`xml.dom.minidom` element containing the GML
        representation of a linear ring. The ``ring`` argument is
        expected to be a list of tuples which represent 2-D point coordinates
        with (x,y)/(lon,lat) axis order. The ``srid`` argument shall contain the
        EPSG ID of the spatial reference system as an integer.
        """

        floatFormat  = PPREC2[ crss.isProjected(srid) ] 

        # get axes swapping function 
        swap = crss.getAxesSwapper( srid ) 

        pos_list = " ".join([ floatFormat%swap(*point) for point in ring])

        return self._makeElement(
            "gml", "LinearRing", [
                ("gml", "posList", pos_list)
            ]
        )

    def encodePolygon(self, poly, base_id):
        """
        This method returns a :mod:`xml.dom.minidom` element containing the GML
        representation of a polygon. The ``poly`` argument is expected to be a
        GeoDjango :class:`~django.contrib.gis.geos.Polygon` or 
        :class:`~django.contrib.gis.geos.GEOSGeometry` object containing a
        polygon. The ``base_id`` string is used to generate the required gml:id
        attributes on different elements of the polygon encoding.
        """
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
        """
        This method returns a :mod:`xml.dom.minidom` element containing the GML
        represenation of a multipolygon. The ``geom`` argument is expected to be
        a GeoDjango :class:`~django.contrib.gis.geos.GEOSGeometry` object. The 
        ``base_id`` string is used to generate the required gml:id attributes 
        on different elements of the multipolygon encoding.
        """
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
    """
    This encoder implements some encodings of EO O&M. It inherits from
    :class:`GMLEncoder`.
    """
    def _initializeNamespaces(self):
        ns_dict = super(EOPEncoder, self)._initializeNamespaces()
        ns_dict.update({
            "om": "http://www.opengis.net/om/2.0",
            "eop": "http://www.opengis.net/eop/2.0"
        })
        return ns_dict

    def encodeFootprint(self, footprint, eo_id):
        """
        Returns a :mod:`xml.dom.minidom` element containing the EO O&M
        representation of a footprint. The ``footprint`` argument shall contain
        a GeoDjango :class:`~django.contrib.gis.geos.GEOSGeometry` object 
        containing the footprint as a polygon or multipolygon. The ``eo_id`` 
        argument is passed on to the GML encoder as a base ID for generating 
        required gml:id attributes.
        """
        return self._makeElement(
            "eop", "Footprint", [
                ("@gml", "id", "footprint_%s" % eo_id),
                ("eop", "multiExtentOf", [
                    (self.encodeMultiPolygon(footprint, eo_id),)
                ])
            ]
        )
    
    def encodeMetadataProperty(self, eo_id, contributing_datasets=None):
        """
        This method returns a :mod:`xml.dom.minidom` element containing the
        EO O&M representation of an eop:metaDataProperty element.
        
        The ``eo_id`` element is reported in the eop:identifier element. If
        provided, a list of ``contributing_datasets`` descriptions will be
        included in the eop:composedOf element.
        """
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
        """
        This method returns a :mod:`xml.dom.minidom` element containing the
        EO O&M representation of an Earth Observation. It takes an
        ``eo_metadata`` object as an input that implements the
        :class:`~.EOMetadataInterface`.
        
        Note that the return value is only a minimal encoding with the
        mandatory elements.
        """
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
    """
    This encoder provides methods for obtaining GMLCOV 1.0 compliant XML
    encodings of coverage descriptions.
    """
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
        """
        This method returns a :mod:`xml.dom.minidom` element containing the
        GMLCOV represenation of the domain set for rectified or referenceable
        coverages. The ``coverage`` argument is expected to implement
        :class:`~.EOCoverageInterface`.
        
        The domain set can be represented by either a referenceable or
        a rectified grid; :meth:`encodeReferenceableGrid` or
        :meth:`encodeRectifiedGrid` are called accordingly.
        """
        if coverage.getType() == "eo.ref_dataset":
            return self._makeElement("gml", "domainSet", [
                (self.encodeReferenceableGrid( coverage.getSize(), 
                    coverage.getSRID(),
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])
        else:
            return self._makeElement("gml", "domainSet", [
                (self.encodeRectifiedGrid( coverage.getSize(),
                    coverage.getExtent(), coverage.getSRID(),
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])
    
    def encodeSubsetDomainSet(self, coverage, srid, size, extent):
        """
        This method returns a :mod:`xml.dom.minidom` element containing the
        GMLCOV representation of a domain set for subsets of rectified or
        referenceable coverages. Whereas :meth:`encodeDomainSet`
        computes the grid metadata based on the spatial reference system, extent
        and pixel size of the whole coverage, this method can be customized
        with parameters related to a subset of the coverage.
        
        The method expects four parameters: ``coverage`` shall be an object
        implementing :class:`~.EOCoverageInterface`; ``srid`` shall be the
        EPSG ID of the subset CRS (which does not have to be the same as the
        coverage CRS); ``size`` shall be a 2-tuple of width and height of the
        subset; finally the ``extent`` shall be represented by a 4-tuple
        ``(minx, miny, maxx, maxy)``.

        """
        if coverage.getType() == "eo.ref_dataset":
            return self._makeElement("gml", "domainSet", [
                (self.encodeReferenceableGrid( size, srid, 
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])
        else:
            return self._makeElement("gml", "domainSet", [
                (self.encodeRectifiedGrid( size, extent, srid,
                    "%s_grid" % coverage.getCoverageId()
                ),)
            ])


    def encodeRectifiedGrid(self, size, (minx, miny, maxx, maxy), srid, id):
        """
        This method returns a :mod:`xml.dom.minidom` element containing the
        GMLCOV representation of a rectified grid. It expects
        four parameters as input: ``size`` shall be a 2-tuple of width and
        height of the subset; the extent shall be represented by a 4-tuple
        ``(minx, miny, maxx, maxy)``; the ``srid`` shall contain the EPSG ID
        of the spatial reference system; finally, the ``id`` string is used to
        generate gml:id attributes on certain elements that require it.
        """
        
        axesUnits, axesLabels, floatFormat , axesReversed , crsProjected = \
            _getUnitLabelAndFormat( srid ) 

        # get axes swapping function 
        swap = crss.getAxesSwapper( srid , axesReversed ) 

        origin    = floatFormat % swap( minx, maxy )
        x_offsets = floatFormat % swap( ( maxx - minx )/float( size[0] ) , 0 )
        y_offsets = floatFormat % swap( 0 , ( miny - maxy )/float( size[1] ) )

        grid_element = self._makeElement("gml", "RectifiedGrid", [
            ("", "@dimension", 2),
            ("@gml", "id", self._getGMLId(id)),
            ("gml", "limits", [
                ("gml", "GridEnvelope", [
                    ("gml", "low", "0 0"),
                    ("gml", "high", "%d %d" % (size[0]-1, size[1]-1))
                ])
            ]),
            ("gml", "axisLabels", axesLabels)
        ])

        grid_element.appendChild(self._makeElement("gml", "origin", [
            ("gml", "Point", [
                ("", "@srsName", crss.asURL(srid) ),
                ("@gml", "id", self._getGMLId("%s_origin" % id)),
                ("gml", "pos", origin)
            ])
        ]))

        grid_element.appendChild(self._makeElement("gml", "offsetVector", [
            ("", "@srsName", "http://www.opengis.net/def/crs/EPSG/0/%s" % srid),
            ("", "@@", x_offsets)
        ]))
        grid_element.appendChild(self._makeElement("gml", "offsetVector", [
            ("", "@srsName", "http://www.opengis.net/def/crs/EPSG/0/%s" % srid),
            ("", "@@", y_offsets)
        ]))
                    
        return grid_element


    def encodeReferenceableGrid(self, size, srid, id):
        """
        This method returns a :mod:`xml.dom.minidom` element containig the
        GMLCOV representation of a referenceable grid. It expects
        three parameters: ``size`` is a 2-tuple of width and height of the
        grid, the ``srid`` is the EPSG ID of the spatial reference system
        and the ``id`` string is used to generate gml:id attributes on
        elements that require it.
        
        Note that the return value is a gml:ReferenceableGrid element that
        actually does not exist in the GML standard.
        
        The reason is that EOxServer geo-references datasets using ground
        control points (GCPs) provided with the dataset. With the current GML
        implementations of gml:AbstractReferenceableGrid it is not possible
        to specify only the GCPs in the description of the grid. You'd have to
        calculate and encode the coordinates of every grid point instead. This
        would blow up the XML descriptions of typical satellite scenes to
        several 100 MB - which is clearly impractical.
        
        The current implementation returns a gml:RectifiedGrid pseudo-element
        that is based on the gml:AbstractGrid structure and has about the
        following structure::
        
            <gml:ReferenceableGrid dimension="2" gml:id="some_id">
                <gml:limits>
                    <gml:GridEnvelope>
                        <gml:low>0 0</gml:low>
                        <gml:high>999 999</gml:high>
                    </gml:GridEnvelope>
                </gml:limits>
                <gml:axisLabels>lon lat</gml:axisLabels>
            </gml:ReferenceableGrid>
        """
        axesUnits, axesLabels, floatFormat , axesReversed , crsProjected = \
            _getUnitLabelAndFormat( srid ) 

        grid_element = self._makeElement("gml", "ReferenceableGrid", [
            ("", "@dimension", 2),
            ("@gml", "id", self._getGMLId(id)),
            ("gml", "limits", [
                ("gml", "GridEnvelope", [
                    ("gml", "low", "0 0"),
                    ("gml", "high", "%d %d" % (size[0]-1, size[1]-1))
                ])
            ]),
            ("gml", "axisLabels", axesLabels)
        ])
        
        return grid_element


    def encodeBoundedBy(self, (minx, miny, maxx, maxy), srid = 4326 ):
        """
        This method returns a :mod:`xml.dom.minidom` element representing the
        gml:boundedBy element. It expects the extent as a 4-tuple
        ``(minx, miny, maxx, maxy)``. The ``srid`` parameter is optional and
        represents the EPSG ID of the spatial reference system as an integer;
        default is 4326.
        """
        axesUnits, axesLabels, floatFormat , axesReversed , crsProjected = \
            _getUnitLabelAndFormat( srid ) 

        # get axes swapping function 
        swap = crss.getAxesSwapper( srid , axesReversed ) 

        return self._makeElement("gml", "boundedBy", [
            ("gml", "Envelope", [
                ("", "@srsName", crss.asURL( srid ) ),
                ("", "@axisLabels", axesLabels ),
                ("", "@uomLabels", axesUnits ),
                ("", "@srsDimension", 2),
                ("gml", "lowerCorner", floatFormat % swap(minx, miny) ),
                ("gml", "upperCorner", floatFormat % swap(maxx, maxy) )
            ])
        ])

    def encodeRangeType(self, coverage):
        """
        This method returns the range type XML encoding based on GMLCOV and
        SWE Common as an :mod:`xml.dom.minidom` element. The ``coverage``
        parameter shall implement :class:`~.EOCoverageInterface`.
        """
        range_type = coverage.getRangeType()
        
        return self._makeElement("gmlcov", "rangeType", [
            ("swe", "DataRecord", [
                (self.encodeRangeTypeField(range_type, band),)
                for band in range_type.bands
            ])
        ])

    def encodeRangeTypeField(self, range_type, band):
        """
        This method returns the the encoding of a SWE Common field as an
        :mod:`xml.dom.minidom` element. This XML structure represents a band in
        terms of typical EO data. The ``range_type`` parameter shall be a
        :class:`~.RangeType` object, the ``band`` parameter a :class:`~.Band`
        object.
        """
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
        """
        This method returns the SWE Common encoding of a nil value as an
        :mod:`xml.dom.minidom` element; the input parameter shall be of type
        :class:`~.NilValue`.
        """
        return self._makeElement("swe", "NilValues", [
            ("swe", "nilValue", [
                ("", "@reason", nil_value.reason),
                ("", "@@", nil_value.value)
            ])
        ])


class WCS20Encoder(CoverageGML10Encoder):
    """
    This encoder class provides methods for generating XML needed by WCS 2.0.
    It inherits from :class:`CoverageGML10Encoder`.
    """
    def _initializeNamespaces(self):
        ns_dict = super(WCS20Encoder, self)._initializeNamespaces()
        ns_dict.update({
            "wcs": "http://www.opengis.net/wcs/2.0",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        })
        return ns_dict
    
    def encodeExtension(self):
        """
        Returns an empty wcs:Extension element as an :mod:`xml.dom.minidom`
        element.
        """
        return self._makeElement("wcs", "Extension", [])
    
    def encodeCoverageDescription(self, coverage):
        """
        Returns a :mod:`xml.dom.minidom` element representing a coverage
        description. The method expects one parameter, ``coverage``, which
        shall implement the :class:`~.EOCoverageInterface`.
        """
        return self._makeElement("wcs", "CoverageDescription", [
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(coverage.getWGS84Extent()),),
            ("wcs", "CoverageId", coverage.getCoverageId()),
            (self.encodeDomainSet(coverage),),
            (self.encodeRangeType(coverage),),
            ("wcs", "ServiceParameters", [
                ("wcs", "CoverageSubtype", coverage.getCoverageSubtype()),
            ])
        ])
    
    def encodeCoverageDescriptions(self, coverages, is_root=False):
        """
        Returns a :mod:`xml.dom.minidom` element representing a
        wcs:CoverageDescriptions element. The ``coverages`` argument shall be
        a list of objects implementing :class:`~.EOCoverageInterface` whereas
        the optional ``is_root`` flag indicates that the element will be the
        document root and thus should include an xsi:schemaLocation attribute
        pointing to the EO-WCS schema; it defaults to ``False``.
        """
        if is_root:
            sub_nodes = [("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd")]
        else:
            sub_nodes = []
        
        if coverages is not None and len(coverages) != 0:
            sub_nodes.extend([(self.encodeCoverageDescription(coverage),) for coverage in coverages])

        return self._makeElement("wcs", "CoverageDescriptions", sub_nodes)


class WCS20EOAPEncoder(WCS20Encoder):
    """
    This encoder provides methods for generating EO-WCS compliant XML
    descriptions.
    """
    def _initializeNamespaces(self):
        ns_dict = super(WCS20EOAPEncoder, self)._initializeNamespaces()
        ns_dict.update({
            "ows": "http://www.opengis.net/ows/2.0",
            "crs": "http://www.opengis.net/wcs/service-extension/crs/1.0",
            "wcseo": "http://www.opengis.net/wcseo/1.0",
            "xlink": "http://www.w3.org/1999/xlink"
        })
        return ns_dict
    
    def encodeContributingDatasets(self, coverage, poly=None):
        """
        This method returns a list of :mod:`xml.dom.minidom` elements containing
        wcseo:dataset descriptions of contributing datasets. This is used for
        coverage descriptions of Rectified Stitched Mosaics. The ``coverage``
        parameter shall refer to a :class:`~.RectifiedStitchedMosaicWrapper`
        object. The optional ``poly`` argument may contain a GeoDjango
        :class:`~django.contrib.gis.geos.GEOSGeometry` object describing the 
        polygon. If it is provided, the set of contributing datasets will be 
        restricted to those intersecting the given polygon.
        """
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
        """
        This method returns a :mod:`xml.dom.minidom` element containing the
        EO Metadata description of a coverage as needed for EO-WCS descriptions.
        The method requires one argument, ``coverage``, that shall implement
        :class:`~.EOCoverageInterface`.
        
        Moreover, a :class:`~.OWSRequest` object ``req`` can be provided. If it
        is present, a wcseo:lineage element that describes the request
        arguments will be added to the metadata description.
        
        The ``include_composed_of`` and ``poly`` arguments are ignored at the
        moment.
        """
        
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
                ("gmlcov", "Extension", [
                    ("wcseo", "EOMetadata", [
                        (earth_observation,),
                    ]),
                ]),
            ])
        else:
            return self._makeElement("gmlcov", "metadata", [
                ("gmlcov", "Extension", [
                    ("wcseo", "EOMetadata", [
                        (earth_observation,),
                        (lineage,)
                    ]),
                ]),
            ])

    def encodeContents(self):
        """
        Returns an empty wcs:Contents element as :mod:`xml.dom.minidom`
        element.
        """
        return self._makeElement("wcs", "Contents", [])

    def encodeCoverageSummary(self, coverage):
        """
        This method returns a wcs:CoverageSummary element as
        :mod:`xml.dom.minidom` element. It expects a ``coverage`` object
        implementing :class:`~.EOCoverageInterface` as input.
        """
        return self._makeElement("wcs", "CoverageSummary", [
            ("wcs", "CoverageId", coverage.getCoverageId()),
            ("wcs", "CoverageSubtype", coverage.getEOCoverageSubtype()),
        ])

    def encodeCoverageDescription(self, coverage, is_root=False):
        """
        This method returns a wcs:CoverageDescription element including
        EO Metadata as :mod:`xml.dom.minidom` element. It expects one
        mandatory argument, ``coverage``, which shall implement
        :class:`~.EOCoverageInterface`. The optional ``is_root`` flag indicates
        whether the returned element will be the document root of the
        response. If yes, a xsi:schemaLocation attribute pointing to the
        EO-WCS schema will be added to the root element. It defaults to
        ``False``.
        """
        
        # retrieve the format registry 
        FormatRegistry = getFormatRegistry() 

        # get the coverage's source format 
        source_mime   = coverage.getData().getSourceFormat() 
        source_format = FormatRegistry.getFormatByMIME( source_mime ) 

        # map the source format to the native one 
        native_format = FormatRegistry.mapSourceToNativeWCS20( source_format ) 

        if is_root:
            sub_nodes = [("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd")]
        else:
            sub_nodes = []

        sub_nodes.extend([
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(coverage.getExtent(),coverage.getSRID()),),
            ("wcs", "CoverageId", coverage.getCoverageId()),
            (self.encodeEOMetadata(coverage),),
            (self.encodeDomainSet(coverage),),
            (self.encodeRangeType(coverage),),
            ("wcs", "ServiceParameters", [
                ("wcs", "CoverageSubtype", coverage.getEOCoverageSubtype()),
                ("wcs", "nativeFormat" , native_format.mimeType ) 
            ])
        ])
        return self._makeElement("wcs", "CoverageDescription", sub_nodes)

    #TODO: remove once fully supported by mapserver 
    def encodeSupportedCRSs( self ) : 
        """
        This method returns list of :mod:`xml.dom.minidom` elements containing
        the supported CRSes for a service. The CRSes are retrieved using
        :func:`eoxserver.resources.coverages.crss.getSupportedCRS_WCS`. They
        are encoded as crsSupported elements in the namespace of the WCS 2.0
        CRS extension.
        """

        # get list of supported CRSes 
        supported_crss = crss.getSupportedCRS_WCS(format_function=crss.asURL) 

        el = [] 

        for sc in supported_crss : 

            el.append( self._makeElement( "crs" , "crsSupported" , sc ) ) 

        return el 
    
    def encodeRangeSet( self , reference , mimeType ) :
        """
        This method returns a :mod:`xml.dom.minidom` element containing a
        reference to the range set of the coverage. The ``reference`` parameter
        shall refer to the file part of a multipart message. The ``mime_type``
        shall contain the MIME type of the delivered coverage.
        """
        return self._makeElement("gml", "rangeSet", 
            [( "gml","File" , 
                [("gml","rangeParameters",
                    [( "@xlink" , "arcrole" , "fileReference" ), 
                     ( "@xlink" , "href" , reference ), 
                     ( "@xlink" , "role" , mimeType ), 
                    ]),
                 ("gml","fileReference",reference), 
                 ("gml","fileStructure",[]), 
                 ("gml","mimeType",mimeType), 
                ]),
            ]) 

    def encodeReferenceableDataset( self , coverage , reference , mimeType , is_root = False , subset = None ) : 
        """
        This method returns the description of a Referenceable Dataset as a
        :mod:`xml.dom.minidom` element. It expects three input arguments:
        ``coverage`` shall be a :class:`~.ReferenceableDatasetWrapper` instance;
        ``reference`` shall be a string containing a reference to the
        coverage data; ``mime_type`` shall be a string containing the MIME type
        of the coverage data.
        
        The ``is_root`` flag indicates that the returned element is the
        document root and an xsi:schemaLocation attribute pointing to the
        EO-WCS schemas shall be added. It defaults to ``False``. The
        ``subset`` argument is optional. In case it is provided it indicates
        that the description relates to a subset of the dataset only and thus
        the metadata (domain set) shall be changed accordingly. It is expected
        to be a 4-tuple of ``(srid, size, extent, footprint)``. The ``srid``
        represents the integer EPSG ID of the CRS description. The ``size``
        contains a 2-tuple of width and height. The ``extent`` is a 4-tuple
        of ``(minx, miny, maxx, maxy)``; the coordinates shall be expressed
        in the CRS denoted by ``srid``. The ``footprint`` part is not used.
        """

        # handle subset 
        dst_srid   = coverage.getSRID() 

        if subset is None : 
            # whole area - no subset 
            domain = self.encodeDomainSet(coverage)
            eomd   = self.encodeEOMetadata(coverage)
            dst_extent = coverage.getExtent()

        else : 
        
            # subset is given 
            _srid, size, _extent, footprint = subset 

            domain = self.encodeSubsetDomainSet(coverage, _srid, size, _extent)
            eomd   = self.encodeEOMetadata(coverage, poly=footprint)

            # get the WGS84 extent
            poly = Polygon.from_bbox(_extent)
            poly.srid = _srid
            poly.transform(dst_srid)
            dst_extent = poly.extent

        sub_nodes = []  

        if is_root:
            sub_nodes.append( ("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd") )

        sub_nodes.extend([
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(dst_extent,dst_srid),),(domain,),
            (self.encodeRangeSet( reference , mimeType ),),
            (self.encodeRangeType(coverage),),(eomd,),])

        return self._makeElement("wcseo", "ReferenceableDataset", sub_nodes)


    def encodeSubsetCoverageDescription(self, coverage, srid, size, extent, footprint, is_root=False):
        """
        This method returns a :mod:`xml.dom.minidom` element containing a
        coverage description for a subset of a coverage according to WCS 2.0.
        The ``coverage`` parameter shall implement
        :class:`~.EOCoverageInterface`. The ``srid`` shall contain the
        integer EPSG ID of the output (subset) CRS. The ``size`` parameter
        shall be a 2-tuple of width and height. The ``extent`` shall be a
        4-tuple of ``(minx, miny, maxx, maxy)`` expressed in the CRS described
        by ``srid``. The ``footprint`` argument shall be a GeoDjango
        :class:`~django.contrib.gis.geos.GEOSGeometry` object containing a 
        polygon. The ``is_root`` flag indicates whether the resulting 
        wcs:CoverageDescription element is the document root of the response. 
        In that case a xsi:schemaLocation attribute pointing to the EO-WCS 
        schema will be added. It defaults to ``False``.
        """
        poly = Polygon.from_bbox(extent)
        poly.srid = srid
        poly.transform(4326)
        
        wgs84_extent = poly.extent
        
        if is_root:
            sub_nodes = [("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd")]
        else:
            sub_nodes = []
        sub_nodes.extend([
            ("@xsi", "schemaLocation", "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"),
            ("@gml", "id", self._getGMLId(coverage.getCoverageId())),
            (self.encodeBoundedBy(wgs84_extent),),
            ("wcs", "CoverageId", coverage.getCoverageId()),
            (self.encodeEOMetadata(coverage, poly=footprint),),
            (self.encodeSubsetDomainSet(coverage, srid, size, extent),),
            (self.encodeRangeType(coverage),),
            ("wcs", "ServiceParameters", [
                ("wcs", "CoverageSubtype", coverage.getEOCoverageSubtype()),
            ])
        ])
        return self._makeElement("wcs", "CoverageDescription", sub_nodes)
    
    def encodeDatasetSeriesDescription(self, dataset_series):
        """
        This method returns a :mod:`xml.dom.minidom` element representing
        a Dataset Series description. The method expects a
        :class:`~.DatasetSeriesWrapper` object ``dataset_series`` as its
        only input.
        """
        return self._makeElement("wcseo", "DatasetSeriesDescription", [
            ("@gml", "id", self._getGMLId(dataset_series.getEOID())),
            (self.encodeBoundedBy(dataset_series.getWGS84Extent()),),
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
        """
        This method returns a wcs:DatasetSeriesDescriptions element as a
        :mod:`xml.dom.minidom` element. The element contains the
        descriptions of a list of Dataset Series contained in the
        ``datasetseriess`` parameter.
        """
        if datasetseriess is not None and len(datasetseriess) != 0:
            sub_nodes = [(self.encodeDatasetSeriesDescription(datasetseries),) for datasetseries in datasetseriess]
        else:
            sub_nodes = []
        return self._makeElement("wcseo", "DatasetSeriesDescriptions", sub_nodes)
        
    def encodeEOCoverageSetDescription(self, datasetseriess, coverages, numberMatched=None, numberReturned=None):
        """
        This method returns a wcseo:EOCoverageSetDescription element (the
        response to a EO-WCS DescribeEOCoverageSet request) as a 
        :mod:`xml.dom.minidom` element.
        
        ``datasetseriess`` shall be a list of :class:`~.DatasetSeriesWrapper`
        objects. The ``coverages`` argument shall be a list of objects
        implementing :class:`~.EOCoverageInterface`. The optional
        ``numberMatched`` and ``numberReturned`` arguments are used in
        responses for pagination.
        """
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
        """
        Returns a list of ows:Profile elements referring to the WCS 2.0 profiles
        implemented by EOxServer (EO-WCS and its GET KVP binding as well as
        the CRS extension of WCS 2.0). The resulting :mod:`xml.dom.minidom`
        elements can be used in WCS 2.0 GetCapabilities responses.
        """
        return [self._makeElement("ows", "Profile", "http://www.opengis.net/spec/WCS_application-profile_earth-observation/1.0/conf/eowcs"),
                self._makeElement("ows", "Profile", "http://www.opengis.net/spec/WCS_application-profile_earth-observation/1.0/conf/eowcs_get-kvp"),
                self._makeElement("ows", "Profile", "http://www.opengis.net/spec/WCS_service-extension_crs/1.0/conf/crs")] #TODO remove once fully supported by mapserver 

    def encodeDescribeEOCoverageSetOperation(self, http_service_url):
        """
        This method returns an ows:Operation element describing the
        additional EO-WCS DescribeEOCoverageSet operation for use in the
        WCS 2.0 GetCapabilities response. The return value is - as always -
        a :mod:`xml.dom.minidom` element.
        
        The only parameter is the HTTP service URL of the EOxServer instance.
        """
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
        """
        This element returns the ows:WGS84BoundingBox for a Dataset Series.
        The input parameter shall be a :class:`~.DatasetSeriesWrapper` object.
        """
        minx, miny, maxx, maxy = dataset_series.getWGS84Extent()

        floatFormat = PPREC2[False] 

        return self._makeElement("ows", "WGS84BoundingBox", [
            ("ows", "LowerCorner", floatFormat%(minx, miny)),
            ("ows", "UpperCorner", floatFormat%(maxx, maxy))
        ])
    
    def encodeTimePeriod(self, dataset_series):
        """
        This method returns a gml:TimePeriod element referring to the
        time period of a Dataset Series. The input argument is expected to
        be a :class:`~.DatasetSeriesWrapper` object.
        """
        timeFormat = "%Y-%m-%dT%H:%M:%S"

        teoid = "%s_timeperiod" % dataset_series.getEOID()
        start = dataset_series.getBeginTime().strftime(timeFormat)
        stop  = dataset_series.getEndTime().strftime(timeFormat)

        return self._makeElement("gml", "TimePeriod", [
            ("@gml", "id", self._getGMLId(teoid) ),
            ("gml", "beginPosition", start ), 
            ("gml", "endPosition", stop ) 
        ])

    def encodeDatasetSeriesSummary(self, dataset_series):
        """
        This method returns a wcseo:DatasetSeriesSummary element referring to
        ``dataset_series``, a :class:`~.DatasetSeriesWrapper` object.
        """
        return self._makeElement("wcseo", "DatasetSeriesSummary", [
            (self.encodeWGS84BoundingBox(dataset_series),),
            ("wcseo", "DatasetSeriesId", dataset_series.getEOID()),
            (self.encodeTimePeriod(dataset_series),)
        ])

    def encodeRectifiedDataset(self, dataset, req=None, nodes=None, poly=None):
        """
        This method returns a wcseo:RectifiedDataset element describing the
        ``dataset``  object of type :class:`~.RectifiedDatasetWrapper`. The
        ``nodes`` parameter may contain a list of :mod:`xml.dom.minidom` nodes
        to be appended to the root element. The ``req`` and ``poly`` arguments
        are passed on to :meth:`encodeEOMetadata`.
        """
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
        """
        This method returns a wcseo:RectifiedStitchedMosaic element describing
        the ``mosaic``  object of type
        :class:`~.RectifiedStitchedMosaicWrapper`. The ``nodes`` parameter may
        contain a list of :mod:`xml.dom.minidom` nodes to be appended to the
        root element. The ``req`` and ``poly`` arguments are passed on to
        :meth:`encodeEOMetadata`.
        """
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
        """
        This method returns a ows:Constraint element representing the default
        maximum of descriptions in an EO-WCS DescribeEOCoverage response for use
        in WCS 2.0 GetCapabilities responses. The ``count`` argument is
        expected to contain a positive integer.
        """
        return self._makeElement("ows", "Constraint", [
            ("", "@name", "CountDefault"),
            ("ows", "NoValues", ""),
            ("ows", "DefaultValue", count)
        ])
