{% extends "gis/admin/openlayers.js" %}

{% block extra_layers %}
    overlay_layer = new OpenLayers.Layer.WMS( "EOX Maps", "//tiles.maps.eox.at/wms/", {layers:"overlay",transparent:"true",format:'image/png'} );
    {{ module }}.map.addLayer(overlay_layer);
{% endblock extra_layers %}
