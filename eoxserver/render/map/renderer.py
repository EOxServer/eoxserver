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

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.render.map.config import (
    DEFAULT_EOXS_MAP_RENDERER, DEFAULT_EOXS_LEGEND_RENDERER
)


MAP_RENDERER = None
LEGEND_RENDERER = None


def get_map_renderer():
    global MAP_RENDERER
    if MAP_RENDERER is None:
        specifier = getattr(
            settings, 'EOXS_MAP_RENDERER', DEFAULT_EOXS_MAP_RENDERER
        )

        MAP_RENDERER = import_string(specifier)()

    return MAP_RENDERER


def get_legend_renderer():
    global LEGEND_RENDERER
    if LEGEND_RENDERER is None:
        specifier = getattr(
            settings, 'EOXS_LEGEND_RENDERER', DEFAULT_EOXS_LEGEND_RENDERER
        )

        LEGEND_RENDERER = import_string(specifier)()

    return LEGEND_RENDERER

