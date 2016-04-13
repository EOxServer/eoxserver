import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from eoxserver.core.util.xmltools import etree
from eoxserver.contrib import gdal, ogr

NSMAP = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'atom': 'http://www.w3.org/2005/Atom'
}


class GeoJSONMixIn(object):
    format_name = 'json'

    def get_ids(self, response):
        data = json.loads(response.content)
        return [
            feature['properties']['id'] for feature in data['features']
        ]


class KMLMixIn(object):
    format_name = 'kml'

    def get_ids(self, response):
        tree = etree.fromstring(response.content)
        return tree.xpath(
            'kml:Document/kml:Folder/kml:Placemark/kml:ExtendedData/'
            'kml:SchemaData/kml:SimpleData[@name="id"]/text()',
            namespaces=NSMAP
        )


class AtomMixIn(object):
    format_name = 'atom'

    def get_ids(self, response):
        ids = []
        gdal.FileFromMemBuffer('/vsimem/temp', response.content)

        ds = ogr.Open('/vsimem/temp')
        lyr = ds.GetLayer(0)
        feat = lyr.GetNextFeature()
        while feat is not None:
            ids.append(feat.GetFieldAsString('id'))
            feat.Destroy()
            feat = lyr.GetNextFeature()

        ds.Destroy()
        gdal.Unlink('/vsimem/temp')
        return ids


class RSSMixIn(object):
    format_name = 'rss'

    def get_ids(self, response):
        ids = []
        gdal.FileFromMemBuffer('/vsimem/temp', response.content)

        ds = ogr.Open('/vsimem/temp')
        lyr = ds.GetLayer(0)
        feat = lyr.GetNextFeature()
        while feat is not None:
            ids.append(feat.GetFieldAsString('title'))
            feat.Destroy()
            feat = lyr.GetNextFeature()

        ds.Destroy()
        gdal.Unlink('/vsimem/temp')
        return ids


class BaseSearchMixIn(object):
    fixtures = [
        "range_types.json", "meris_range_type.json",
        "meris_coverages_uint16.json", "meris_coverages_rgb.json",
        "meris_coverages_reprojected_uint16.json",
        "asar_range_type.json", "asar_coverages.json"
    ]

    def setUp(self):
        client = Client()

        self.response = client.get(
            reverse('opensearch:collection:search',
                kwargs={
                    'collection_id': self.collection_id,
                    'format_name': self.format_name
                }
            ),
            self.request
        )

    def tearDown(self):
        pass

    def test_ids(self):
        self.assertItemsEqual(self.expected_ids, self.get_ids(self.response))


class CollectionSearchMixIn(BaseSearchMixIn):
    def test_links(self):
        if self.format_name in ("rss", "atom"):
            pass


class RecordSearchMixIn(BaseSearchMixIn):
    def test_links(self):
        if self.format_name in ("rss", "atom"):
            pass


class SearchFullJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {}
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
    ]


class SearchFullTestAtomCase(AtomMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {}
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
    ]


class SearchFullRSSTestCase(RSSMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {}
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
    ]


class SearchFullKMLTestCase(KMLMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {}
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
    ]


class SearchCountJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {
        'count': '2'
    }
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"
    ]


class SearchStartIndexJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {
        'startIndex': '1'
    }
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
    ]


class SearchStartIndexCountJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {
        'startIndex': '1',
        'count': '1'
    }
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"
    ]


class SearchTemporalStartJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {
        'start': '2006-08-30T10:09:49Z'
    }
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
    ]


class SearchTemporalEndJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {
        'end': '2006-08-30T10:09:48Z'
    }
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"
    ]


class SearchTemporalStartEndJSONTestCase(GeoJSONMixIn, RecordSearchMixIn, TestCase):
    collection_id = "MER_FRS_1P_reduced_RGB"
    request = {
        'start': '2006-08-18T09:09:29Z',
        'end': '2006-08-30T10:09:48Z'
    }
    expected_ids = [
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"
    ]

# TODO: timerel tests

# TODO: bbox tests

# TODO: geometry tests

# TODO: lat/lon/radius tests

# TODO: georel tests

# TODO: combined tests
