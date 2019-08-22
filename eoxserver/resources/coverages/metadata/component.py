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

from eoxserver.contrib.vsi import open as vsi_open

from eoxserver.resources.coverages.metadata.product_formats import get_readers


class ProductMetadataComponent(object):
    def read_product_metadata_file(self, path):
        for reader_cls in get_readers():
            reader = reader_cls()

            if hasattr(reader, 'test_path') and reader.test_path(path):
                return reader.read_path(path)
            elif hasattr(reader, 'test'):
                try:
                    f = vsi_open(path)
                except IOError:
                    continue

                if reader.test(f):
                    f.seek(0)
                    return reader.read(f)

        if f:
            f.close()

        return {}

    def collect_package_metadata(self, storage, handler, cache=None):
        path = handler.get_vsi_path(storage.url)
        for reader_cls in get_readers():
            reader = reader_cls()
            if hasattr(reader, 'test_path'):
                if reader.test_path(path):
                    return reader.read_path(path)
            else:
                try:
                    with open(path) as f:
                        if hasattr(reader, 'test') and f and reader.test(f):
                            return reader.read(f)
                except IOError:
                    pass

        raise Exception('No suitable metadata reader found.')
