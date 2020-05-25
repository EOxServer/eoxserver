# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------


from django.conf import settings
from django.utils.module_loading import import_string


FEATURE_INFO_FORMATS = None

DEFAULT_EOXS_FEAUTURE_INFO_FORMATS = [
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
    'eoxserver.render.native.formats.',
]


def get_feature_info_format(mime_type):
    global FEATURE_INFO_FORMATS
    if FEATURE_INFO_FORMATS is None:
        specifiers = getattr(
            settings, 'EOXS_FEATURE_INFO_FORMATS',
            DEFAULT_EOXS_FEAUTURE_INFO_FORMATS
        )
        FEATURE_INFO_FORMATS = [
            import_string(specifier)()
            for specifier in specifiers
        ]
    for frmt in FEATURE_INFO_FORMATS:
        if frmt.mime_type == mime_type:
            return frmt


class FeatureInfoRenderer(object):
    def render(self, objects, mime_type):
        frmt = get_feature_info_format(mime_type)
        frmt.render(objects)
