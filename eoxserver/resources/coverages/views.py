import os.path
from zipfile import ZipFile
import json
try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO
import traceback
import re
import mimetypes
import shutil

from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, FileResponse,
    Http404
)
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config
from eoxserver.contrib.vsi import VSIFileResponse
from eoxserver.backends.access import vsi_open
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration.product import (
    ProductRegistrator
)
from eoxserver.resources.coverages.registration.browse import BrowseRegistrator
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


def metadata(request, identifier, semantic):
    """ View to retrieve metadata files for a specific product.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    frmt = request.GET.get('format')

    try:
        semantic_code = {
            name: code
            for code, name in models.MetaDataItem.SEMANTIC_CHOICES
        }[semantic]
    except KeyError as exc:
        raise Http404(semantic) from exc

    qs = models.MetaDataItem.objects.filter(
        eo_object__identifier=identifier, semantic=semantic_code,
    )
    if frmt:
        qs = qs.filter(format=frmt)

    metadata_item = get_object_or_404(qs)

    return VSIFileResponse(
        vsi_open(metadata_item),
        content_type=metadata_item.format
    )


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
    except Exception as e:
        return HttpResponseBadRequest('Failed to open ZIP file: %s' % e)

    try:
        with zipfile as zipfile, transaction.atomic():
            product_desc = json.load(zipfile.open('product.json'))
            granules_desc = json.load(zipfile.open('granules.json'))

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

            product = _register_product(collection, product_desc, granules_desc)

            _add_metadata(
                product, zipfile, 'description.html', 'documentation',
                'text/html',
            )
            _add_metadata(
                product, zipfile, 'thumbnail\.(png|jpeg|jpg)', 'thumbnail'
            )
            _add_metadata(
                product, zipfile, 'metadata\.xml', 'description', 'text/xml'
            )

            granules = []
            # iterate over the granules and register them
            for granule_desc in granules_desc['features']:
                coverage = _register_granule(
                    product, collection, granule_desc
                )
                granules.append(coverage)

                # add the coverage to the product
                models.product_add_coverage(product, coverage)

            models.collection_insert_eo_object(collection, product)
            models.collection_collect_metadata(
                collection, product_summary=True, coverage_summary=True
            )

    except (KeyError, ValueError) as e:
        return HttpResponseBadRequest(str(e))
    except Exception:
        return HttpResponseBadRequest(traceback.format_exc())

    return HttpResponse(
        'Successfully registered product %s with granules: %s'
        % (product.identifier, ', '.join(
            granule.identifier for granule in granules
        ))
    )


def _register_product(collection, product_def, granules_def):
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
        discover_masks=False,
        discover_browses=False,
        discover_metadata=False,
        replace=True,
    )

    browse_locations = []
    features = granules_def['features']
    if len(features) == 1:
        location = features[0]['properties'].get('location')
        if location:
            browse_locations.append(location)
    else:
        browse_locations = [
            granule_desc['properties']['location']
            for granule_desc in features
            if granule_desc['properties'].get('band') == 'TCI'
        ]
    for browse_location in browse_locations:
        BrowseRegistrator().register(
            product.identifier, [browse_location]
        )

    return product


def _register_granule(product, collection, granule_def):
    properties = granule_def['properties']
    coverage_types_base = models.CoverageType.objects.filter(
        allowed_collection_types__collections=collection
    )

    if 'band' in properties:
        # get the coverage type associated with the collection and the granules
        # band ID
        identifier = '%s_%s' % (product.identifier, properties['band'])
        coverage_type = coverage_types_base.get(
            name__iendswith=properties['band']
        )

    else:
        # for a lack of a better generic way, just get the first allowed
        # coverage type associated with the collection
        identifier = os.path.basename(properties['location'])
        coverage_type = coverage_types_base[0]

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


def _add_metadata(product, zipfile, pattern, semantic, frmt=None):
    def _get_file_info(zipfile, pattern):
        for info in zipfile.infolist():
            if re.match(pattern, info.filename):
                return info

    reader = RegistrationConfigReader(get_eoxserver_config())
    metadata_filename_template = reader.metadata_filename_template

    info = _get_file_info(zipfile, pattern)
    if info and metadata_filename_template:
        frmt = frmt or mimetypes.guess_type(info.filename)[0]

        semantic_code = {
            name: code
            for code, name in models.MetaDataItem.SEMANTIC_CHOICES
        }[semantic]

        out_filename = metadata_filename_template.format(
            product_id=product.identifier, filename=info.filename
        )

        out_dirname = os.path.dirname(out_filename)

        # make directories
        try:
            os.makedirs(out_dirname)
        except OSError as exc:
            if exc.errno != 17:
                raise

        with open(out_filename, "w") as out_file:
            shutil.copyfileobj(zipfile.open(info), out_file)

        models.MetaDataItem.objects.create(
            eo_object=product, format=frmt, location=out_filename,
            semantic=semantic_code
        )


class RegistrationConfigReader(config.Reader):
    section = "coverages.registration"
    metadata_filename_template = config.Option()
