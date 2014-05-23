#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

from datetime import datetime

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import LiteralData, ComplexData


class TestProcess(Component):
    """ Simple test process. """ 

    # Comment following line to make the test process active.
    abstract = True

    implements(ProcessInterface)

    identifier = "id"
    title = "title"
    description = "description"
    metadata = ["a", "b"]
    profiles = ["p", "q"]

    inputs = {
        "X": int,
        "Y": datetime,
        "Z": LiteralData(
            "MyZIdenifier", description="myAbstract", 
            type=float, default=1., allowed_values=[1., 2., 3.]
        ),
        "V": LiteralData(
            "MyVIdenifier", description="VVV", 
            type=float, default=1., values_reference="http://foo.bar/value",
            uoms=("metres", "feet")
        ),
        "W": LiteralData(
            "MyWIdenifier", description="WWW", 
            type=datetime, optional = True 
        ),
    }

    outputs = {
        "X": int, 
        "Y": float,
        "Z": LiteralData(
            "MyZIdenifier", description="myAbstract", type=float,
            uoms=("metres", "feet")
        )
    }

