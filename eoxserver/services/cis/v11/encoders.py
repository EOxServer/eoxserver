# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

from lxml.builder import ElementMaker

from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap

# namespace declarations
ns_cis = NameSpace("http://www.opengis.net/gml/1.1", "cis")
ns_swe = NameSpace("http://www.opengis.net/swe/2.0", "swe")

nsmap = NameSpaceMap(ns_cis, ns_swe)

# Element factories
CIS = ElementMaker(namespace=ns_cis.uri, nsmap=nsmap)
SWE = ElementMaker(namespace=ns_swe.uri, nsmap=nsmap)


class CIS11XMLEncoder(XMLEncoder):
    def encode_axis_extent(self, axis, origin, size):
        if axis.regular:
            return CIS('axisExtent',
                axisLabel=axis.name,
                uomLabel=axis.uom,
                lowerBound=str(origin),
                upperBound=str(origin + (axis.offset * size)),
            )
        else:
            return CIS('axisExtent',
                axisLabel=axis.name,
                uomLabel=axis.uom,
                lowerBound=str(axis.positions[0]),
                upperBound=str(axis.positions[-1]),
            )

    def encode_envelope(self, grid, origins, sizes):
        return CIS('envelope', *[
                self.encode_axis_extent(axis, origin, size)
                for axis, origin, size in izip_longest(grid, origins, sizes)
            ],
            axisLabels=' '.join(axis.name for axis in grid),
            srsName=grid.coordinate_reference_system,
            srsDimension=str(len(grid))
        )

    def encode_regular_axis(self, axis, origin, size):
        """
        """
        return CIS('RegularAxis',
            axisLabel=axis.name,
            uomLabel=axis.uom,
            lowerBound=str(origin),
            upperBound=str(origin + (axis.offset * size)),
            resolution=str(axis.offset),
        )

    def encode_irregular_axis(self, axis):
        """
        """
        return CIS('IrregularAxis', *[
                CIS('C', str(position))
                for position in axis.positions
            ],
            axisLabel=axis.name,
            uomLabel=axis.uom,
        )

    def encode_grid(self, grid, origins, sizes):
        return CIS('generalGrid', *([
                self.encode_regular_axis(axis, origin, size)
                if axis.regular else
                self.encode_irregular_axis(axis)
                for axis, origin, size in izip_longest(grid, origins, sizes)
            ] + [
                CIS('gridLimits', *[
                    CIS(
                        'indexAxis',
                        axisLabel=label,
                        lowerBound="0",
                        upperBound=str(size),
                    ) for label, size in zip('ijkl', sizes)
                ])
            ]),
            srsName=grid.coordinate_reference_system,
            axisLabels=' '.join(axis.name for axis in grid)
        )

    def encode_domain_set(self, coverage):
        return CIS('domainSet',
            self.encode_grid(coverage.grid, coverage.origin, coverage.size)
        )

    def encode_nil_values(self, nil_values):
        return SWE("nilValues",
            SWE("NilValues",
                *[
                    SWE("nilValue", nil_value[0], reason=nil_value[1])
                    for nil_value in nil_values
                ]
            )
        )

    def encode_field(self, field):
        return SWE("field",
            SWE("Quantity",
                SWE("description", field.description),
                self.encode_nil_values(field.nil_values),
                SWE("uom", code=field.unit_of_measure),
                SWE("constraint",
                    SWE("AllowedValues",
                        *[
                            SWE("interval", "%g %g" % value_range)
                            for value_range in field.allowed_values
                        ] + [
                            SWE("significantFigures", str(
                                field.significant_figures
                            ))
                        ] if field.significant_figures else []
                    )
                ),
                # http://www.opengis.net/def/dataType/OGC/0/
                definition=field.definition
            ),
            name=field.identifier
        )

    def encode_range_type(self, range_type):
        return CIS('rangeType',
            SWE('DataRecord', *[
                    self.encode_field(field) for field in range_type
                ]
            )
        )

    def encode_general_grid_coverage(self, coverage):
        pass
