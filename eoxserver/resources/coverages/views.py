import os.path
from zipfile import ZipFile
import json
from cStringIO import StringIO
import traceback

from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
)
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models import Q

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration.product import (
    ProductRegistrator
)
from eoxserver.resources.coverages.registration.registrators.gdal import (
    GDALRegistrator
)

# def browse_view(request, identifier):
#     browse_type = request.GET.get('type')
#     style = request.GET.get('style')

#     qs = models.Browse.objects.filter(
#         product__identifier=identifier,
#         style=style
#     )

#     if browse_type:
#         qs = qs.filter(browse_type__name=browse_type)
#     else:
#         qs = qs.filter(browse_type__isnull=True)

#     browse = qs.get()

#     ds = gdal.Open(get_vsi_path(browse))
#     tmp_file = vsi.TemporaryVSIFile.from_buffer('')
#     driver = gdal.GetDriverByName('PNG')

#     gt = ds.GetGeoTransform()

#     out_ds = driver.Create(tmp_file.name, 500, 500, 3)
#     out_ds.SetGeoTransform([
#         gt[0],
#     )


#     driver.CreateCopy(tmp_file.name, ds)

#     ds = None

#     return HttpResponse(tmp_file.read(), content_type='image/png')


def product_register(request):
    """ View to register a Product + 'Granules' (coverages) from a so-called
        'product.zip', entailing metadata and referencing local files.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    content = request.read()

    try:
        buffered_file = StringIO(content)
        zipfile = ZipFile(buffered_file)
    except Exception, e:
        return HttpResponseBadRequest('Failed to open ZIP file: %s' % e)

    try:
        with zipfile as zipfile, transaction.atomic():
            product_desc = json.load(zipfile.open('product.json'))

            # get the collection from the 'parentId'
            try:
                parent_id = product_desc['properties']['eop:parentIdentifier']
                collection = models.Collection.objects.get(identifier=parent_id)
            except KeyError:
                return HttpResponseBadRequest(
                    'Missing product property: eop:parentIdentifier'
                )
            except models.Collection.DoesNotExist:
                return HttpResponseBadRequest(
                    'No such collection %r' % parent_id
                )

            product = _register_product(collection, product_desc)

            granules = []
            granules_desc = json.load(zipfile.open('granules.json'))

            # iterate over the granules and register them
            for granule_desc in granules_desc['features']:
                coverage = _register_granule(
                    product, collection, granule_desc
                )
                granules.append(coverage)

                # add the coverage to the product
                models.product_add_coverage(product, coverage)

            models.collection_insert_eo_object(collection, product)
            models.collection_collect_metadata(collection)

    except (KeyError, ValueError), e:
        return HttpResponseBadRequest(str(e))
    except Exception:
        return HttpResponseBadRequest(traceback.format_exc())

    return HttpResponse(
        'Successfully registered product %s with granules: %s'
        % (product.identifier, ', '.join(
            granule.identifier for granule in granules
        ))
    )


def _register_product(collection, product_def):
    type_name = None
    collection_type = collection.collection_type

    # get the first product type from the collection
    if collection_type:
        product_type = collection_type.allowed_product_types.first()
        if product_type:
            type_name = product_type.name

    properties = product_def['properties']

    footprint = GEOSGeometry(json.dumps(product_def['geometry'])).wkt
    identifier = properties['eop:identifier']
    begin_time = properties['timeStart']
    end_time = properties['timeEnd']

    location = properties['originalPackageLocation']

    product, _ = ProductRegistrator().register(
        metadata_locations=[],
        mask_locations=[],
        package_path=location,
        overrides=dict(
            identifier=identifier,
            footprint=footprint,
            begin_time=begin_time,
            end_time=end_time,
            **properties
        ),
        type_name=type_name,
        replace=True,
    )

    return product


def _register_granule(product, collection, granule_def):
    properties = granule_def['properties']
    coverage_types_base = models.CoverageType.objects.filter(Q(
        allowed_collection_types__collections=collection
    ) | Q(
        allowed_product_types__allowed_collection_types__collections=collection
    ))

    if 'band' in properties:
        # get the coverage type associated with the collection and the granules
        # band ID
        identifier = '%s_%s' % (product.identifier, properties['band'])
        coverage_type = coverage_types_base.get(
            name__endswith=properties['band']
        )

    else:
        # for a lack of a better generic way, just get the first allowed
        # coverage type associated with the collection
        identifier = os.path.basename(properties['location'])
        coverage_type = coverage_types_base[0]

        print coverage_type

    overrides = dict(
        identifier=identifier,
        begin_time=product.begin_time,
        end_time=product.end_time,
        footprint=GEOSGeometry(json.dumps(granule_def['geometry'])).wkt
    )

    return GDALRegistrator().register(
        data_locations=[[properties['location']]],
        metadata_locations=[],
        coverage_type_name=coverage_type.name,
        overrides=overrides,
        replace=True,
    ).coverage
