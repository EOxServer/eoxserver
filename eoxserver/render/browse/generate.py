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

from uuid import uuid4

from eoxserver.contrib import vrt


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
    def __init__(self, template):
        """ Create a new :class:`FilenameGenerator` from a given template
            :param template: the template string used to construct the filenames
                             from. Uses the ``.format()`` style language. Keys
                             are ``index``, ``uuid`` and ``extension``.
        """
        self._template = template
        self._filenames = []

    def generate(self, extension=None):
        """ Generate and store a new filename using the specified template. An
            optional ``extension`` can be passed, when used in the template.
        """
        filename = self._template.format(
            index=len(self._filenames),
            uuid=uuid4().hex,
            extension=extension,
        )
        self._filenames.append(filename)
        return filename

    @property
    def filenames(self):
        """ Get a list of all generated filenames.
        """
        return self._filenames


def generate_browse(band_expressions, fields_and_coverages, generator=None):
    """ Produce a temporary VRT file describing how transformation of the
        coverages to browses.

        :param band_exressions: the band expressions for the various bands
        :param fields_and_coverages: a dictionary mapping the field names to all
                                     coverages with that field
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

    out_band_filenames = []

    # iterate over the input band expressions
    for band_expression in band_expressions:
        # TODO: allow more sophisticated expressions
        fields = band_expression.split(',')

        selected_filenames = []

        # iterate over all fields that the output band shall be comprised of
        for field in fields:
            coverages = fields_and_coverages[field]

            # iterate over all coverages for that field to select the single
            # field
            for coverage in coverages:
                location = coverage.get_location_for_field(field)
                orig_filename = location.path
                orig_band_index = coverage.get_band_index_for_field(field)

                # only make a VRT to select the band if band count for the
                # dataset > 1
                if location.field_count == 1:
                    selected_filename = orig_filename
                else:
                    selected_filename = generator.generate()
                    vrt.select_bands(
                        orig_filename, [orig_band_index], selected_filename
                    )

                selected_filenames.append(selected_filename)

        # if only a single file is required to generate the output band, return
        # it.
        if len(selected_filenames) == 1:
            out_band_filename = selected_filenames[0]

        # otherwise mosaic all the input bands to form a composite image
        else:
            out_band_filename = generator.generate()
            vrt.mosaic(selected_filenames, out_band_filename)

        out_band_filenames.append(out_band_filename)

    # make shortcut here, when we only have one band, just return it
    if len(out_band_filenames) == 1:
        return out_band_filenames[0], generator

    # return the stacked bands as a VRT
    else:
        stacked_filename = generator.generate()
        vrt.stack_bands(out_band_filenames, stacked_filename)
        return stacked_filename, generator
