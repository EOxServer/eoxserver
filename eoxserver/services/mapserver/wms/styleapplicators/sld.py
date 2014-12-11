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

import logging

try:
    from eoxserver.contrib.mapserver import MS_VERSION_NUM
except ImportError:
    MS_VERSION_NUM = 0

from eoxserver.core import Component, implements
from eoxserver.backends.access import connect
from eoxserver.services.mapserver.interfaces import StyleApplicatorInterface


logger = logging.getLogger(__name__)


# Versions smaller than 6.2 result in a segfault in this operation.
if MS_VERSION_NUM >= 60200:
    class SLDStyleApplicator(Component):
        implements(StyleApplicatorInterface)

        def apply(self, coverage, data_items, layer):
            sld_items = filter(lambda d: (
                d.semantic.startswith("style") and d.format.upper() == "SLD"
            ), data_items)

            for sld_item in sld_items:
                sld_filename = connect(sld_item)
                with open(sld_filename) as f:
                    layer.map.applySLD(f.read())
