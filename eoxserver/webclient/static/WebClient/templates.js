
namespace("WebClient").Templates = (function() {

    return {
        
        logo: "", // to be overridden
        
        mainControl: _.template('\
            <table class="ui-widget ui-widget-content ui-corner-all"> \
                <tr> \
                    <td style="vertical-align:middle">Date:</td> \
                    <td style="vertical-align:middle;width:70%;padding:10px"><div id="slider"></div></td> \
                    <td style="vertical-align:middle;width:20%;"><button id="btn-download"/></td> \
                </tr> \
            </table> \
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
            <div id="div-acc-help" style="width: 100%; max-height: 640px; overflow: auto;"> \
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
            <% var id = serviceIdentification, pr = serviceProvider, md = serviceMetadata, op = operations; %> \
            <div id="acc-info" style="width: 100%; max-height: 640px; overflow: auto;"> \
                <h3><a href="#">Service Identification</a></h3> \
                <div> \
                    <div class="row"> \
                        <div class="cell">Title</div> \
                        <div class="cell"><p><%= id.title %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Abstract</div> \
                        <div class="cell"><p class="scrollable"><%= id.abstract %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Keywords</div> \
                        <div class="cell"><p class="scrollable"><%= id.keywords.join(", ") %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Type</div> \
                        <div class="cell"><p><%= id.serviceType %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Version</div> \
                        <div class="cell"><p><%= id.serviceTypeVersion %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Profiles</div> \
                        <div class="cell"><ul class="scrollable"> \
                            <% _.each(id.profiles, function(profile) { %> \
                                <li><%= profile %></li>\
                            <% }); %> \
                        </ul></div> \
                    </div> \
                    <div class="row"> \
                        <div class="cell">Fees</div> \
                        <div class="cell"><p><%= id.fees %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Constraints</div> \
                        <div class="cell"><p><%= id.accessConstraints %></p></div>\
                    </div> \
                </div> \
                <h3><a href="#">Service Provider</a></h3> \
                <div> \
                    <div class="row"> \
                        <div class="cell">Name</div> \
                        <div class="cell"><p><%= pr.providerName %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Site</div> \
                        <div class="cell"><p><%= pr.providerSite %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Individual</div> \
                        <div class="cell"><p><%= pr.individualName %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Role</div> \
                        <div class="cell"><p><%= pr.role  %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Position</div> \
                        <div class="cell"><p><%= pr.positionName  %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Voice</div> \
                        <div class="cell"><p><%= pr.contactInfo.phone.voice %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Facsimile</div> \
                        <div class="cell"><p><%= pr.contactInfo.phone.facsimile %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Address</div> \
                        <div class="cell"><p><%= pr.contactInfo.address.deliveryPoint %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">City</div> \
                        <div class="cell"><p><%= pr.contactInfo.address.city %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Region</div> \
                        <div class="cell"><p><%= pr.contactInfo.address.region %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Postal Code</div> \
                        <div class="cell"><p><%= pr.contactInfo.address.postalCode %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Country</div> \
                        <div class="cell"><p><%= pr.contactInfo.address.country %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">E-Mail</div> \
                        <div class="cell"><p><%= pr.contactInfo.address.electronicMailAddress %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Homepage</div> \
                        <div class="cell"><p><%= pr.contactInfo.onlineResource %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Hours</div> \
                        <div class="cell"><p><%= pr.contactInfo.hoursOfService %></p></div>\
                    </div> \
                    <div class="row"> \
                        <div class="cell">Contact</div> \
                        <div class="cell"><p><%= pr.contactInfo.contactInstructions %></p></div>\
                    </div> \
                </div> \
                <h3><a href="#">Service Metadata</a></h3> \
                <div> \
                    <div class="row"> \
                        <div class="cell">Formats</div> \
                        <div class="cell"><ul> \
                            <% _.each(md.formatsSupported, function(format) { %> \
                                <li><%= format %></li>\
                            <% }); %> \
                        </ul></div> \
                    </div> \
                    <div class="row"> \
                        <div class="cell">CRSs</div> \
                        <div class="cell"><ul> \
                            <% _.each(md.crssSupported, function(crs) { %> \
                                <li><%= crs %></li>\
                            <% }); %> \
                        </ul></div> \
                    </div> \
                </div> \
                <h3><a href="#">Operations</a></h3> \
                <div> \
                    <% _.each(op, function(operation) { %> \
                        <div class="row"> \
                            <div class="cell"><%= operation.name %></div> \
                            <div class="cell"> \
                                GET: <%= operation.getUrl %> \
                                POST: <%= operation.postUrl %> \
                            </div> \
                        </div> \
                    <% }); %> \
                </div> \
            </div> \
        '),
        
        downloadSelection: _.template('\
            <div id="coverages"></div> \
            <div id="div-select-buttons"> \
            <button id="btn-select-all">Select All</button> \
            <button id="btn-deselect-all">Deselect All</button> \
            </div> \
            <select class="formats"> \
                <% _.each(service.serviceMetadata.formatsSupported, function(format) { %> \
                    <option value="<%= format %>"> <%= format %> </option> \
                <% }); %> \
            </select> \
            <div id="div-downloads"></div>'
        ),
        
        downloadSelectionItem: _.template('\
            <input type="checkbox" checked="true" class="chk-selected" style="float:left;"/> \
            <div style="clear:right;max-width:40em;overflow:hidden;"><%= model.coverageId %></div> \
            <% if (model.coverageSubtype === "ReferenceableDataset") { %> \
                Width:<input type="text" class="sizex" size="5" maxlength="5" disabled="disabled" /> \
                Height:<input type="text" class="sizey" size="5" maxlength="5" disabled="disabled" /> \
                <div style="padding-left: 50px; float:right"></div> \
            <% } else { %> \
                Width:<input type="text" class="sizex" size="5" maxlength="5" /> \
                Height:<input type="text" class="sizey" size="5" maxlength="5" /> \
                CRS:<select class="crs"> \
                    <% _.each(srids, function(srid) { %> \
                        <% var crsurl = "http://www.opengis.net/def/crs/EPSG/0/" + srid %> \
                        <option value="<%= crsurl %>" <%= (crsurl === model.nativeCRS) ? "selected": "" %>>EPSG:<%= srid %></option> \
                    <% }); %> \
                </select> \
            <% } %> \
            <input type="button" class="btn-select-rangetype" value="Select Bands"></input> \
            <input type="button" class="btn-show-info" value="Show Info"></input>'
        ),

        rangeTypeSelection: _.template('\
            <% _.each(availableBands, function(band) { %> \
                <div class="ui-widget ui-widget-content ui-corner-all ui-band-item"> \
                    <input type="checkbox" band="<%= band%>" <%= (_.contains(selectedBands, band))?"checked":""%>></input><%= band %> \
                </div> \
            <% }); %> \
        '),

        coverageInfo: _.template('\
            <div class="ui-widget ui-widget-content ui-corner-all ui-section"> \
                <table> \
                    <tr> \
                        <td>Coverage ID</td> \
                        <td style="max-width:670px;overflow-x:scroll"><%= model.coverageId %></td> \
                    </tr> \
                    <tr> \
                        <td>Subtype</td> \
                        <td><%= model.coverageSubtype %></td> \
                    </tr> \
                    <tr> \
                        <td>Envelope</td> \
                        <td><%= model.bounds.lower.join(", ") %>, <%= model.bounds.upper.join(", ") %></td> \
                    </tr> \
                    <tr> \
                        <td>Image Size</td> \
                        <td><%= model.size[0] %>px x <%= model.size[1] %>px</td> \
                    </tr> \
                    <tr> \
                        <td>Time Period</td> \
                        <td><%= model.timePeriod[0].toISOString() %> - <%= model.timePeriod[1].toISOString() %></td> \
                    </tr> \
                </table> \
            </div> \
            <%  var ratio = model.size[0] / model.size[1]; \
                var width, height; \
                if (model.size[0] > model.size[1]) { \
                    width = 400; \
                    height = 400 / ratio; \
                } \
                else { \
                    width = 400 * ratio;  \
                    height = 400; \
                } \
            %> \
            <div style="float:left;" class="ui-widget ui-widget-content ui-corner-all ui-section"> \
                <div id="div-coverage-info-map" class="" style="width:500px;height:500px"></div>\
                <table style="width:100%"><tr><td>Opacity:</td><td style="width:80%;padding-right:0.5em"><div id="div-coverage-info-opacity"></div></td></tr></table>\
            </div> \
            <div class="ui-widget ui-widget-content ui-corner-all ui-section" style="float:right"> \
                Select Bands:\
                <div id="div-coverage-info-bands"></div> \
            </div> \
        ')
    }

}) ();
