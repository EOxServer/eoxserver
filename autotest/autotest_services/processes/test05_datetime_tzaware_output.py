# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, DateTime, DateTimeTZAware,
)

class TestProcess05(Component):
    """ Test processes testing time-zone aware date-time input data-type
    with automatic time-zone conversion.
    """
    implements(ProcessInterface)

    identifier = "TC05:identity:literal:datetime"
    title = "Test Case 05: Literal output date-time time-zone test."
    profiles = ["test_profile"]

    TZ_DEFAULT = DateTime.TZOffset(+90)
    TZ_TARGET = DateTime.TZOffset(-120)
    #TIME_ZONE_UTC = DateTime.UTC

    inputs = [
        ('datetime', LiteralData(
            "TC05:datetime", DateTime, title="Date-time input.",
        )),
    ]

    outputs = [
        ('datetime_original', LiteralData(
            "TC05:datetime", DateTime,
            title="Date-time output without modification.",
        )),
        ('datetime_aware', LiteralData(
            "TC05:datetime_aware", DateTimeTZAware(TZ_DEFAULT),
            title="Date-time output with default time-zone.",
        )),
        ('datetime_converted', LiteralData(
            "TC05:datetime_converted", DateTimeTZAware(TZ_DEFAULT, TZ_TARGET),
            title="Date-time output with default time-zone.",
        )),
    ]

    def execute(self, **inputs):
        return {
            'datetime_original': inputs['datetime'],
            'datetime_aware': inputs['datetime'],
            'datetime_converted': inputs['datetime'],
        }
