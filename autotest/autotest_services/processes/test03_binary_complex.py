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

import uuid
import os.path
from numpy.random import RandomState
from osgeo import gdal
from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.exceptions import ExecuteError
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, CDFile, CDByteBuffer,
    FormatBinaryRaw, FormatBinaryBase64, AllowedRange,
)

class TestProcess03(Component):
    """ Test process generating binary complex data output. """
    implements(ProcessInterface)

    identifier = "TC03:image_generator:complex"
    title = "Test Case 03: Complex data binary output with format selection."
    description = (
        "Test process generating binary complex data output (an image)."
    )
    metadata = {"test-metadata": "http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("method", LiteralData(
            'TC03:method', str, optional=True,
            title="Complex data output passing method.",
            abstract=(
                "This option controls the method how the complex data output "
                "payload is passed from process code."
            ),
            allowed_values=('in-memory-buffer', 'file'), default='file',
        )),
        ("seed", LiteralData(
            'TC03:seed', int, optional=True, title="Random generator seed.",
            abstract=(
                "Optional random generator seed that can be used to obtain "
                "reproducible random-generated result."
            ),
            allowed_values=AllowedRange(0, None, dtype=int),
        )),
    ]

    outputs = [
        ("output", ComplexData(
            'TC03:output00', title="Test case #02: Complex output #00",
            abstract="Binary complex data output (random-generated image).",
            formats=(
                FormatBinaryRaw('image/png'),
                FormatBinaryBase64('image/png'),
                FormatBinaryRaw('image/jpeg'),
                FormatBinaryBase64('image/jpeg'),
                FormatBinaryRaw('image/tiff'),
                FormatBinaryBase64('image/tiff'),
            )
        )),
    ]

    # NOTE:
    #   The output complex data format has to be handled by the processes
    #   itself and the format selection has to be passed to the 'execute'
    #   subroutine.  The output complex data format selection is passed
    #   to the process as an additional input argument - a simple dictionary
    #   with the 'mime_type', 'encoding', 'schema', and 'as_reference' keywords.
    #   In case no format being selected by the user this format selection
    #   is set to the default format.  The name of the input argument holding
    #   the is controlled by the process output definition.

    @staticmethod
    def execute(method, seed, output):
        # size of the output image
        size_x, size_y = (768, 512)

        # output format selection
        if output['mime_type'] == "image/png":
            extension = ".png"
            driver = gdal.GetDriverByName("PNG")
            options = []
        elif output['mime_type'] == "image/jpeg":
            extension = ".jpg"
            driver = gdal.GetDriverByName("JPEG")
            options = []
        elif output['mime_type'] == "image/tiff":
            extension = ".tif"
            driver = gdal.GetDriverByName("GTiff")
            options = ["TILED=YES", "COMPRESS=DEFLATE", "PHOTOMETRIC=RGB"]
        else:
            ExecuteError("Unexpected output format received! %r" % output)

        # generate a random in-memory GDAL dataset
        mem_driver = gdal.GetDriverByName("MEM")
        mem_ds = mem_driver.Create("", size_x, size_y, 3, gdal.GDT_Byte)
        random_state = RandomState(seed)
        for i in xrange(3):
            mem_ds.GetRasterBand(i+1).WriteArray(
                (256.0 * random_state.rand(size_y, size_x)).astype('uint8')
            )

        # convert in-memory dataset to the desired output
        tmp_filename = os.path.join("/tmp", str(uuid.uuid4()) + extension)
        output_filename = "test03_binary_complex" + extension

        try:
            driver.CreateCopy(tmp_filename, mem_ds, 0, options)
            del mem_ds

            if method == 'file':
                # Return object as a temporary Complex Data File.
                # None that the object holds the format attributes!
                # The 'filename' parameter sets the raw output
                # 'Content-Disposition: filename=' HTTP header.
                return CDFile(tmp_filename, filename=output_filename, **output)

            elif method == 'in-memory-buffer':
                # Return object as an in-memory Complex Data Buffer.
                # None that the object holds the format attributes!
                # The 'filename' parameter sets the raw output
                # 'Content-Disposition: filename=' HTTP header.
                with file(tmp_filename) as fid:
                    _output = CDByteBuffer(
                        fid.read(), filename=output_filename, **output
                    )
                os.remove(tmp_filename)
                return _output
        except:
            # make sure no temporary file is left in case of an exception
            if os.path.isfile(tmp_filename):
                os.remove(tmp_filename)
            raise
