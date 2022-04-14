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

import os
from os.path import basename, join, relpath, split
from itertools import chain

from django.http.response import StreamingHttpResponse, FileResponse
import zipstream

from eoxserver.backends.access import vsi_open
from eoxserver.backends.storages import get_handler_for_model
from eoxserver.core.decoders import kvp, typelist, lower
from eoxserver.resources.coverages import models
from eoxserver.services.ows.dseo.v10.encoders import DSEO10CapabilitiesXMLEncoder


class MissingProductError(Exception):
    pass


class GetCapabilitiesHandler(object):
    service = 'DSEO'
    request = 'GetCapabilities'
    versions = ['1.0', '1.0.0']
    methods = ['GET']

    def handle(self, request):
        decoder = GetCapabilitiesKVPDecoder(request.GET)
        encoder = DSEO10CapabilitiesXMLEncoder()

        return encoder.serialize(
            encoder.encode_capabilities(request, decoder.sections),
            pretty_print=True
        ), encoder.content_type


class GetProductHandler(object):
    service = 'DSEO'
    request = 'GetProduct'
    versions = ['1.0', '1.0.0']
    methods = ['GET']

    def handle(self, request):
        decoder = GetProductKVPDecoder(request.GET)
        product_uri = decoder.product_uri

        try:
            product = models.Product.objects.get(identifier=product_uri)
        except models.Product.DoesNotExist:
            raise MissingProductError("Requested product is missing")

        package = product.package
        if package and package.parent is None:
            handler = get_handler_for_model(package)
            if handler.name in ('ZIP', 'TAR'):
                response = FileResponse(
                    open(package.url), content_type='application/octet-stream',
                )
                response['Content-Disposition'] = 'attachment; filename="%s"' % (
                    basename(package.url)
                )
                return response

            elif handler.name == 'directory':
                zip_stream = zipstream.ZipFile(
                    mode='w', compression=zipstream.ZIP_DEFLATED
                )
                # compute a base path name, in order to have the last part of
                # the path always in the filename
                base = split(
                    package.url[:-1] if package.url.endswith('/')
                    else package.url
                )[0]
                for root, _, filenames in os.walk(package.url):
                    for filename in filenames:
                        path = join(root, filename)
                        zip_stream.write(path, relpath(path, base))
                response = StreamingHttpResponse(
                    zip_stream, content_type='application/octet-stream'
                )
                response['Content-Disposition'] = \
                    'attachment; filename="%s.zip"' % product.identifier

                return response

        elif package:
            # TODO: determine whether the files are local. if yes then unpack
            # from parent storage
            raise NotImplementedError

        else:
            # for each coverage iterate over all metadata and array
            # metadata files and create a ZIP on the fly

            zip_stream = zipstream.ZipFile(
                mode='w', compression=zipstream.ZIP_DEFLATED
            )

            for coverage in product.coverages.all():
                items = chain(
                    coverage.arraydata_items.all(),
                    coverage.metadata_items.all()
                )
                for data_item in items:
                    add_item_to_zipstream(data_item, zip_stream, product, coverage)

            # add product metadata
            product_items = chain(
                product.metadata_items.all()
            )
            for metadata_item in product_items:
                add_item_to_zipstream(metadata_item, zip_stream, product, None)

            response = StreamingHttpResponse(
                zip_stream, content_type='application/octet-stream'
            )
            response['Content-Disposition'] = 'attachment; filename="%s.zip"' % (
                product.identifier
            )
            return response


# helper function to iterate over a data item in chunks
def _iter_data_item(data_item, chunk_size=65535):
    with vsi_open(data_item) as vsi_file:
        while True:
            data = vsi_file.read(chunk_size)
            if data:
                yield data
            else:
                break


def add_item_to_zipstream(data_item, zip_stream, product, coverage):
    if coverage:
        filepath = join(
            product.identifier,
            coverage.identifier,
            basename(data_item.location)
        )
    else:
        filepath = join(
            product.identifier,
            basename(data_item.location)
        )
    # faster encoding when local files. Fallback on VSI API otherwise
    if not data_item.storage:
        zip_stream.write(
            data_item.location,
            filepath
        )
    else:
        zip_stream.write_iter(
            filepath,
            _iter_data_item(data_item)
        )


class GetCapabilitiesKVPDecoder(kvp.Decoder):
    sections = kvp.Parameter(type=typelist(lower, ","), num="?", default=["all"])
    updatesequence = kvp.Parameter(num="?")
    acceptversions = kvp.Parameter(type=typelist(str, ","), num="?")
    acceptformats = kvp.Parameter(type=typelist(str, ","), num="?", default=["text/xml"])
    acceptlanguages = kvp.Parameter(type=typelist(str, ","), num="?")


class GetProductKVPDecoder(kvp.Decoder):
    product_uri = kvp.Parameter('producturi', num=1)
