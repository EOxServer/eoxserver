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
import numpy as np
from osgeo import gdal
from numpy.random import random
from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.exceptions import ExecuteException
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, CDFile, CDByteBuffer,
    FormatBinaryRaw, FormatBinaryBase64,
)

class TestProcess03(Component):
    """ Test process generating complext data binary output (image) with
        fomat selection.
    implements(ProcessInterface)
    """
    implements(ProcessInterface)

    identifier = "TC03:image_generator:complex"
    title = "Test Case 03: Complex data binary data with format selection."
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("method", LiteralData('TC03:method', str, optional=True,
            title="Complex data passing method.",
            abstract="Select method how the complex data output is passed.",
            allowed_values=('in-memory-buffer', 'file'), default='file',
        )),
    ]

    outputs = [
        ("output00",
            ComplexData('TC03:output00',
                title="Test case #02: Complex output #00",
                abstract="Copy of the input00.",
                formats=(
                    FormatBinaryRaw('image/png'),
                    FormatBinaryBase64('image/png'),
                    FormatBinaryRaw('image/jpeg'),
                    FormatBinaryBase64('image/jpeg'),
                    FormatBinaryRaw('image/tiff'),
                    FormatBinaryBase64('image/tiff'),
                )
            )
        ),
    ]

    # NOTE: For complex outputs the format selection must be handled
    #       by the actual process. Therefore there are additional inputs
    #       having the identifiers of the outputs containing the actual
    #       format selection. In case of no format selected by the user
    #       the format selection argument contains the default format.
    @staticmethod
    def execute(method, output00):
        base_fname = os.path.join("/tmp", str(uuid.uuid4()))
        size = (768, 512)

        mem_driver = gdal.GetDriverByName("MEM")
        mem_ds = mem_driver.Create("", size[0], size[1], 3, gdal.GDT_Byte)
        for i in xrange(3):
            data = np.array(random((size[1], size[0]))*256, 'uint8')
            mem_ds.GetRasterBand(i+1).WriteArray(data)

        if output00['mime_type'] == "image/png":
            fname = base_fname+".png"
            driver = gdal.GetDriverByName("PNG")
            options = []
        elif output00['mime_type'] == "image/jpeg":
            fname = base_fname+".jpg"
            driver = gdal.GetDriverByName("JPEG")
            options = []
        elif output00['mime_type'] == "image/tiff":
            fname = base_fname+".tif"
            driver = gdal.GetDriverByName("GTiff")
            options = ["TILED=YES", "COMPRESS=DEFLATE", "PHOTOMETRIC=RGB"]
        else:
            ExecuteException("Invalid format! %r"%output00)

        try:
            driver.CreateCopy(fname, mem_ds, 0, options)
            del mem_ds

            if method == 'file':
                # Return object as a temporary Complex Data File.
                # None that the object holds the format attributes!
                return CDFile(fname, **output00)

            elif method == 'in-memory-buffer':
                # Return object as an im-memore Complex Data Buffer.
                # None that the object holds the format attributes!
                with file(fname) as fid:
                    output = CDByteBuffer(fid.read(), **output00)
                os.remove(fname)
                return output
        except:
            # make sure no temporary file is left
            if os.path.isfile(fname):
                os.remove(fname)
            raise
