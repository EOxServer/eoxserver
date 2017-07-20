from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from eoxserver.contrib import gdal, vsi
from eoxserver.backends.access import get_vsi_path
from eoxserver.resources.coverages import models


def browse_view(request, identifier):
    browse_type = request.GET.get('type')
    style = request.GET.get('style')

    qs = models.Browse.objects.filter(
        product__identifier=identifier,
        style=style
    )

    if browse_type:
        qs = qs.filter(browse_type__name=browse_type)
    else:
        qs = qs.filter(browse_type__isnull=True)

    browse = qs.get()

    ds = gdal.Open(get_vsi_path(browse))
    tmp_file = vsi.TemporaryVSIFile.from_buffer('')
    driver = gdal.GetDriverByName('PNG')
    driver.CreateCopy(tmp_file.name, ds)

    ds = None

    return HttpResponse(tmp_file.read(), content_type='image/png')
