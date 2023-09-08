<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" xmlns:sld="http://www.opengis.net/sld" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>S2B_30UUG_20221226_0_L2A_scl</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="values">
              <sld:ColorMapEntry color="#000000" quantity="0" label="NO_DATA"/>
              <sld:ColorMapEntry color="#ff0000" quantity="1" label="SATURATED_OR_DEFECTIVE"/>
              <sld:ColorMapEntry color="#2e2e2e" quantity="2" label="DARK_AREA_PIXELS"/>
              <sld:ColorMapEntry color="#541800" quantity="3" label="CLOUD_SHADOWS"/>
              <sld:ColorMapEntry color="#46e800" quantity="4" label="VEGETATION"/>
              <sld:ColorMapEntry color="#ffff00" quantity="5" label="NOT_VEGETATED"/>
              <sld:ColorMapEntry color="#0000ff" quantity="6" label="WATER"/>
              <sld:ColorMapEntry color="#525252" quantity="7" label="UNCLASSIFIED"/>
              <sld:ColorMapEntry color="#787878" quantity="8" label="CLOUD_MEDIUM_PROBABILITY"/>
              <sld:ColorMapEntry color="#b5b5b5" quantity="9" label="CLOUD_HIGH_PROBABILITY"/>
              <sld:ColorMapEntry color="#00b6bf" quantity="10" label="THIN_CIRRUS"/>
              <sld:ColorMapEntry color="#da00f2" quantity="11" label="SNOW"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>
