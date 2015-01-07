#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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


class RegistratorInterface(object):
    """ Interface for components that allow the registration files as datasets.
    """

    def register(self, items, overrides=None, cache=None):
        """ Register a dataset as the given ``dataset_type`` and the provided
        ``items``. All required metadata is retrieved from the
        ``items``, overrides can be specified by supplying an ``overrides``
        :class:`dict`.

        :param items: an iterable that yields four-tuples:
                      (storage or package or ``None``, location, semantic,
                      format).
        :param overrides: a :class:`dict` containing any metadata value that
                          cannot be retrieved from the supplied ``data_items``,
                          or shall override any supplied value
        :param cache: an instance of :class:`CacheContext
                      <eoxserver.backends.cache.CacheContext>` for cached file
                      access during registration
        :returns: the registered dataset. the actual type depends on the passed
                  metadata
        """
        pass
