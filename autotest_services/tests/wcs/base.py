

from lxml import etree

class WCS11GetCoverageMixIn(object):
    def prepareXMLData(self, xml_data):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_data, parser)

        try:
            reference = tree.xpath("wcs:Coverage/ows:Reference", 
                namespaces={
                    "wcs": "http://www.opengis.net/wcs/1.1", 
                    "ows": "http://www.opengis.net/ows/1.1"
                }
            )[0]

            href = reference.attrib["{http://www.w3.org/1999/xlink}href"]

            begin = href.rfind("_")
            end = href.rfind(".")

            href = "%s%s" % (href[:begin], href[end:])

            reference.attrib["{http://www.w3.org/1999/xlink}href"] = href
            return etree.tostring(
                tree, pretty_print=True, encoding='UTF-8', xml_declaration=True
            )
        except:
            return xml_data[:]


class WCS20GetCoverageMixIn(object):
    def prepareXMLData(self, xml_data):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_data, parser)

        try:
            range_parameters = tree.xpath(
                "gml:rangeSet/gml:File/gml:rangeParameters", 
                namespaces={"gml": "http://www.opengis.net/gml/3.2"}
            )[0]

            file_reference = tree.xpath(
                "gml:rangeSet/gml:File/gml:fileReference", 
                namespaces={"gml": "http://www.opengis.net/gml/3.2"}
            )[0]

            href = range_parameters.attrib["{http://www.w3.org/1999/xlink}href"]

            begin = href.rfind("_")
            end = href.rfind(".")

            href = "%s%s" % (href[:begin], href[end:])

            range_parameters.attrib["{http://www.w3.org/1999/xlink}href"] = href
            file_reference.text = href
            return etree.tostring(
                tree, pretty_print=True, encoding='UTF-8', xml_declaration=True
            )
        except:
            return xml_data[:] 