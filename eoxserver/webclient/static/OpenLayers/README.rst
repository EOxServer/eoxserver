
The OpenLayers.js was build using OpenLayers 2.10 with the following build
instructions and configuration::

  $ cd path/to/OpenLayers-2.10/build
  $ python build.py custom.cfg
  $ cp OpenLayers.js path/to/eoxserver/webclient/static/OpenLayers/

custom.cfg::
  
  [first]
  OpenLayers/SingleFile.js
  OpenLayers.js
  OpenLayers/Util.js
  OpenLayers/BaseTypes.js
  OpenLayers/BaseTypes/Class.js
  OpenLayers/BaseTypes/Bounds.js
  Rico/Corner.js

  [last]

  [include]
  OpenLayers/Map.js
  OpenLayers/Projection.js
  OpenLayers/Layer/Vector.js
  OpenLayers/Layer/Boxes.js
  OpenLayers/Layer/WMS.js
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

