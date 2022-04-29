# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Mussab Abdalla<mussab.abdalla@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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
# -----------------------------------------------------------------------------

from uuid import uuid4
import json
import numpy as np
from eoxserver.core import Component

import eoxserver.render.browse.functions as functions

from eoxserver.contrib import gdal
from eoxserver.contrib.vsi import open as vsi_open

from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, FormatJSON, CDObject,
    FormatBinaryRaw, FormatBinaryBase64, CDByteBuffer,
    BoundingBoxData
)
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError

from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open

from django.contrib.gis.geos import Polygon
import logging

logger = logging.getLogger(__name__)


class DemProcessingProcess(Component):
    """ DemProcessing defines a WPS process that provides multiple
        DEM processes """

    identifier = "DemProcessing"
    title = "Dem Processing (hillshade, aspect, relief...)for a coverage/s that intersects with the input bbox"
    description = ("provides processed results of all the coverages whithin a provided bounding box. "
                  " The processes returns hillshade, aspect/ratio, slope and contour.")
    metadata = {}
    profiles = ['EOxServer:DemProcessing']

    inputs = {
        "coverage": LiteralData(
            "coverage",
            title="coverage identifier."),
        "identifier": LiteralData(
            "identifier",
            optional=True,
            title="identifier of the process to be implemented."
        ),
        "bbox": BoundingBoxData(
            "bbox",
            title="bounding box that intersect with the products."
        ),
        "azimuth": LiteralData(
            "azimuth",
            optional=True,
            title="azimuth of the light source",
            abstract="Optional the azimuth of the light source, only for hillshade mode."
        ),
        "altitude": LiteralData(
            "altitude",
            optional=True,
            title="altitude  of the light source",
            abstract="Optional the altitude  of the light source, only for hillshade mode."
        ),
        "scale": LiteralData(
            "scale",
            optional=True,
            title="Ratio of vertical units to horizontal.",
            abstract="Optional can be used to set the ratio of vertical units to horizontal, used for hillshade ans slope"
        ),
        "z_factor": LiteralData(
            "z_factor",
            optional=True,
            title="Vertical exaggeration",
            abstract="Optional Vertical exaggeration used to pre-multiply the elevations, only for hillshade mode."
        ),
        "interval": LiteralData(
            "interval",
            optional=True,
            title="Elevation interval between contours.",
            abstract="Optional Elevation interval between contours., only for contour."
        ),
        "algorithm": LiteralData(
            "algorithm",
            optional=True,
            title="Dem Processing algorithm.",
            abstract="Optional Dem Processing algorithm to be performed,it varies depending on the process."
        ),
    }

    outputs = {
        "result": ComplexData(
            "result",
            title="output data",
            abstract="Binary/geojson complex data output.",
            formats=(
                FormatBinaryRaw('image/png'),
                FormatBinaryBase64('image/png'),
                FormatBinaryRaw('image/jpeg'),
                FormatBinaryBase64('image/jpeg'),
                FormatBinaryRaw('image/tiff'),
                FormatBinaryBase64('image/tiff'),
                FormatJSON()
            )
        ),
    }

    @staticmethod
    def execute(coverage, identifier, bbox, result, z_factor, interval, scale, azimuth, altitude, algorithm):
        """ The main execution function for the process.
        """

        np_bbox = np.array(bbox)
        flattened_bbox = np_bbox.flatten()
        values = flattened_bbox.tolist()

        data_format = "raster"
        # output format selection
        if result['mime_type'] == "image/png":
            extension = "png"
            driver = gdal.GetDriverByName("PNG")
        elif result['mime_type'] == "image/jpeg":
            extension = "jpg"
            driver = gdal.GetDriverByName("JPEG")
        elif result['mime_type'] == "image/tiff":
            extension = "tif"
            driver = gdal.GetDriverByName("GTiff")
        else:
            extension = "geojson"
            data_format = "vector"
            driver = gdal.GetDriverByName("GeoJSON")

        # get the dataset series matching the requested ID
        try:
            model = models.Coverage.objects.get(
                identifier=coverage)

        except models.Coverage.DoesNotExist:
            raise InvalidInputValueError(
                "coverage", "Invalid coverage name '%s'!" % coverage
            )
        try:

            data_items = model.arraydata_items.all()

        except model.arraydata_items.all().length > 1:
            raise InvalidInputValueError(
                "coverage", "coverage '%s' has more than one imagery, the profile process handles single images!" % coverage
            )
        data_item = data_items[0]

        original_ds = gdal_open(data_item, False)

        # check if the provided box is compatible with the coverage
        geoTransform = original_ds.GetGeoTransform()
        minx = geoTransform[0]
        maxy = geoTransform[3]
        maxx = minx + geoTransform[1] * original_ds.RasterXSize
        miny = maxy + geoTransform[5] * original_ds.RasterYSize
        coverage_bbox = Polygon.from_bbox((minx, miny, maxx, maxy))
        request_bbox = Polygon.from_bbox(values)

        if coverage_bbox.contains(request_bbox):
            values_bbox = coverage_bbox.intersection(request_bbox)
            if values_bbox.area > 0:
                values = list(values_bbox.extent)
            else:
                logger.error('The provided bbox is not inside or intersecting with the coverage')

        output_filename = '/vsimem/%s.%s' % (uuid4().hex, extension)
        tmp_ds = '/vsimem/%s.tif' % uuid4().hex
        ds = gdal.Warp(tmp_ds, original_ds, dstSRS=original_ds.GetProjection(), outputBounds=values, format='Gtiff')

        if identifier == 'hillshade':
            args = [ds, z_factor, scale, azimuth, altitude, algorithm]
        elif identifier == 'aspect':
            args = [ds, False, False, algorithm]
        elif identifier == 'slopeshade':
            args = [ds, scale, algorithm]
        elif identifier == 'contours':
            interval = int(interval) if interval is not None else 100
            args = [ds, 0, interval, -9999, data_format]

        func = functions.get_function(identifier)
        res_ds = func(*args)

        out_ds = driver.CreateCopy(output_filename, res_ds, 0)

        if extension == 'tif':
            out_ds.SetGeoTransform(ds.GetGeoTransform())
            out_ds.SetProjection(ds.GetProjection())
        del out_ds

        if extension == "geojson":

            with vsi_open(output_filename) as f:

                _output = CDObject(
                    json.load(f), format=FormatJSON(),
                    filename=("contours.json")
                )

        else:

            with vsi_open(output_filename, 'rb') as fid:
                _output = CDByteBuffer(
                    fid.read(), filename=output_filename,
                )
                if getattr(_output, 'mime_type', None) is None:
                    setattr(_output, 'mime_type', result['mime_type'])
        gdal.Unlink(output_filename)
        gdal.Unlink(tmp_ds)
        return _output
