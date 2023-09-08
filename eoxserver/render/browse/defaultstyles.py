from eoxserver.render.colors import COLOR_SCALES
from eoxserver.render.browse.objects import RasterStyle, RasterStyleColorEntry

DEFAULT_RASTER_STYLES = {}

for name, entries in COLOR_SCALES.items():
    DEFAULT_RASTER_STYLES[name] = RasterStyle(
        name,
        "ramp",
        [
            RasterStyleColorEntry(i, color)
            for i, color in entries
        ]
    )
