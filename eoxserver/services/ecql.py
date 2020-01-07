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

from pycql import parse, get_repr
from pycql.integrations.django import to_filter


from .filters import get_field_mapping_for_model


def apply(qs, cql, exclude=False):
    """ Applies a given CQL filter on a passed queryset. The field mapping is
        deducted from the model of the passed queryset.
        A new queryset is returned with all filters applied.
        :param qs: the base query to apply the filters on. The :attr:`model`
                   is used to determine the metadata field mappings.
        :param cql: a string containing the CQL expressions to be parsed and
                    applied
        :param exclude: whether the filters shall be applied using
                        :meth:`exclude`. Default is ``False``.
        :returns: A new queryset object representing the filtered queryset.
        :rtype: :class:`django.db.models.QuerySet`
    """
    mapping, mapping_choices = get_field_mapping_for_model(qs.model)
    ast = parse(cql)

    filters = to_filter(ast, mapping, mapping_choices)
    if exclude:
        return qs.exclude(filters)
    else:
        return qs.filter(filters)
