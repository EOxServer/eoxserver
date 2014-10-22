
The OpenLayers.js was build using OpenLayers 2.13.1 with the following build
instructions and configurations:

  $ cd path/to/OpenLayers-2.13.1/build
  $ ./build.py -c closure_ws custom_eoxserver
  $ cp OpenLayers.js path/to/eoxserver/webclient/static/OpenLayers/

custom_eoxserver.cfg::

  [first]

  [last]

  [include]
  OpenLayers/Util.js
  OpenLayers/BaseTypes.js
  OpenLayers/BaseTypes/Class.js
  OpenLayers/BaseTypes/Bounds.js
  OpenLayers/Map.js
  OpenLayers/Projection.js
  OpenLayers/Layer/Vector.js
  OpenLayers/Layer/Boxes.js
  OpenLayers/Layer/WMS.js
  OpenLayers/Layer/WMTS.js
  OpenLayers/Layer/OSM.js
  OpenLayers/Format/OSM.js
  OpenLayers/Format/GML.js
  OpenLayers/Popup/FramedCloud.js
  OpenLayers/Marker/Box.js
  OpenLayers/Control/Navigation.js
  OpenLayers/Control/Zoom.js
  OpenLayers/Control/PanZoom.js
  OpenLayers/Control/WMSGetFeatureInfo.js
  OpenLayers/Control/Panel.js
  OpenLayers/Control/Permalink.js
  OpenLayers/Control/LayerSwitcher.js
  OpenLayers/Control/MousePosition.js
  OpenLayers/Control/KeyboardDefaults.js
  OpenLayers/Control/Attribution.js
  OpenLayers/Control/TouchNavigation.js
  OpenLayers/Renderer/SVG.js
  OpenLayers/Renderer/VML.js
  OpenLayers/Format/WMSGetFeatureInfo.js
  OpenLayers/Protocol/HTTP.js
  OpenLayers/Strategy/Fixed.js
  OpenLayers/Strategy/BBOX.js
  OpenLayers/StyleMap.js
  OpenLayers/Rule.js
  OpenLayers/Filter/Comparison.js
  OpenLayers/Filter/Logical.js

  [exclude]
