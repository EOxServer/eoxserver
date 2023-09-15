from eoxserver.render.colors import COLOR_SCALES, BASE_COLORS
from eoxserver.render.browse.objects import (
    GeometryStyle,
    RasterStyle,
    RasterStyleColorEntry,
)

DEFAULT_RASTER_STYLES = {}
DEFAULT_GEOMETRY_STYLES = {}

for name, entries in COLOR_SCALES.items():
    DEFAULT_RASTER_STYLES[name] = RasterStyle(
        name,
        "ramp",
        name,
        name,
        [
            RasterStyleColorEntry(i, color)
            for i, color in entries
        ]
    )


for name in BASE_COLORS.keys():
    DEFAULT_GEOMETRY_STYLES[name] = GeometryStyle(name, name, name)
