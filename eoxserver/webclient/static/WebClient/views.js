namespace("WebClient").Views = (function() {

    var models = namespace("WebClient.Models");
    var templates = namespace("WebClient.Templates");

    var zpad = function(a, b){
        return(1e15 + a + "").slice(-b);
    }

    /**
     *  view MapView
     *
     * A view responsible displaying the OpenLayers map with all its functionality.
     * Receives two models on startup, a BoundingBoxSelectionModel and a
     * DateTimeIntervalModel for which the map listens for changes and sets
     * attributes.
     */

    var MapView = Backbone.View.extend({
        initialize: function(options) {
            this.bboxModel = options.bboxModel;
            this.dtModel = options.dtModel;
            this.mapParams = options.mapParams;
            this.layerParams = options.layerParams;

            this.bboxModel.on("change", this.onBBoxChange, this);
            this.bboxModel.on("bboxSelect:start", this.onBBoxSelectStart, this);
            this.bboxModel.on("bboxSelect:stop", this.onBBoxSelectStop, this);
            this.dtModel.on("change", this.onDateTimeChange, this);
        },
        render: function() {
            var bounds = OpenLayers.Bounds.fromString("-180,-90,180,90");

            this.bboxLayer = new OpenLayers.Layer.Boxes("Bounding Box", {
                displayInLayerSwitcher: false
            });
            
            var boxControl = new OpenLayers.Control();
            OpenLayers.Util.extend(boxControl, {
                handler: new OpenLayers.Handler.Box(boxControl, {
                    "done": _.bind(this.onBoxSelected, this)
                })
            });
            this.boxControl = boxControl;

            layerDefaults = {
                requestEncoding: 'REST',
                url: [ 'http://a.tiles.maps.eox.at/wmts/','http://b.tiles.maps.eox.at/wmts/','http://c.tiles.maps.eox.at/wmts/','http://d.tiles.maps.eox.at/wmts/','http://e.tiles.maps.eox.at/wmts/' ],
                matrixSet: 'WGS84',
                style: 'default',
                format: 'image/png',
                resolutions: [ 0.70312500000000000000,0.35156250000000000000,0.17578125000000000000,0.08789062500000000000,0.04394531250000000000,0.02197265625000000000,0.01098632812500000000,0.00549316406250000000,0.00274658203125000000,0.00137329101562500000,0.00068664550781250000,0.00034332275390625000,0.00017166137695312500 ],
                maxExtent: new OpenLayers.Bounds(-180.000000,-90.000000,180.000000,90.000000),
                projection: new OpenLayers.Projection('EPSG:4326'),
                gutter: 0,
                buffer: 0,
                units: 'dd',
                transitionEffect: 'resize',
                isphericalMercator: false,
                wrapDateLine: true,
                zoomOffset: 0
            };

            var wmtsLayer = new OpenLayers.Layer.WMTS(
                OpenLayers.Util.applyDefaults(
                    {
                        name: 'EOX Maps Terrain',
                        layer: 'terrain',
                        isBaseLayer: true,
                        attribution: 'Terrain { Data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors and <a href="http://maps.eox.at/#data">others</a>, Rendering &copy; <a href="http://eox.at">EOX</a> }',
                    },
                    layerDefaults
                )
            );

            var wmtsOverlay = new OpenLayers.Layer.WMTS(
                OpenLayers.Util.applyDefaults(
                    {
                        name: 'EOX Maps Overlay',
                        layer: 'overlay',
                        isBaseLayer: false,
                        attribution: 'Overlay { Data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Rendering &copy; <a href="http://eox.at">EOX</a> and <a href="https://github.com/mapserver/basemaps">MapServer</a> }',
                    },
                    layerDefaults
                )
            );

            var mapParams = {
                projection: new OpenLayers.Projection('EPSG:4326'),
                displayProjection: new OpenLayers.Projection('EPSG:4326'),
                numZoomLevels:13,
                units: 'dd',
                maxExtent: bounds,
                restrictedExtent: bounds,
                controls: [
                    new OpenLayers.Control.Navigation(),
                    new OpenLayers.Control.PanZoom(),
                    new OpenLayers.Control.WMSGetFeatureInfo(),
                    new OpenLayers.Control.LayerSwitcher({'ascending': false}),
                    new OpenLayers.Control.Permalink(),
                    new OpenLayers.Control.Permalink('permalink'),
                    new OpenLayers.Control.MousePosition(),
                    new OpenLayers.Control.Attribution(),
                    boxControl
                ],
                layers: [
                    wmtsLayer
                ]
            };

            // allow overrides
            _.extend(mapParams, this.mapParams);

            this.map = new OpenLayers.Map(this.el, mapParams);
            this.map.events.register("moveend", this, this.onMapMoveEnd);

            var useFeatureInfo;
            
            this.layers = _.map(this.layerParams, function(params) {
                var layer;
                if (params.service === "wms") {
                    layer = new OpenLayers.Layer.WMS( params.name, params.url, {
                        layers: params.layerId,
                        transparent: true,
                        version: "1.3.0"
                    }, {
                        maxExtent: bounds,
                        displayOutsideMaxExtent: true,
                        visibility: params.visible,
                        gutter: 5
                    });
                }
                else if (params.service === "wmts") {
                    layer = new OpenLayers.Layer.WMTS({
                        name: params.name,
                        url: params.url,
                        layer: params.layerId,
                        transparent: true,
                        visibility: true,
                        gutter: 0,
                        isBaseLayer: false,
                        style: 'default',
                        matrixSet: 'WGS84',
                        zoomOffset: -1,
                        transitionEffect: 'resize',
                        units: "dd",
                        projection: new OpenLayers.Projection("EPSG:4326".toUpperCase()),
                        sphericalMercator: false,
                        format: 'image/png',
                        resolutions: [0.70312500000000000000,0.35156250000000000000,0.17578125000000000000,0.08789062500000000000,0.04394531250000000000,0.02197265625000000000,0.01098632812500000000,0.00549316406250000000,0.00274658203125000000,0.00137329101562500000,0.00068664550781250000,0.00034332275390625000,0.00017166137695312500,0.00008583068847656250,0.00004291534423828120,0.00002145767211914060,0.00001072883605957030,0.00000536441802978516],
                    });
                }
                else {
                    throw new Error("Service type " + params.service + " is not supported");
                }
                if (params.featureInfo) {
                    useFeatureInfo = {
                        layer: layer,
                        url: params.url
                    }
                }
                return layer;
            });

            this.map.addLayers(this.layers);
            this.map.addLayer(this.bboxLayer);
            this.map.addLayer(wmtsOverlay);

            if (useFeatureInfo) {
                this.infoControl = new OpenLayers.Control.WMSGetFeatureInfo({
                    url: useFeatureInfo.url, 
                    title: 'Identify features by clicking',
                    queryVisible: true,
                    layers: [useFeatureInfo.layer],
                    eventListeners: {
                        getfeatureinfo: _.bind(this.onFeatureInfo, this)
                    }
                });
        
                this.map.addControl(this.infoControl);
                this.infoControl.activate();
            }

            this.map.zoomToExtent(new OpenLayers.Bounds.fromArray(this.bboxModel.get("values")));
        },

        /// internal events

        onBoxSelected: function(bounds) {
            var ll = this.map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.left, bounds.bottom)); 
            var ur = this.map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top));

            this.bboxModel.set({
                values: [ll.lon, ll.lat, ur.lon, ur.lat],
                isSet: true
            });
            this.bboxModel.trigger("bboxSelect:stop");
        },

        onMapMoveEnd: function() {
            if (!this.bboxModel.get("isSet")) {
                this.bboxModel.set("values", this.map.getExtent().toArray());
            }
        },

        onFeatureInfo: function(event) {
            if (event.request.status == 200) {
                if (event.text) {
                    var popup = new OpenLayers.Popup.FramedCloud(
                        null,
                        this.map.getLonLatFromPixel(event.xy),
                        null,
                        event.text,
                        null,
                        true
                    );
                    this.map.addPopup(popup);
                }
            }
            else if (event.request.status >= 400 && event.request.status <= 420) {
            //else if (event.request.status == 500) {
                var popup_text = "No coverages found at point " + this.map.getLonLatFromPixel(event.xy) + "<BR/>" +
                                  " for time " + this.dtModel.getBeginString() + "/" + this.dtModel.getEndString();
                var popup = new OpenLayers.Popup.FramedCloud(
                        null,
                        this.map.getLonLatFromPixel(event.xy),
                        null,
                        popup_text,
                        null,
                        true
                );
                this.map.addPopup(popup);
            }
        },

        /// external events

        onBBoxChange: function() {
            this.bboxLayer.clearMarkers();
            if (this.bboxModel.get("isSet")) {
                var bounds = this.bboxModel.get("values")
                var box = new OpenLayers.Marker.Box(OpenLayers.Bounds.fromArray(bounds));
                box.setBorder("lightgreen", 2);
                this.bboxLayer.addMarker(box);
            }
            else if(!this.bboxModel.get("isSet") && this.bboxModel.hasChanged("isSet")) {
                // set the current view extend as bbox if no real bbox is set
                this.bboxModel.set("values", this.map.getExtent().toArray());
            }
        },
        onBBoxSelectStart: function() {
            this.boxControl.activate();
        },
        onBBoxSelectStop: function() {
            this.boxControl.deactivate();
        },

        /**
         *  function onDateTimeChange
         *
         * Callbackfunction to be called when the selected date/time has
         * changed. Updates all WMS layers (apart from the baselayers) with the
         * new begin/end datetimes.
         */

        onDateTimeChange: function() {
            _.each(this.map.getLayersByClass("OpenLayers.Layer.WMS"), function(layer) {
                if (layer.isBaseLayer) return;
                var timeString = this.dtModel.getBeginString()
                                 + "/" + this.dtModel.getEndString();
                layer.mergeNewParams({time: timeString});
                this.infoControl.vendorParams["TIME"] = timeString;
            }, this);
        }
    });

    /**
     *  view MainControlView
     *
     * This class inherits the main control dialog. It is responsible for the
     * correct initialization of its subviews, as the DateSliderView,
     * DateTimeSelectionView, BoundingBoxSelectionView, and the HelpView.
     *
     * Once the Download button is clicked, the application is navigated to the
     * downloadSelection route.
     */

    var MainControlView = Backbone.View.extend({
        template: templates.mainControl,
        initialize: function(options) {
            this.router = options.router;
            this.dtModel = options.dtModel;
            this.bboxModel = options.bboxModel;
            this.capsModel = options.capsModel;

            // set up subviews

            this.timeSliderView = new TimeSliderView({
                model: this.dtModel,
                url: options.owsUrl,
                eoid: options.eoid
            });

            /*this.dateSliderView = new DateSliderView({
                model: this.dtModel
            });*/
            
            this.dtSelectionView = new DateTimeSelectionView({
                model: this.dtModel
            });
            
            this.bboxSelectionView = new BoundingBoxSelectionView({
                model: this.bboxModel
            });

            this.serviceInfoView = new ServiceInfoView({
                model: this.capsModel
            });
            
            this.helpView = new HelpView();

            this.views = [
                this.timeSliderView,
                this.dtSelectionView,
                this.bboxSelectionView,
                this.serviceInfoView,
                this.helpView
            ];
        },
        events: {
            "click #btn-download": "onDownloadClick"
        },
        render: function() {
            this.$el.html(this.template());

            var that = this;
            
            // setup main dialog
            
            this.$el.dialog({
                create: function (event, ui) {
                    $(".ui-widget-header").append(templates.logo);
                },
                open: function(event, ui) {
                    that.$el.parent().find(".ui-dialog-titlebar-close").hide();
                },
                closeOnEscape: false,
                resizable: false,
                width: 560,
                height: 'auto',
                position: 'top',
            });

            // setup tab layout
            
            this.$("#tabs-main").tabs({
                collapsible: true,
                selected: -1
            });

            this.$("#btn-download").button({
                label: "Download",
            });

            // render subviews

            this.timeSliderView.setElement($("#slider"));
            this.dtSelectionView.setElement(this.$("#frg-date"));
            this.bboxSelectionView.setElement(this.$("#frg-bbox"));
            this.serviceInfoView.setElement(this.$("#frg-info"));
            this.helpView.setElement(this.$("#frg-help"));

            _.each(this.views, function(view) { view.render(); });
        },
        onDownloadClick: function() {
            var begin = this.dtModel.get("begin");
            var end = this.dtModel.get("end");
            var bbox = this.bboxModel.get("values");
            var args = [];
            
            args.push("bbox=" + bbox.join(","));
            args.push("begin=" + this.dtModel.getBeginString());
            args.push("end=" + this.dtModel.getEndString());
            
            Backbone.history.navigate("select?" + args.join("&"), true);
        }
    });

    /**
     *  view DateSlider
     *
     * This view initializes and manages the date slider and its tooltips.
     * Therefore it listenes on a DateTimeIntervalModel which it receives upon
     * initialization and also sets values to it.
     */

    var TimeSliderView = Backbone.View.extend({
        events: {
            "selectionChanged": "onSelectionChanged"
        },
        initialize: function(options) {
            this.url = options.url;
            this.eoid = options.eoid;
        },
        render: function() {
            var model = this.model;
            this.slider = new TimeSlider(this.el, {
                domain: {
                    start: model.get("min"),
                    end: model.get("max")
                },
                brush: {
                    start: model.get("begin"),
                    end: model.get("end")
                },
                datasets: [{
                    id: this.eoid,
                    color: "red",
                    data: new TimeSlider.Plugin.EOWCS({
                        url: this.url,
                        eoid: this.eoid, 
                        dataset: this.eoid
                    })
                }]
            });

        },
        onSelectionChanged: function(event) {
            var e = event.originalEvent;
            this.model.set({
                begin: e.detail.start,
                end: e.detail.end
            });
        }
    });


    var DateSliderView = Backbone.View.extend({
        initialize: function(options) {
            // bind events to member function
            this.model.on("change:begin change:end", this.onDateChange, this);
        },
        events: {
            "slide": "onSlide",
            "slidestop": "onSlideStop",
            "mouseenter .ui-slider-handle": "onMouseEnterHandle",
            "mouseleave .ui-slider-handle": "onMouseLeaveHandle"
        },
        render: function() {
            var minTime = this.model.get("min").getTime(),
                maxTime = this.model.get("max").getTime(),
                beginTime = this.model.get("begin").getTime(),
                endTime = this.model.get("end").getTime();
            
            this.$el.slider({
                range: true,
                values: [beginTime, endTime],
                min: minTime,
                max: maxTime,
                step: 24 /* hours */ * 60 /* minutes */
                    * 60 /* seconds */ * 1000 /* milliseconds */
            });

            this.$tooltip = $("#div-tooltip");
        },

        setToolTipTextAndPosition: function(text, x, y) {
            this.$tooltip.css({
                'left': x + 10 + 'px',
                'top': y + 10 + 'px'
            });
            this.$tooltip.find("a").text(text);
        },
        
        /// event handlers

        onSlide: function(event, ui) {
            var begin = new Date(ui.values[0]);
            var end = new Date(ui.values[1]);
            var text;
            
            if (ui.values[0] != this.model.get("begin").getTime()) {
                text = $.datepicker.formatDate('yy-mm-dd', begin);
            }
            else if (ui.values[1] != this.model.get("end").getTime()) {
                text = $.datepicker.formatDate('yy-mm-dd', end)
            }
            this.setToolTipTextAndPosition(text, event.pageX, event.pageY);
            return true;
        },
        onSlideStop: function(event, ui) {
            this.model.set({
                begin: new Date(ui.values[0]),
                end: new Date(ui.values[1])
            });
        },

        /// Tooltip specific events

        onMouseEnterHandle: function(event) {
            var idx = $(event.target).index();
            var values = this.$el.slider("option", "values");
            var text = $.datepicker.formatDate('yy-mm-dd', new Date(values[idx-1]));
            this.setToolTipTextAndPosition(text, event.pageX, event.pageY);
            this.$tooltip.fadeIn(100);
        },
        onMouseLeaveHandle: function(event) {
            this.$tooltip.css({
                'top': event.pageY + 10 + 'px',
                'left': event.pageX + 10 + 'px',
            }).fadeOut(100);
        },

        /// external events
        
        onDateChange: function() {
            // don't rerender here, just set the values
            this.$el.slider(
                "option", "values",
                [this.model.get("begin").getTime(), this.model.get("end").getTime()]
            );
        }
    });

    /**
     *  view DateTimeSelectionView
     *
     * This view visualizes two date pickers and two time pickers. It listens and
     * writes to a DateTimeIntervalModel.
     */

    var DateTimeSelectionView = Backbone.View.extend({
        template: templates.datetimeSelection,
        initialize: function(options) {
            // bind events to member function
            this.model.on("change", this.onDateTimeChange, this);
        },
        events: {
            "change #inp-begin-date": "onBeginDateChange",
            "change #inp-end-date": "onEndDateChange",
            "change #inp-begin-time": "onBeginTimeChange",
            "change #inp-end-time": "onEndTimeChange"
        },
        render: function() {
            this.$el.html(this.template());

            this.$beginDate = this.$("#inp-begin-date");
            this.$endDate = this.$("#inp-end-date");
            this.$beginTime = this.$("#inp-begin-time");
            this.$endTime = this.$("#inp-end-time");

            var minDate = this.model.get("min"),
                maxDate = this.model.get("max"),
                beginDate = this.model.get("begin"),
                endDate = this.model.get("end");
            
            this.$("#inp-begin-date,#inp-end-date").datepicker({
                showOn: 'focus',
                minDate: minDate,
                maxDate: maxDate,
                dateFormat: 'yy-mm-dd'
            });
            this.$beginDate.datepicker("setDate", beginDate);
            this.$endDate.datepicker("setDate", endDate);
            this.$beginTime.val("" + zpad(beginDate.getHours(), 2) + ":" + zpad(beginDate.getMinutes(), 2));
            this.$endTime.val("" + zpad(endDate.getHours(), 2) + ":" + zpad(endDate.getMinutes(), 2));
        },

        parseDateTime: function($dateField, $timeField, $errorField) {
            try {
                var date = $.datepicker.parseDate("yy-mm-dd", $dateField.val());
                var timeRex = /([0-9]{1,2}):([0-9]{1,2})/;

                var match = timeRex.exec($timeField.val());
                if (match.length != 3) throw new Error();

                var hours = parseInt(match[1]);
                var minutes = parseInt(match[2]);

                if (hours > 23 || hours < 0
                    || minutes > 59 || minutes < 0) throw new Error();
                
                date.setHours(match[1]);
                date.setMinutes(match[2]);

                if ($errorField) {
                    $errorField.removeClass("error");
                }

                return date;
            }
            catch(e) {
                if ($errorField) {
                    $errorField.addClass("error");
                }
            }
        },

        /// internal events
        
        onBeginDateChange: function() {
            var date = this.parseDateTime(this.$beginDate, this.$beginTime, this.$beginDate);
            if (date) {
                this.model.set("begin", date);
            }
        },
        onEndDateChange: function() {
            var date = this.parseDateTime(this.$endDate, this.$endTime, this.$endDate);
            if (date) {
                this.model.set("end", date);
            }
        },
        onBeginTimeChange: function() {
            var date = this.parseDateTime(this.$beginDate, this.$beginTime, this.$beginTime);
            if (date) {
                this.model.set("begin", date);
            }
        },
        onEndTimeChange: function() {
            var date = this.parseDateTime(this.$endDate, this.$endTime, this.$endTime);
            if (date) {
                this.model.set("end", date);
            }
        },

        /// external events
        
        onDateTimeChange: function() {
            var model = this.model;
            if (model.hasChanged("begin")) {
                this.$beginDate.datepicker("setDate", model.get("begin"));
                this.$endDate.datepicker("option", "minDate", model.get("begin"));
            }
            if (model.hasChanged("end")) {
                this.$endDate.datepicker("setDate", model.get("end"));
                this.$beginDate.datepicker("option", "maxDate", model.get("end"));
            }
        }
    });

    /**
     *  view BoundingBoxSelectionView
     *
     * This class is responsible for selecting a bounding box. This can either be
     * achieved through the text input fields or via the Select BBOX button. This
     * emits the event bboxSelect:start on the BoundingBoxSelectionModel other
     * views might listen to (in this case the MapView to draw a bounding box).
     * Once the selection process is finished, the bboxSelect:stop event shall be
     * triggered.
     */

    var BoundingBoxSelectionView = Backbone.View.extend({
        template: templates.bboxSelection,
        initialize: function(options) {
            // bind events to member function
            this.model.on("change", this.onBBoxChange, this);
            this.model.on("bboxSelect:stop", this.onBBoxSelectStop, this);
        },
        events: {
            "change #minx,#miny,#maxx,#maxy": "onBBoxInputChange",
            "change #chk-draw-bbox": "onDrawBBoxChange",
            "click #btn-clear-bbox": "onClearBBoxClick"
        },
        render: function() {
            this.$el.html(this.template());

            this.$inputs = this.$("#minx,#miny,#maxx,#maxy");
            this.$drawBBox = this.$("#chk-draw-bbox");
            this.$clearBBox = this.$("#btn-clear-bbox");

            this.$drawBBox.button({label: "Draw BBOX"});
            this.$clearBBox.button({label: "Clear BBOX"});
        },

        /// internal events
        
        onBBoxInputChange: function() {
            var values = _.map(["#minx", "#miny", "#maxx", "#maxy"], function(id) {
                return parseFloat($(id).val());
            });
            
            this.model.set({
                values: values,
                isSet: true
            });
        },
        onDrawBBoxChange: function() {
            if (this.$drawBBox.is(":checked"))
                this.model.trigger("bboxSelect:start");
            else
                this.model.trigger("bboxSelect:stop");
        },
        onClearBBoxClick: function() {
            this.model.set("isSet", false);
            this.$inputs.val("");
        },

        /// external events
        
        onBBoxChange: function() {
            var $inputs = this.$inputs;
            if (this.model.get("isSet")) {
                var v = this.model.get("values");
                this.$("#minx").val(v[0]);
                this.$("#miny").val(v[1]);
                this.$("#maxx").val(v[2]);
                this.$("#maxy").val(v[3]);
            }
        },
        onBBoxSelectStop: function() {
            if (this.$drawBBox.is(":checked")) {
                this.$drawBBox.trigger("click");
            }
        }
    });

    /**
     *  view ServiceInfoView
     *
     * View to display the service details as extracted from the Capabilities
     * response.
     */
     
    var ServiceInfoView = Backbone.View.extend({
        template: templates.serverInfo,
        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            this.$("#acc-info").accordion({ 
                autoHeight: false,
            });
        }
    });

    /**
     *  view HelpView
     *
     * Simple view for displaying help.
     */

    var HelpView = Backbone.View.extend({
        template: templates.help,
        render: function() {
            this.$el.html(this.template);
            this.$("#div-acc-help").accordion({ 
                autoHeight: false,
            });
        }
    });

    /**
     *  view DownloadSelectionView
     *
     * This view displays all coverages associated with the currently viewed
     * dataset series. The user can 
     */

    var DownloadSelectionView = Backbone.View.extend({
        template: templates.downloadSelection,
        initialize: function(options) {
            this.service = options.service;

            var regex = new RegExp("http://www.opengis.net/def/crs/EPSG/0/([0-9]+)");

            var srids = _.map(this.service.get("serviceMetadata").crssSupported, function(crs) {
                return regex.exec(crs)[1];
            });

            this.itemViews = this.model.map(function(model) {
                return new DownloadSelectionItemView({
                    model: model,
                    srids: srids,
                    owsUrl: options.owsUrl
                });
            });
            this.bbox = options.bbox;
        },
        events: {
            "dialogclose": "onDialogClose",
            "click #btn-select-all": "onSelectAllClick",
            "click #btn-deselect-all": "onDeselectAllClick"
        },
        render: function() {
            this.$el.html(this.template({
                model: this.model.toJSON(),
                service: this.service.toJSON()
            }));
            
            this.$el.dialog({
                title: "Select Coverages for Download",
                autoOpen: false,
                width: 'auto',
                modal: true,
                resizable: false,
                buttons: {
                    "Start Download": _.bind(this.onStartDownloadClick, this)
                }
            });

            this.$("#div-select-buttons").buttonset();
            
            _.each(this.itemViews, function(view) {
                this.$("#coverages").append(view.render().$el);
            }, this);

            this.$el.dialog("open");
        },

        /// internal events
        onSelectAllClick: function() {
            this.$('.chk-selected:not(:checked)').trigger("click").trigger("change");
        },
        onDeselectAllClick: function() {
            this.$('.chk-selected:checked').trigger("click").trigger("change");
        },
        
        onDialogClose: function() {
            Backbone.history.navigate("", true);
        },

        onStartDownloadClick: function() {
            var selected = _.filter(this.itemViews, function(view) {
                return view.isSelected();
            });

            if (selected.length > 0) {
                var format = this.$(".formats").val();
                var bbox = this.bbox;
                var confirmationRequired = false;
                var urls = _.map(selected, function(view) {
                    var coverage = view.model;
                    var params = view.getParameters();
                    params.format = format;
                    params.bbox = bbox;

                    if (((params.sizeX || coverage.get("size")[0])
                        * (params.sizeY || coverage.get("size")[1])) > 10000)
                        confirmationRequired = true;
                    return coverage.getDownloadUrl(params);
                });

                if ((confirmationRequired && confirm("At least of the requested images is potentially large. Do you wish to continue the download?")) || !confirmationRequired) {
                    _.each(urls, function(url) {
                        this.$("#div-downloads").append($('<iframe style="display:none" src="' + url + '"></iframe>'));
                    }, this);
                    
                    this.$el.dialog("destroy");
                    Backbone.history.navigate("", true);
                }
            }
        }
    });

    /**
     *  view DownloadSelectionItemView
     *
     * A view for displaying a single coverage for selection.
     */

    var DownloadSelectionItemView = Backbone.View.extend({
        template: templates.downloadSelectionItem,
        attributes: {
            class: "ui-widget ui-widget-content ui-corner-all ui-coverage-item"
        },
        initialize: function(options) {
            this.owsUrl = options.owsUrl;
            this.srids = options.srids;
            var bands = _.pluck(this.model.getRangeType(), "name");
            this.rangetypeSelection = new models.RangeTypeSelectionModel({
                availableBands: bands,
                selectedBands: bands
            });
        },
        events: {
            "click .btn-select-rangetype": "onSelectRangeTypeClick",
            "click .btn-show-info": "onShowInfoClick"
        },
        render: function() {
            this.$el.html(this.template({
                model: this.model.toJSON(),
                srids: this.srids
            }));
            return this;
        },

        /// internal events
        
        onSelectRangeTypeClick: function() {
            var rangeTypeView = new RangeTypeSelectionDialogView({
                model: this.rangetypeSelection
            });
            rangeTypeView.render();
        },
        
        /**
         *  callback onShowInfoClick
         *
         * Function, that gets triggered when the show info button is clicked
         * for the selected coverage. Opens a new CoverageInfoView and displays
         * additional coverage information.
         */

        onShowInfoClick: function() {
            var infoView = new CoverageInfoView({
                model: this.model,
                owsUrl: this.owsUrl
            });
            infoView.render();
        },

        /// methods

        /**
         *  method isSelected
         *
         * Returns true if the associated coverage is selected for download.
         */
         
        isSelected: function() {
            return this.$(".chk-selected").is(":checked");
        },

        /**
         *  method getParameters
         *
         * Returns an object containing key-value pairs of options to be passed
         * to the libcoverage.js functions according to the given inputs.
         */
        
        getParameters: function() {
            var params = {};
            
            var sizex = parseInt(this.$(".sizex").val());
            var sizey = parseInt(this.$(".sizey").val());
            if(!isNaN(sizex)) params.sizeX = sizex;
            if(!isNaN(sizey)) params.sizeY = sizey;

            /// get rangeSubset
            if (!_.isEqual(this.rangetypeSelection.get("selectedBands"),
                           this.rangetypeSelection.get("availableBands"))) {
                params.rangeSubset = this.rangetypeSelection.get("selectedBands");
            }

            var selectedCRS = this.$(".crs").val(); // TODO: find out the correct one
            if (this.model.get("nativeCRS") !== selectedCRS)
                params.outputCRS = selectedCRS;
            
            return params;
        }
    });

    /**
     *  view RangeTypeSelectionView
     *
     * View to select a range subset from a coverages range type. 
     */

    var RangeTypeSelectionView = Backbone.View.extend({
        initialize: function(options) {
            this.limitTo = options.limitTo;
        },
        template: templates.rangeTypeSelection,
        events: {
            "sortstop": "onSortStop",
            "change input": "onChangeSelection",
        },
        render: function() {
            this.$el.html(this.template(this.model.toJSON()));

            this.$el.sortable({
                containment: "parent",
                placeholder: "ui-state-highlight",
                forcePlaceholderSize: true,
                axis: "y",
                tolerance: "pointer"
            }).disableSelection();
        },

        /// internal events

        onSortStop: function() {
            this.resetBands();
        },

        onChangeSelection: function() {
            var $checked = this.$("input:checked");
            var $notChecked = this.$("input:not(:checked)");
            if (this.limitTo && $checked.size() >= this.limitTo) {
                // deactivate all unchecked checkboxes
                $notChecked.attr("disabled", true);
            }
            else {
                // activate all checkboxes
                $notChecked.attr("disabled", false);
            }

            this.resetBands();
        },

        /// internal methods

        resetBands: function() {
            var $checked = this.$("input:checked");
            var bands = $checked.map(function() {
                return $(this).attr("band");
            }).get();
            this.model.set("selectedBands", bands);
        }
    });

    /**
     *  view RangeTypeSelectionDialogView
     *
     * Wraps the RangeTypeSelectionView in a dialog
     */

    var RangeTypeSelectionDialogView = Backbone.View.extend({
        initialize: function() {
            this.rangeTypeSelectionView = new RangeTypeSelectionView({
                model: this.model
            });
        },
        render: function() {
            this.$el.html('<div id="div-coverage-info-bands"></div>');
            this.rangeTypeSelectionView.setElement(this.$("#div-coverage-info-bands"));
            this.rangeTypeSelectionView.render();
            
            this.$el.dialog({
                title: "Select Bands for Range Subsetting",
                autoOpen: true,
                width: 'auto',
                modal: true,
                resizable: false,
                buttons: {
                    "Okay": _.bind(this.onOkayClick, this),
                    "Cancel": _.bind(this.onCancelClick, this)
                }
            });

            this.previousSelection = this.model.get("selectedBands");
        },

        /// internal events

        onOkayClick: function() {
            if (this.model.get("selectedBands").length == 0) {
                alert("At least one band has to be selected!");
                return;
            }
            this.$el.dialog("destroy");
            this.remove();
        },

        onCancelClick: function() {
            this.model.set("selectedBands", this.previousSelection);
            this.$el.dialog("destroy");
            this.remove();
        }
    });

    /**
     *  view CoverageInfoView
     *
     * View to display additional info for a coverage.
     */

    var CoverageInfoView = Backbone.View.extend({
        initialize: function(options) {
            this.owsUrl = options.owsUrl;
            this.rangeTypeModel = new models.RangeTypeSelectionModel({
                availableBands: _.pluck(this.model.get("rangeType"), "name")
            });
            this.rangeTypeModel.on("change", this.onRangeTypeSelectionChange, this);
        },
        template: templates.coverageInfo,
        events: {
            "dialogbeforeclose": "onDialogClose",
            "slide #div-coverage-info-opacity": "onOpacitySlide"
        },
        render: function() {
            this.$el.html(this.template({model: this.model.toJSON()}));
            this.$el.attr("id", "div-coverage-info");
            
            this.$el.dialog({
                title: "Coverage Info",
                autoOpen: true,
                width: 'auto',
                maxWidth: 600,
                modal: true,
                resizable: false
            });

            var bounds = new OpenLayers.Bounds.fromString(this.model.get("bounds").lower.join(",") + "," + this.model.get("bounds").upper.join(","), true);

            /// background

            layerDefaults = {
                requestEncoding: 'REST',
                url: [ 'http://a.tiles.maps.eox.at/wmts/','http://b.tiles.maps.eox.at/wmts/','http://c.tiles.maps.eox.at/wmts/','http://d.tiles.maps.eox.at/wmts/','http://e.tiles.maps.eox.at/wmts/' ],
                matrixSet: 'WGS84',
                style: 'default',
                format: 'image/png',
                resolutions: [ 0.70312500000000000000,0.35156250000000000000,0.17578125000000000000,0.08789062500000000000,0.04394531250000000000,0.02197265625000000000,0.01098632812500000000,0.00549316406250000000,0.00274658203125000000,0.00137329101562500000,0.00068664550781250000,0.00034332275390625000,0.00017166137695312500 ],
                maxExtent: new OpenLayers.Bounds(-180.000000,-90.000000,180.000000,90.000000),
                projection: new OpenLayers.Projection('EPSG:4326'),
                gutter: 0,
                buffer: 0,
                units: 'dd',
                transitionEffect: 'resize',
                isphericalMercator: false,
                wrapDateLine: true,
                zoomOffset: 0
            };

            var wmtsLayer = new OpenLayers.Layer.WMTS(
                OpenLayers.Util.applyDefaults(
                    {
                        name: 'EOX Maps Terrain',
                        layer: 'terrain',
                        isBaseLayer: true,
                        attribution: 'Terrain { Data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors and <a href="http://maps.eox.at/#data">others</a>, Rendering &copy; <a href="http://eox.at">EOX</a> }',
                    },
                    layerDefaults
                )
            );

            /// set up 'bands' eo-wms layer

            var rangeType = this.model.get("rangeType");
            var initialBands = (rangeType.length < 3) ? rangeType[0].name : _.pluck(_.first(rangeType, 3), "name").join(",");

            this.layer = new OpenLayers.Layer.WMS(this.model.get("coverageId"), this.owsUrl, {
                layers: this.model.get("coverageId") + "_bands",
                transparent: true,
                version: "1.3.0",
                dim_bands: initialBands
            }, {
                maxExtent: bounds,
                displayOutsideMaxExtent: true,
                gutter: 5
            });

            /// footprint layer

            var vectorLayer = new OpenLayers.Layer.Vector('Basic Vector Layer');

            var footprint = this.model.get("footprint");
            var points = [];
            for(var i = 0; i < footprint.length; i += 2) {
                points.push(new OpenLayers.Geometry.Point(footprint[i+1], footprint[i]));
            }
            points.push(points[0]);
            vectorLayer.addFeatures([
                new OpenLayers.Feature.Vector(
                    new OpenLayers.Geometry.LineString(points)
                )
            ]);

            /// map creation

            this.map = new OpenLayers.Map({
                div: this.$("#div-coverage-info-map").get(0),
                projection: new OpenLayers.Projection("EPSG:4326"),
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                numZoomLevels:13,
                units: "d",
                layers: [
                    wmtsLayer, this.layer, vectorLayer
                ]
            });
            this.map.zoomToExtent(bounds);

            /// setup range type selection

            var rangeTypeSelectionView = new RangeTypeSelectionView({
                model: this.rangeTypeModel,
                limitTo: 3
            });
            rangeTypeSelectionView.setElement(this.$("#div-coverage-info-bands"));
            rangeTypeSelectionView.render();

            /// opacity slider
            
            this.$("#div-coverage-info-opacity").slider({
                min: 0.,
                max: 1.,
                value: 1.,
                step: 0.025
            });
        },

        /// internal events
        
        onDialogClose: function() {
            this.map.destroy();
        },

        onOpacitySlide: function(evt, ui) {
            this.layer.setOpacity(ui.value);
        },

        onRangeTypeSelectionChange: function() {
            var bands = this.rangeTypeModel.get("selectedBands");
            if(bands.length == 1 || bands.length == 3) {
                this.layer.mergeNewParams({
                    dim_bands: bands.join(",")
                });
            }
        }
    });

    

    return {
        MapView: MapView,
        MainControlView: MainControlView,
        DownloadSelectionView: DownloadSelectionView
    }

})();
