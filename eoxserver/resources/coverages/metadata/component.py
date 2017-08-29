#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from eoxserver.resources.coverages.metadata.product_formats.sentinel2 import (
    S2ProductFormatReader
)


class ProductMetadataComponent(object):
    # metadata_readers = ExtensionPoint(ProductMetadataReaderInterface)
    metadata_readers = [S2ProductFormatReader]

    def get_reader_by_test(self, path):
        try:
            f = open(path)
        except IOError:
            f = None

        for reader_cls in self.metadata_readers:
            reader = reader_cls()
            if hasattr(reader, 'test_path') and reader.test_path(path):
                return reader
            elif hasattr(reader, 'test') and f and reader.test(f):
                return reader

        if f:
            f.close()

        return None

    def collect_metadata(self, data_items, cache=None):
        collected_metadata = {}
        for data_item in data_items:
            path = retrieve(data_item, cache)
            reader = self.get_reader_by_test(path)
            if reader:
                if hasattr(reader, 'read_path'):
                    metadata = reader.read_path(path)
                else:
                    with open(path) as f:
                        metadata = reader.read(f)

                metadata.update(collected_metadata)
                collected_metadata = metadata
        return collected_metadata

    def collect_package_metadata(self, storage, cache=None):
        # path = retrieve(storage, cache)
        path = storage.url
        reader = self.get_reader_by_test(path)
        if reader:
            if hasattr(reader, 'read_path'):
                return reader.read_path(path)
            else:
                try:
                    with open(path) as f:
                        return reader.read(f)
                except IOError:
                    pass

        raise Exception('No suitable metadata reader found.')
