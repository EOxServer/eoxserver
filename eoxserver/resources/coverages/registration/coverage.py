# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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


DEFAULT_EOXS_COVERAGE_REGISTRATORS = [
    'eoxserver.resources.coverages.registration.registrators.gdal.GDALRegistrator',
    'eoxserver.resources.coverages.registration.registrators.hdf.HDFRegistrator'
]

COVERAGE_REGISTRATORS = None


def _setup_factories():
    global COVERAGE_REGISTRATORS
    specifiers = getattr(
        settings, 'EOXS_COVERAGE_REGISTRATORS',
        DEFAULT_EOXS_COVERAGE_REGISTRATORS
    )
    COVERAGE_REGISTRATORS = [
        import_string(specifier)()
        for specifier in specifiers
    ]


def get_coverage_registrator(scheme=None):
    """ Returns the configured coverage registrator
    """
    if COVERAGE_REGISTRATORS is None:
        _setup_factories()

    if not COVERAGE_REGISTRATORS:
        raise Exception('No coverage registrator configured')

    if scheme is None:
        return COVERAGE_REGISTRATORS[0]

    for registrator in COVERAGE_REGISTRATORS:
        if registrator.scheme == scheme:
            return registrator

    raise Exception(
        "No registrator for scheme '%s' configured. "
        "Available schemes are: %s" % (
            scheme, ", ".join([
                registrator.scheme
                for registrator in COVERAGE_REGISTRATORS
            ])
        )
    )
