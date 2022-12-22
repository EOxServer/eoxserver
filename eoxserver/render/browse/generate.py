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

from uuid import uuid4
import ast
import _ast
import operator
import logging
import concurrent.futures
from functools import wraps

import numpy as np
from django.utils.six import string_types

from eoxserver.render.browse.util import warp_fields
from eoxserver.render.browse.functions import get_function, get_buffer
from eoxserver.contrib import vrt, gdal, osr, gdal_array


logger = logging.getLogger(__name__)


class BrowseGenerationError(Exception):
    pass


class BrowseGenerator(object):
    def __init__(self, footprint_alpha=True, ):
        pass

    def generate(self, product, browse_type, style, out_filename):
        if not product.product_type or \
                not product.product_type == browse_type.product_type:
            raise BrowseGenerationError("Product and browse type don't match")


class FilenameGenerator(object):
    """ Utility class to generate filenames after a certain pattern (template)
        and to keep a list for later cleanup.
    """
    def __init__(self, template, default_extension=None):
        """ Create a new :class:`FilenameGenerator` from a given template
            :param template: the template string used to construct the
                             filenames from. Uses the ``.format()`` style
                             language. Keys are ``index``, ``uuid`` and
                             ``extension``.
        """
        self._template = template
        self._filenames = []
        self._default_extension = default_extension

    def generate(self, extension=None):
        """ Generate and store a new filename using the specified template. An
            optional ``extension`` can be passed, when used in the template.
        """
        filename = self._template.format(
            index=len(self._filenames),
            uuid=uuid4().hex,
            extension=extension or self._default_extension,
        )
        self._filenames.append(filename)
        return filename

    @property
    def filenames(self):
        """ Get a list of all generated filenames.
        """
        return self._filenames


class BandExpressionError(ValueError):
    pass


ALLOWED_NODE_TYPES = (
    _ast.Module,
    _ast.Expr,
    _ast.Load,
    _ast.Name,
    _ast.Call,

    _ast.UnaryOp,
    _ast.BinOp,

    _ast.Subscript,
    _ast.Slice,
    _ast.Load,
    _ast.Index if hasattr(_ast, 'Index') else _ast.Subscript,

    _ast.Mult,
    _ast.Div,
    _ast.Add,
    _ast.Sub,
    _ast.Num if hasattr(_ast, 'Num') else _ast.Constant,
    _ast.List,

    _ast.BitAnd,
    _ast.BitOr,
    _ast.BitXor,

    _ast.USub,
)


def parse_expression(band_expression):
    """ Parse and validate the passed band expression
    """
    parsed = ast.parse(band_expression)
    for node in ast.walk(parsed):
        if not isinstance(node, ALLOWED_NODE_TYPES):
            raise BandExpressionError(
                'Invalid expression: %s' % type(node).__name__
            )
    return parsed.body[0].value


def parent_walk(node, depth=0):
    if depth == 0:
        yield None, node

    for child in ast.iter_child_nodes(node):
        yield node, child
        for child, ancestor in parent_walk(child, depth+1):
            yield child, ancestor


def extract_fields(band_expression):
    """ Extract the fields required to generate the output band.
        :param band_expression: the band expression to extract the fields of
        :type band_expression: str
        :return: a list of field names
        :rtype: list
    """
    if isinstance(band_expression, string_types):
        root_expr = parse_expression(band_expression)
    else:
        root_expr = band_expression
    return [
        node.id
        for parent, node in parent_walk(root_expr)
        if isinstance(node, _ast.Name) and not (
            isinstance(parent, _ast.Call) and parent.func == node
        )
    ]


class BrowseCreationInfo(object):
    def __init__(self, filename, env, bands=None):
        self.filename = filename
        self.env = env
        self.bands = bands


# make shortcut: if all relevant bands are in one dataset, we
# will only return that and give the band numbers
def single_file_and_indices(band_expressions, fields_and_coverages):
    band_indices = []
    filenames = set()
    env = None
    for band_expression in band_expressions:
        fields = extract_fields(band_expression)
        if len(fields) != 1:
            return None, None, None

        field = fields[0]

        coverages = fields_and_coverages[field]
        # break early if we are dealing with more than one coverage
        if len(coverages) != 1:
            return None, None, None

        coverage = coverages[0]
        location = coverage.get_location_for_field(field)

        filenames.add(location.path)
        band_indices.append(
            coverage.get_band_index_for_field(field)
        )
        env = location.env

    if len(filenames) == 1:
        return filenames.pop(), env, band_indices

    return None, None, None


def generate_browse(band_expressions, fields_and_coverages,
                    width, height, bbox, crs, generator=None, variables=None):
    """ Produce a temporary VRT file describing how transformation of the
        coverages to browses.

        :param band_exressions: the band expressions for the various bands
        :param fields_and_coverages: a dictionary mapping the field names to
                                     all coverages with that field
        :param: band_expressiosn: list of strings
        :type fields_and_coverages: dict
        :return: A tuple of the filename of the output file and the generator
                 which was used to generate the filenames.
                 In most cases this is the filename refers to a generated VRT
                 file in very simple cases the file might actually refer to an
                 original file.
        :rtype: tuple
    """
    generator = generator or FilenameGenerator('/vsimem/{uuid}.vrt')

    # out_band_filenames = []

    parsed_expressions = [
        parse_expression(band_expression)
        for band_expression in band_expressions
    ]

    is_simple = all(isinstance(expr, _ast.Name) for expr in parsed_expressions)

    if not is_simple:
        return _generate_browse_complex(
            parsed_expressions,
            fields_and_coverages,
            width,
            height,
            bbox,
            crs,
            generator,
            variables if variables is not None else {}
        ), generator, True

    single_filename, env, bands = single_file_and_indices(
        band_expressions, fields_and_coverages
    )

    # for single files, we make a shortcut and just return it and the used
    # bands
    if single_filename:
        return (
            BrowseCreationInfo(single_filename, env, bands),
            generator, False
        )

    else:
        return _generate_browse_complex(
            parsed_expressions, fields_and_coverages,
            width, height, bbox, crs, generator,
            variables={}
        ), generator, True

    # iterate over the input band expressions
    # for band_expression in band_expressions:
    #     fields = extract_fields(band_expression)

    #     selected_filenames = []

    #     # iterate over all fields that the output band shall be comprised of
    #     for field in fields:
    #         coverages = fields_and_coverages[field]

    #         # iterate over all coverages for that field to select the single
    #         # field
    #         for coverage in coverages:
    #             location = coverage.get_location_for_field(field)
    #             orig_filename = location.path
    #             orig_band_index = coverage.get_band_index_for_field(field)

    #             # only make a VRT to select the band if band count for the
    #             # dataset > 1
    #             if location.field_count == 1:
    #                 selected_filename = orig_filename
    #             else:
    #                 selected_filename = generator.generate()
    #                 vrt.select_bands(
    #                     orig_filename, location.env,
    #                     [orig_band_index], selected_filename
    #                 )

    #             selected_filenames.append(selected_filename)

    #     # if only a single file is required to generate the output band, return
    #     # it.
    #     if len(selected_filenames) == 1:
    #         out_band_filename = selected_filenames[0]

    #     # otherwise mosaic all the input bands to form a composite image
    #     else:
    #         out_band_filename = generator.generate()
    #         vrt.mosaic(selected_filenames, out_band_filename)

    #     out_band_filenames.append(out_band_filename)

    # # make shortcut here, when we only have one band, just return it
    # if len(out_band_filenames) == 1:
    #     return (
    #         BrowseCreationInfo(out_band_filenames[0], None), generator, False
    #     )

    # # return the stacked bands as a VRT
    # else:
    #     stacked_filename = generator.generate()
    #     vrt.stack_bands(out_band_filenames, env or location.env, stacked_filename)
    #     return (
    #         BrowseCreationInfo(stacked_filename, None), generator, False
    #     )


def thread_warp(coverages, field_name, bbox, crs, width, height):
    return field_name, warp_fields(
        coverages, field_name, bbox, crs, width, height
    )


def _generate_browse_complex(parsed_exprs, fields_and_coverages,
                             width, height, bbox, crs, generator, variables):

    # TODO: get the pixel buffer and adjust accordingly
    # buffer = get_buffer()
    o_x = bbox[0]
    o_y = bbox[3]
    res_x = (bbox[2] - bbox[0]) / width
    res_y = -(bbox[3] - bbox[1]) / height
    tiff_driver = gdal.GetDriverByName('GTiff')

    field_names = set()
    for parsed_expression in parsed_exprs:
        field_names |= set(extract_fields(parsed_expression))

    fields_and_datasets = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for field_name in field_names:
            coverages = fields_and_coverages[field_name]
            futures.append(
                executor.submit(
                    thread_warp,
                    coverages, field_name, bbox, crs, width, height
                )
            )
            # field_data = warp_fields(
            #     coverages, field_name, bbox, crs, width, height
            # )
            # fields_and_datasets[field_name] = field_data
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            fields_and_datasets[res[0]] = res[1]

    cache = {}
    out_datasets = []
    for band_index, parsed_expr in enumerate(parsed_exprs, start=1):
        with np.errstate(divide='ignore', invalid='ignore'):
            out_data = _evaluate_expression(
                parsed_expr, fields_and_datasets, variables, cache
            )

        if isinstance(out_data, (int, float)):
            out_data = gdal_array.OpenNumPyArray(
                np.full((height, width), out_data), False
            )
        out_datasets.append(out_data)

    out_filename = generator.generate('tif')
    tiff_driver = gdal.GetDriverByName('GTiff')
    out_ds = tiff_driver.Create(
        out_filename,
        width, height, len(parsed_exprs),
        out_datasets[0].GetRasterBand(1).DataType,
        options=[
            "TILED=YES",
            "COMPRESS=PACKBITS"
        ]
    )
    out_ds.SetGeoTransform([o_x, res_x, 0, o_y, 0, res_y])
    out_ds.SetProjection(osr.SpatialReference(crs).wkt)

    for band_index, out_data in enumerate(out_datasets, start=1):
        band = out_data.GetRasterBand(1)
        out_band = out_ds.GetRasterBand(band_index)
        out_band.WriteArray(band.ReadAsArray())

    return BrowseCreationInfo(out_filename, None)


def wrap_operator(function):
    @wraps(function)
    def inner(lhs, rhs):
        if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
            return function(lhs, rhs)

        gt = None
        if isinstance(lhs, gdal.Dataset):
            gt = lhs.GetGeoTransform()
            band = lhs.GetRasterBand(1)
            lhs = band.ReadAsArray()

        if isinstance(rhs, gdal.Dataset):
            gt = gt or rhs.GetGeoTransform()
            band = rhs.GetRasterBand(1)
            rhs = band.ReadAsArray()

        data = function(lhs, rhs)
        out_ds = gdal_array.OpenNumPyArray(data, False)
        out_ds.SetGeoTransform(gt)
        # TODO: copy metadata
        return out_ds

    return inner


operator_map = {
    _ast.Add: wrap_operator(operator.add),
    _ast.Sub: wrap_operator(operator.sub),
    _ast.Div: wrap_operator(operator.truediv),
    _ast.Mult: wrap_operator(operator.mul),
}


def _evaluate_expression(expr, fields_and_datasets, variables, cache):
    key = ast.dump(expr)
    if key in cache:
        return cache[key]

    if isinstance(expr, _ast.Name):
        result = fields_and_datasets[expr.id]

    elif isinstance(expr, _ast.BinOp):
        left_data = _evaluate_expression(
            expr.left, fields_and_datasets, variables, cache
        )

        right_data = _evaluate_expression(
            expr.right, fields_and_datasets, variables, cache
        )

        op = operator_map[type(expr.op)]
        result = op(left_data, right_data)

    elif isinstance(expr, _ast.Call):
        if not isinstance(expr.func, _ast.Name):
            raise BrowseGenerationError('Invalid function call')

        args_data = [
            _evaluate_expression(
                arg, fields_and_datasets, variables, cache
            ) for arg in expr.args
        ]
        if expr.func.id == 'var':
            result = variables.get(*args_data)
        else:
            func = get_function(expr.func.id)
            res = func(*args_data)
            result = res

    elif isinstance(expr, _ast.Subscript):
        value = _evaluate_expression(
            expr.value, fields_and_datasets, variables, cache
        )
        # assume that we will only use a single index
        if isinstance(expr.slice.value, int):
            slice_ = expr.slice.value  # python 3.10
        else:
            slice_ = expr.slice.value.value  # python 3.8

        # Get a copy of the selected band
        data = value.GetRasterBand(slice_ + 1).ReadAsArray()
        result = gdal_array.OpenNumPyArray(data, True)
        # restore nodata on output
        nodata_value = value.GetRasterBand(slice_ + 1).GetNoDataValue()
        if nodata_value is not None:
            result.GetRasterBand(1).SetNoDataValue(nodata_value)

    elif hasattr(_ast, 'Num') and isinstance(expr, _ast.Num):
        result = expr.n

    elif hasattr(_ast, 'Constant') and isinstance(expr, _ast.Constant):
        result = expr.value

    elif hasattr(_ast, 'List') and isinstance(expr, _ast.List):
        result = [
            _evaluate_expression(
                item, fields_and_datasets, variables, cache,
            ) for item in expr.elts
        ]
    else:
        raise BandExpressionError('Invalid expression node %s' % expr)

    cache[key] = result
    return result
