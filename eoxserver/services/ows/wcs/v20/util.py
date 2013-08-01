from lxml.builder import ElementMaker
from eoxserver.core.util.xml import NameSpace, NameSpaceMap


# namespace declarations
ns_xlink = NameSpace("http://www.w3.org/1999/xlink", "xlink")
ns_ogc = NameSpace("http://www.opengis.net/ogc", "ogc")
ns_ows = NameSpace("http://www.opengis.net/ows/2.0", "wcs")
ns_gml = NameSpace("http://www.opengis.net/gml/3.2", "gml")
ns_gmlcov = NameSpace("http://www.opengis.net/gml/3.2", "gmlcov")
ns_wcs = NameSpace("http://www.opengis.net/wcs/2.0", "ows")
ns_crs = NameSpace("http://www.opengis.net/wcs/service-extension/crs/1.0", "crs")
ns_eowcs = NameSpace("http://www.opengis.net/wcseo/1.0", "eowcs")

# namespace map
nsmap = NameSpaceMap(
    ns_xlink, ns_ogc, ns_ows, ns_gml, ns_gmlcov, ns_wcs, ns_crs, ns_eowcs
)

# Element factories
OWS = ElementMaker(namespace=ns_ows.uri, nsmap=nsmap)
GML = ElementMaker(namespace=ns_gml.uri, nsmap=nsmap)
WCS = ElementMaker(namespace=ns_wcs.uri, nsmap=nsmap)
CRS = ElementMaker(namespace=ns_crs.uri, nsmap=nsmap)
EOWCS = ElementMaker(namespace=ns_eowcs.uri, nsmap=nsmap)
