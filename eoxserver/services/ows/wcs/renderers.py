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

from eoxserver.services.ows.wcs.config import (
    DEFAULT_EOXS_CAPABILITIES_RENDERERS,
    DEFAULT_EOXS_COVERAGE_DESCRIPTION_RENDERERS,
    DEFAULT_EOXS_COVERAGE_RENDERERS,
)

COVERAGE_RENDERERS = None
COVERAGE_DESCRIPTION_RENDERERS = None
CAPABILITIES_RENDERERS = None


def _setup_capabilities_renderers():
    global CAPABILITIES_RENDERERS
    specifiers = getattr(
        settings, 'EOXS_CAPABILITIES_RENDERERS',
        DEFAULT_EOXS_CAPABILITIES_RENDERERS
    )
    CAPABILITIES_RENDERERS = [
        import_string(identifier)()
        for identifier in specifiers
    ]


def _setup_coverage_description_renderers():
    global COVERAGE_DESCRIPTION_RENDERERS
    specifiers = getattr(
        settings, 'EOXS_COVERAGE_RENDERERS',
        DEFAULT_EOXS_COVERAGE_DESCRIPTION_RENDERERS
    )
    COVERAGE_DESCRIPTION_RENDERERS = [
        import_string(identifier)()
        for identifier in specifiers
    ]


def _setup_coverage_renderers():
    global COVERAGE_RENDERERS
    specifiers = getattr(
        settings, 'EOXS_COVERAGE_RENDERERS',
        DEFAULT_EOXS_COVERAGE_RENDERERS
    )
    COVERAGE_RENDERERS = [
        import_string(specifier)()
        for specifier in specifiers
    ]


def get_capabilities_renderer(params):
    if not CAPABILITIES_RENDERERS:
        _setup_capabilities_renderers()

    for renderer in CAPABILITIES_RENDERERS:
        if renderer.supports(params):
            return renderer
    return None


def get_coverage_description_renderer(params):
    if not COVERAGE_DESCRIPTION_RENDERERS:
        _setup_coverage_description_renderers()

    for renderer in COVERAGE_DESCRIPTION_RENDERERS:
        if renderer.supports(params):
            return renderer
    return None


def get_coverage_renderer(params):
    if not COVERAGE_RENDERERS:
        _setup_coverage_renderers()

    for renderer in COVERAGE_RENDERERS:
        if renderer.supports(params):
            return renderer
    return None
