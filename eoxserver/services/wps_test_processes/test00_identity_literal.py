#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
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

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, String,
    AllowedRange, UnitLinear,
    )

#from datetime import datetime
#from eoxserver.services.ows.wps.parameters import LiteralData, ComplexData
#from eoxserver.services.ows.wps.parameters import (AllowedAny, AllowedEnum,
#    AllowedRange, AllowedByReference)

class TestProcess00(Component):
    """ Test identity process (the ouptuts are copies of the inputs)
        demonstrating various features of the literal data inputs
        and outputs.
    """
    implements(ProcessInterface)

    identifier = "TC00:identity:literal"
    title = "Test Case 00: Literal data identity."
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("input00", str),
        ("input01", LiteralData('TC00:input01', String, optional=True,
            abstract="Simple string input.",
        )),
        ("input02", LiteralData('TC00:input02', str, optional=True,
            abstract="Enumerated string input. Optional with the default.",
            allowed_values=('low','medium','high'), default='medium',
        )),
        ("input03", LiteralData('TC00:input03', float, optional=True,
            title="Distance",
            abstract="Restricted float input. Optional with default. UOM conversion.",
            allowed_values=AllowedRange(0, 2, dtype=float), default=0,
            uoms=(('m', 1.0), ('mm', 1e-3), ('cm', 1e-2), ('dm', 1e-1),
                ('yd', 0.9144), ('ft', 0.3048), ('in', 0.0254),
                ('km', 1000.0), ('mi', 1609.344), ('NM', 1852.0),
            ),
        )),
        ("input04", LiteralData('TC00:input04', float, optional=True,
            title="Distance",
            abstract="Restricted float input. Optional with default.  Advanced UOM conversion.",
            allowed_values=AllowedRange(0, None, dtype=float), default=298.15,
            uoms=(('K', 1.0), UnitLinear('C', 1.0, 273.15),
                UnitLinear('F', 5.0/9.0, 459.67*5.0/9.0))
        )),
    ]

    outputs = [
        ("output00", str),
        ("output01", LiteralData('TC00:output01', String,
            abstract="Simple string output.", default="n/a"
        )),
        ("output02", LiteralData('TC00:output02', str, optional=True,
            abstract="Enumerated string output.",
            allowed_values=('low','medium','high'), default='medium',
        )),
        ("output03", LiteralData('TC00:output03', float,
            title="Distance",
            abstract="Restricted float input. UOM conversion.",
            allowed_values=AllowedRange(0, 1, dtype=float),
            uoms=(('m', 1.0), ('mm', 1e-3), ('cm', 1e-2), ('dm', 1e-1),
                ('yd', 0.9144), ('ft', 0.3048), ('in', 0.0254),
                ('km', 1000.0), ('mi', 1609.344), ('NM', 1852.0),
            ),
        )),
        ("output04", LiteralData('TC00:output04', float, optional=True,
            title="Distance",
            abstract="Restricted float input. Optional with default.  Advanced UOM conversion.",
            allowed_values=AllowedRange(0, None, dtype=float),
            uoms=(('K', 1.0), UnitLinear('C', 1.0, 273.15),
                UnitLinear('F', 5.0/9.0, 459.67*5.0/9.0))
        )),
    ]

    def execute(self, **inputs):
        outputs = {}
        outputs['output00'] = inputs['input00']
        outputs['output01'] = inputs.get('input01')
        outputs['output02'] = inputs['input02']
        outputs['output03'] = inputs['input03']
        outputs['output04'] = inputs['input04']
        return outputs

