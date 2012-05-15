
namespace("WebClient").Templates = (function() {

    return {
        
        logo: _.template('<img src="/static/EOxServer_logo_small.png" style="align: center;"/>'),
        
        mainControl: _.template('\
            <!--<div class="cell">Date:</div> \
            <div class="cell" style="padding: 15px; width: 250px"><div id="slider"></div></div> \
            <div class="cell"><button id="btn-download" /></div>--> \
            <div class="ui-widget ui-widget-content ui-corner-all" style="height:3em;margin-bottom:5px;padding:3px;" > \
                <div style="float:left">Date:</div> \
                <div style="padding: 15px; width: 250px; float:left;display:inline;"><div id="slider" style=""></div></div> \
                <button id="btn-download" style="right:0px"/> \
            </div> \
            <div id="tabs-main"> \
                <ul> \
                    <li><a href="#frg-date"><span>Date/Time</span></a></li> \
                    <li><a href="#frg-bbox"><span>Bounding Box</span></a></li> \
                    <li><a href="#frg-info"><span>Server Info</span></a></li> \
                    <li><a href="#frg-help"><span>Help</span></a></li> \
                </ul> \
                <div id="frg-date" class="container"></div> \
                <div id="frg-bbox" class="container"></div> \
                <div id="frg-info" class="container"></div> \
                <div id="frg-help" class="container"></div> \
            </div>'
        ),
        
        datetimeSelection: _.template('\
            <div class="row"> \
                <div class="cell"><a>Begin Date/Time: </a></div> \
                <div class="cell"><input type="text" id="inp-begin-date" size="10" maxlength="10"></input></div> \
                <div class="cell"><input type="text" id="inp-begin-time" size="10" maxlength="10"></input></div> \
            </div> \
            <div class="row"> \
                <div class="cell"><a>End Date/Time: </a></div> \
                <div class="cell"><input type="text" id="inp-end-date" size="10" maxlength="10"></input></div> \
                <div class="cell"><input type="text" id="inp-end-time" size="10" maxlength="10"></input></div> \
            </div>'
        ),
        
        bboxSelection: _.template('\
            <div id="fragment-bbox" class="container"> \
                <div class="row"> \
                    <div class="cell"><label for="minx">Min X:</label><input type="text" id="minx" size="12" maxlength="12"></input></div> \
                    <div class="cell"><label for="maxx">Max X:</label><input type="text" id="maxx" size="12" maxlength="12"></input></div> \
                </div> \
                <div class="row"> \
                    <div class="cell"><label for="miny">Min Y:</label><input type="text" id="miny" size="12" maxlength="12"></input></div> \
                    <div class="cell"><label for="maxy">Max Y:</label><input type="text" id="maxy" size="12" maxlength="12"></input></div> \
                </div> \
                <div class="row"> \
                    <div class="cell"> \
                        <label for="chk-draw-bbox">Draw BBOX</label> \
                        <input type="checkbox" id="chk-draw-bbox"/> \
                    </div> \
                    <div class="cell"><button id="btn-clear-bbox" /></div> \
                </div> \
                <div class="row"> \
                </div> \
            </div>'
        ),
        
        help: '',
        
        serverInfo: _.template('\
            <div id="acc-info"> \
                <% var headers = ["Service Identification", "Service Provider", "Service Metadata", "Operations"] %> \
                <% _.each(["serviceIdentification", "serviceProvider", "serviceMetadata", "operations"], \
                    function(name, idx) {\
                    var section = sections[name] %> \
                <h3><a href="#"><%= headers[idx] %></a></h3> \
                <div> \
                    <% _.each(section, function (value, key) { %> \
                    <div class="row"> \
                        <div class="cell"><%= (typeof key == "string") ? key : "" %></div> \
                        <div class="cell"><p> \
                            <% if (value instanceof Array) { %> \
                                <%= value.join("\\n") %> \
                            <% } else if (value instanceof Object) {%> \
                                <% _.each(value, function (value, key) { %> \
                                    <%= key %>: <%= value %>\
                                <% }); %> \
                            <% } else {%> \
                                <%= value %> \
                            <% } %> \
                        </p></div> \
                    </div> \
                    <% }); %> \
                </div> \
                <% }); %> \
            </div>'
        ),
        /*
         <% _.each(serviceIdentification, function(value, key) {%> \
                    <div class="row"> \
                        <div class="cell"><%= key %></div> \
                        <div class="cell"><p> \
                        <% if (value instanceof Array) { %> \
                            <%= value.join("\\n") %> \
                        <% } else {%> \
                            <%= value %> \
                        <% } %> \
                        </p></div> \
                    </div> \
                    <% }); %> \
                </div> \
                <h3><a href="#">Service Provider</a></h3> \
                <div> \
                    <% _.each(serviceProvider, function(value, key) {%> \
                    <div class="row"> \
                        <div class="cell"><%= key %></div> \
                        <div class="cell"><p> \
                            <%= value %> \
                        </p></div> \
                    </div> \
                    <% }); %> \
         */
        
        downloadSelection: _.template('\
            <div id="coverages"></div> \
            <select class="formats"> \
                <!-- do this dynamically once the formatsSupported works --> \
                <option value="image/tiff" selected>image/tiff</option> \
                <option value="image/jp2">image/jp2</option> \
            </select> \
            <div id="div-downloads"></div>'
        ),
        
        downloadSelectionItem: _.template('\
            <input type="checkbox" checked="true" class="chk-selected" style="float:left;"/> \
            <div style="clear:right;max-width:40em;overflow:hidden;"><%= coverageId %></div> \
            Width:<input type="text" class="sizex" size="5" maxlength="5" <%= (coverageSubtype === "ReferenceableDataset") ? \'disabled="disabled"\' : "" %>/> \
            Height:<input type="text" class="sizey" size="5" maxlength="5" <%= (coverageSubtype === "ReferenceableDataset") ? \'disabled="disabled"\' : "" %>/> \
            CRS:<select class="crs"> \
                <option value="http://www.opengis.net/def/crs/EPSG/0/4326" selected>EPSG:4326</option> \
            </select> \
            <input type="button" class="btn-select-rangetype" value="Select Bands"></input> \
            <input type="button" class="btn-show-info" value="Show Info"></input>'
        ),

        /*<!-- use this template once supportedCRSs are working as expected -->
        <!--<script type="text/template" id="tpl-download-selection-item">
            <input type="checkbox" checked="true" class="chk-selected" style="float:left;"/>
            <div style="clear:right;"><%= coverageId %></div>
            Width:<input type="text" class="sizex" size="5" maxlength="5"/>
            Height:<input type="text" class="sizey" size="5" maxlength="5"/>
            CRS:<select class="crs">
                <% _.each(supportedCRSs, function(crs) { %>
                    <option value="<%= crs %>" <%= (crs === nativeCRS) ? "selected": "" %>><%= crs %></option>
                <% }); %>
            </select>
            
            <input type="button" class="btn-select-rangetype" value="Select Bands"></input>
            <input type="button" class="btn-show-info" value="Show Info"></input>
        </script>-->*/

        rangeTypeSelection: _.template('\
            <% _.each(rangeType, function(band) { %> \
                <tr> \
                    <td><input type="checkbox" <%= (band.selected) ? "checked" : "" %>><%= band.name %> </input></td> \
                </tr> \
            <% }); %>'
        ),

        coverageInfo: _.template('\
            <table style="border: 1px solid black;"> \
                <tr> \
                    <td>Coverage ID</td> \
                    <td><%= coverageId %></td> \
                </tr> \
                <tr> \
                    <td>Subtype</td> \
                    <td><%= coverageSubtype %></td> \
                </tr> \
                <tr> \
                    <td>Origin</td> \
                    <td><%= origin[0] %>, <%= origin[1] %></td> \
                </tr> \
                <tr> \
                    <td>Image Size</td> \
                    <td><%= size[0] %>px x <%= size[1] %>px</td> \
                </tr> \
                <tr> \
                    <td>Time Period</td> \
                    <td><%= timePeriod[0].toISOString() %> - <%= timePeriod[1].toISOString() %></td> \
                </tr> \
            </table> \
            <%  var ratio = size[0]/size[1]; \
                var width, height; \
                if (size[0]>size[1]) { \
                    width = 400; \
                    height = 400 / ratio; \
                } \
                else { \
                    width = 400 * ratio;  \
                    height = 400; \
                } \
            %> \
            <img style="margin:10px" alt="Preview Image" width="<%= width %>" height="<%= height %>" src="/ows?LAYERS=<%= coverageId %>&TRANSPARENT=true&VERSION=1.3.0&EXCEPTIONS=INIMAGE&SERVICE=WMS&REQUEST=GetMap&STYLES=&FORMAT=image%2Fpng&CRS=EPSG%3A4326&BBOX=<%= bounds.values %>&WIDTH=<%= width %>&HEIGHT=<%= height %>"></img> \
        ')
    }

}) ();
