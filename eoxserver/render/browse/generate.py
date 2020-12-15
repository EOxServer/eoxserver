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

import numpy as np
from django.utils.six import string_types

from eoxserver.render.browse.util import warp_fields
from eoxserver.contrib import vrt, gdal, osr


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

    _ast.Mult,
    _ast.Div,
    _ast.Add,
    _ast.Sub,
    _ast.Num if hasattr(_ast, 'Num') else _ast.Constant,

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
                    width, height, bbox, crs, generator=None):
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
            parsed_expressions, fields_and_coverages,
            width, height, bbox, crs, generator
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
            width, height, bbox, crs, generator
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


def _generate_browse_complex(parsed_exprs, fields_and_coverages,
                             width, height, bbox, crs, generator):
    o_x = bbox[0]
    o_y = bbox[3]
    res_x = (bbox[2] - bbox[0]) / width
    res_y = -(bbox[3] - bbox[1]) / height
    tiff_driver = gdal.GetDriverByName('GTiff')

    field_names = set()
    for parsed_expression in parsed_exprs:
        field_names |= set(extract_fields(parsed_expression))

    fields_and_datasets = {}
    for field_name in field_names:
        coverages = fields_and_coverages[field_name]
        field_data = warp_fields(
            coverages, field_name, bbox, crs, width, height
        )
        fields_and_datasets[field_name] = field_data

    out_filename = generator.generate('tif')
    tiff_driver = gdal.GetDriverByName('GTiff')
    out_ds = tiff_driver.Create(
        out_filename,
        width, height, len(parsed_exprs),
        gdal.GDT_Float32,
        options=[
            "TILED=YES",
            "COMPRESS=PACKBITS"
        ]
    )
    out_ds.SetGeoTransform([o_x, res_x, 0, o_y, 0, res_y])
    out_ds.SetProjection(osr.SpatialReference(crs).wkt)

    for band_index, parsed_expr in enumerate(parsed_exprs, start=1):
        with np.errstate(divide='ignore', invalid='ignore'):
            out_data = _evaluate_expression(
                parsed_expr, fields_and_datasets, generator
            )

        if isinstance(out_data, (int, float)):
            out_data = np.full((height, width), out_data)

        out_band = out_ds.GetRasterBand(band_index)
        out_band.WriteArray(out_data)

    return BrowseCreationInfo(out_filename, None)


operator_map = {
    _ast.Add: operator.add,
    _ast.Sub: operator.sub,
    _ast.Div: operator.truediv,
    _ast.Mult: operator.mul,
}

function_map = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'arcsin': np.arcsin,
    'arccos': np.arccos,
    'arctan': np.arctan,
    'hypot': np.hypot,
    'arctan2': np.arctan2,
    'degrees': np.degrees,
    'radians': np.radians,
    'unwrap': np.unwrap,
    'deg2rad': np.deg2rad,
    'rad2deg': np.rad2deg,
    'sinh': np.sinh,
    'cosh': np.cosh,
    'tanh': np.tanh,
    'arcsinh': np.arcsinh,
    'arccosh': np.arccosh,
    'arctanh': np.arctanh,
    'exp': np.exp,
    'expm1': np.expm1,
    'exp2': np.exp2,
    'log': np.log,
    'log10': np.log10,
    'log2': np.log2,
    'log1p': np.log1p,
}


def _evaluate_expression(expr, fields_and_datasets, generator):
    if isinstance(expr, _ast.Name):
        return fields_and_datasets[expr.id]

    elif isinstance(expr, _ast.BinOp):
        left_data = _evaluate_expression(
            expr.left, fields_and_datasets, generator
        )

        right_data = _evaluate_expression(
            expr.right, fields_and_datasets, generator
        )

        op = operator_map[type(expr.op)]
        return op(left_data, right_data)

    elif isinstance(expr, _ast.Call):
        if not isinstance(expr.func, _ast.Name):
            raise BrowseGenerationError('Invalid function call')

        func = function_map.get(expr.func.id)
        if not func:
            raise BrowseGenerationError(
                'Invalid function %s, available functions are '
                % (expr.func.id, ', '.join(function_map.keys()))
            )

        if not len(expr.args) == 1:
            raise BrowseGenerationError(
                'Invalid number of arguments for function call'
            )

        args_data = [
            _evaluate_expression(
                arg, fields_and_datasets, generator
            ) for arg in expr.args
        ]
        res = func(*args_data)
        logger.info("%s, %s, %s" % (expr.func.id, np.min(res), np.max(res)))
        return res

    elif hasattr(_ast, 'Num') and isinstance(expr, _ast.Num):
        return expr.n

    elif hasattr(_ast, 'Constant') and isinstance(expr, _ast.Constant):
        return expr.value
