
from datetime import datetime
from urllib import unquote

from eoxserver.core import Component, implements, env
from eoxserver.contrib.mapserver import (
    create_request, Map, Layer, outputFormatObj, 
    gdalconst_to_imagemode, gdalconst_to_imagemode_string
)
from eoxserver.backends.cache import CacheContext
from eoxserver.backends.access import connect
from eoxserver.services.component import MapServerComponent
from eoxserver.services.interfaces import CoverageRendererInterface
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss


class CoverageRenderer(Component):
    implements(CoverageRendererInterface)
    abstract = True


class RectifiedCoverageMapServerRenderer(CoverageRenderer):
    handles = (models.RectifiedDataset,)

    def render(self, coverage, **kwargs):
        with CacheContext() as c:
            data_items = coverage.data_items.filter(semantic__startswith="bands")
            locations = map(lambda data_item: connect(data_item, c), data_items)

            #print locations
            #data = connect(coverage, c)
            return self._render(coverage, data_items, locations, kwargs)


    def _render(self, coverage, data_items, locations, kwargs):
        # create and configure map object
        map_ = Map()
        map_.setMetaData("ows_enable_request", "*")

        # configure outputformat
        native_format = get_native_format(coverage, data_items)
        format = kwargs.get("format") or native_format

        if format is None:
            raise Exception("format could not be determined")

        range_type = coverage.range_type
        bands = list(range_type)

        imagemode = gdalconst_to_imagemode(range_type.data_type)
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        basename = "%s_%s" % (coverage.identifier, time_stamp) 
        of = create_outputformat(format, imagemode, basename)
        map_.appendOutputFormat(of)
        map_.setOutputFormat(of)

        # create and configure layer
        layer = Layer(coverage.identifier)

        data_statements = map(
            lambda ds: (ds[0], ds[1].semantic),
            zip(locations, data_items)
        )

        ms_component = MapServerComponent(env)
        layer_connector = ms_component.get_connector(data_statements)
        
        if not layer_connector:
            raise Exception("Could not find applicable layer connector.")

        layer_connector.connect(layer, data_statements)
        
        layer.setProjection(coverage.spatial_reference.proj)

        extent = coverage.extent
        size = coverage.size
        resolution = ((extent[2] - extent[0]) / float(size[0]),
                      (extent[1] - extent[3]) / float(size[1]))

        layer.setExtent(*extent)

        layer.setMetaData({
            "title": coverage.identifier,
            "enable_request": "*"
        }, namespace="ows")

        layer.setMetaData({
            "label": coverage.identifier,
            "extent": "%.10g %.10g %.10g %.10g" % extent,
            "resolution": "%.10g %.10g" % resolution,
            "size": "%d %d" % size,
            "bandcount": str(len(bands)),
            "band_names": " ".join([band.name for band in bands]),
            "interval": "%f %f" % range_type.allowed_values,
            "significant_figures": "%d" % range_type.significant_figures,
            "rangeset_name": range_type.name,
            "rangeset_label": range_type.name,
            "rangeset_axes": ",".join(band.name for band in bands),
            "native_format": native_format,
            "nativeformat": native_format,
            #"formats": getMSWCSFormatMD(),
            "imagemode": gdalconst_to_imagemode_string(range_type.data_type),
        }, namespace="wcs")

        supported_crss = " ".join(
            crss.getSupportedCRS_WCS(format_function=crss.asShortCode)
        ) 
        layer.setMetaData("ows_srs", supported_crss) 
        layer.setMetaData("wcs_srs", supported_crss) 

        for band in bands:
            layer.setMetaData({
                "band_description": band.description,
                "band_definition": band.definition,
                "band_uom": band.uom
            }, namespace=band.name)

            # For MS WCS 1.x interface
            layer.setMetaData({
                "label": band.name,
                "interval": "%d %d" % band.allowed_values
            }, namespace="wcs_%s" % band.name)

        map_.insertLayer(layer)

        if "mask" in kwargs:
            # TODO: implement
            pass

        # create request object and dispatch it agains the map
        request = self._create_request_v20(coverage.identifier, **kwargs)
        response = map_.dispatch(request)
        return response.content, response.content_type


    def _create_request_v20(self, coverageid, subsets=[], sizes=[], 
                            resolutions=[], rangesubset=None, format=None, 
                            outputcrs=None, mediatype=None, interpolation=None,
                            **kwargs):
        params = [
            ("service", "wcs"),
            ("version", "2.0.0"),
            ("request", "getcoverage"),
            ("coverageid", coverageid)
        ]

        for s in subsets:
            # prohibit subsets other that trims and xy
            if s.crs:
                value = "%s,%s(%s,%s)" % (
                    s.axis, s.crs, s.low or "*", s.high or "*"
                )
            else: 
                value = "%s(%s,%s)" % (
                    s.axis, s.low or "*", s.high or "*"
                )
            params.append(("subset", value))

        for size in sizes:
            params.append(("size", "%s(%i)" % (size.axis, size.value)))

        for res in resolutions:
            params.append(("resolution", "%s(%f)" % (res.axis, res.value)))

        if rangesubset: params.append(("rangesubset", ",".join(rangesubset)))
        if format: params.append(("format", format))
        if outputcrs: params.append(("outputcrs", outputcrs))
        if mediatype: params.append(("mediatype", mediatype))
        if interpolation: params.append(("interpolation", interpolation))

        return create_request(params)


class ReferenceableDatasetRenderer(CoverageRenderer):
    handles = (models.ReferenceableDataset,)

    def render(self, coverage, parameters):
        pass


def get_native_format(coverage, data_items):
    if len(data_items) == 1:
        return data_items[0].format

    return None


def create_outputformat(format, imagemode, basename):
    parts = unquote(format).split(";")
    mime_type = parts[0]
    options = map(
        lambda kv: map(lambda i: i.strip(), kv.split("=")), parts[1:]
    )

    registry = getFormatRegistry()
    reg_format = registry.getFormatByMIME(mime_type)

    if not reg_format:
        raise "Unsupported output format '%s'." % format

    outputformat = outputFormatObj(reg_format.driver, "custom")
    outputformat.mimetype = reg_format.mimeType
    outputformat.extension = reg_format.defaultExt
    outputformat.imagemode = imagemode

    for key, value in options:
        print key, value
        outputformat.setOption(key, value)

    filename = basename + reg_format.defaultExt
    outputformat.setOption("FILENAME", str(filename))

    return outputformat


