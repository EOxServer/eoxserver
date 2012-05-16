
namespace("WebClient").Templates = (function() {

    return {
        
        logo: '<img src="/static/EOxServer_logo_small.png" style="align: center;"/>',
        
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
        
        help: '\
            <div id="div-acc-help"> \
                <h3><a href="#">General</a></h3> \
                <div> \
                    <p>Click and drag the map to view the area of interest. Use the  \
                    scroll wheel or hold shift and draw a zoom box to zoom.</p> \
                    <p>To switch the outlines or the preview layers on or off \
                    expand the plus icon on the upper right corner.</p> \
                    <p>Simply clicking on the map will open a window showing  \
                    information about the dataset(s) available at this position.</p> \
                </div> \
                <h3><a href="#">Selection of Date and Time</a></h3> \
                <div> \
                    <p>The begin and end date and time values are used for visualizing \
                    datasets which lie within that time period. It is used for both footprint \
                    overlays and also for the actual download.</p> \
                    <p>The slider handles can be used to adjust the begin and the end date. \
                    Alternatively, in the tab "Date/Time" the dates can be selected via a \
                    date picking widget which can be activated by clicking in the date field.</p> \
                    <p>Also the begin and end time parameters can be set in the according time \
                    input fields.</p> \
                </div> \
                <h3><a href="#">Selection of Bounds</a></h3> \
                <div> \
                    <p>To subset the area of interest, use the "Bounding Box" \
                    tab of the control panel. You can either manually set the values \
                    of the bounding box, or you can use the "Draw BBOX" function.</p> \
                    <p>Once the "Draw BBOX" button is clicked, the bounding box \
                    can be drawed directly in the map. Alternatively it can be adjusted afterwards \
                    in the according input fields.</p> \
                    <p>The Bounding Box can be removed by clicking on the \
                    "Clear BBOX" button.</p> \
                    <p>If no Bounding Box is given, the map extent of the current  \
                    view is used.</p> \
                </div> \
                <h3><a href="#">Download of Coverages</a></h3> \
                <div> \
                    <p>When the "Download" button is clicked, the download dialog is opened. \
                    It contains a list of all coverages that lie within the specified bounds \
                    and time span.</p> \
                    <p>All coverages that are checked will be downloaded upon a click on \
                    "Start Download".</p> \
                    <p>For Rectified Datasets, an optional size for each dimension can be \
                    given. If left empty, the resulting image will not be scaled. Referenceable \
                    Datasets cannot be scaled and the value in the size input fields only displays \
                    their original size.</p> \
                    <p>In the "Bands" dropdown box a number of bands can be selected, when \
                    downloading the image. Multiple bands can be selected by pressing the \
                    "Control"-key while selecting the entries.</p> \
                    <p>When the button "Start Download" is clicked, all selected coverages will be \
                    downloaded with the given parameters. For large downloads (larger than 1000x1000 \
                    pixel) a warning will be shown.</p> \
                </div> \
            </div> \
        ',
        
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
