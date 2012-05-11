$(document).ready(function() {

var views = namespace("App.Views");
var models = namespace("App.Models");

/**
 *  view MapView
 *
 * A view responsible displaying the OpenLayers map with all its functionality.
 * Receives two models on startup, a BoundingBoxSelectionModel and a
 * DateTimeIntervalModel for which the map listens for changes and sets
 * attributes.
 */

views.MapView = Backbone.View.extend({
    initialize: function(options) {
        this.bboxModel = options.bboxModel;
        this.dtModel = options.dtModel;
        this.layerParams = options.layerParams;

        this.bboxModel.on("change", this.onBBoxChange, this);
        this.bboxModel.on("bboxSelect:start", this.onBBoxSelectStart, this);
        this.bboxModel.on("bboxSelect:stop", this.onBBoxSelectStop, this);
        this.dtModel.on("change", this.onDateTimeChange, this);
    },
    events: {
        // needed?
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

        var wms_layer = new OpenLayers.Layer.WMS(
            "OpenLayers WMS",
            "http://vmap0.tiles.osgeo.org/wms/vmap0",
            {layers: 'basic'}
        );

        var map_params = {
            projection: new OpenLayers.Projection("EPSG:4326"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            numZoomLevels:13,
            units: "d",
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
                new OpenLayers.Control.KeyboardDefaults({observeElement: "map_div"}),
                boxControl
            ],
            layers: [
                wms_layer,
                this.bboxLayer
            ]
        };

        this.map = new OpenLayers.Map(this.el, map_params);

        this.layers = _.map(this.layerParams, function(params) {
            if (params.service === "wms") {
                return new OpenLayers.Layer.WMS( params.name, params.url, {
                    layers: params.layerId,
                    transparent: true,
                    version: "1.3.0"
                }, {
                    maxExtent:bounds,
                    displayOutsideMaxExtent:true,
                    visibility: params.visible,
                    gutter: 5
                });
            }
            else if (params.service === "wmts") {
                new OpenLayers.Layer.WMTS({
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
                    resolutions:[0.70312500000000000000,0.35156250000000000000,0.17578125000000000000,0.08789062500000000000,0.04394531250000000000,0.02197265625000000000,0.01098632812500000000,0.00549316406250000000,0.00274658203125000000,0.00137329101562500000,0.00068664550781250000,0.00034332275390625000,0.00017166137695312500,0.00008583068847656250,0.00004291534423828120,0.00002145767211914060,0.00001072883605957030,0.00000536441802978516],
                });
            }
        });

        this.map.addLayers(this.layers);

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

    /// external events

    onBBoxChange: function() {
        this.bboxLayer.clearMarkers();
        if (this.bboxModel.get("isSet")) {
            var bounds = this.bboxModel.get("values")
            var box = new OpenLayers.Marker.Box(OpenLayers.Bounds.fromArray(bounds));
            box.setBorder("lightgreen", 2);
            this.bboxLayer.addMarker(box);
        }
    },
    onBBoxSelectStart: function() {
        this.boxControl.activate();
    },
    onBBoxSelectStop: function() {
        this.boxControl.deactivate();
    },
    onDateTimeChange: function() {
        _.each(this.layers, function(layer) {
            if(layer.mergeNewParams) {
                var timeString = this.dtModel.getBeginString()
                                 + "/" + this.dtModel.getEndString();
                layer.mergeNewParams({time: timeString});
            }
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

views.MainControlView = Backbone.View.extend({
    template: _.template($('#tpl-main-control').html()),
    initialize: function(options) {
        this.router = options.router;
        this.dtModel = options.dtModel;
        this.bboxModel = options.bboxModel;
        this.capsModel = options.capsModel;

        // set up subviews

        this.dateSliderView = new views.DateSliderView({
            model: this.dtModel
        });
        
        this.dtSelectionView = new views.DateTimeSelectionView({
            model: this.dtModel
        });
        
        this.bboxSelectionView = new views.BoundingBoxSelectionView({
            model: this.bboxModel
        });

        this.serviceInfoView = new views.ServiceInfoView({
            model: this.capsModel
        });
        
        this.helpView = new views.HelpView();

        this.views = [
            this.dateSliderView,
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
                $(".ui-widget-header").append($("#tpl-logo").html());
            },
            open: function(event, ui) {
                that.$el.parent().find(".ui-dialog-titlebar-close").hide();
            },
            closeOnEscape: false,
            resizable: false,
            width: 550,
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

        this.dateSliderView.setElement(this.$("#slider"));
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
        
        if (this.bboxModel.get("isSet")) {
            args.push("bbox=" + bbox.join(","));
        }
        args.push("begin=" + this.dtModel.getBeginString());
        args.push("end=" + this.dtModel.getEndString());
        
        this.router.navigate("select?" + args.join("&"), true);
    },
    show: function() {}, // TODO
    hide: function() {},
});

/**
 *  view DateSlider
 *
 * This view initializes and manages the date slider and its tooltips.
 * Therefore it listenes on a DateTimeIntervalModel which it receives upon
 * initialization and also sets values to it.
 */

views.DateSliderView = Backbone.View.extend({
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
            max: maxTime
        });

        this.$tooltip = $("#div-tooltip");
    },

    setToolTipTextAndPosition: function(text, x, y) {
        this.$tooltip.css({
            'top': event.pageY + 10 + 'px',
            'left': event.pageX + 10 + 'px',
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

views.DateTimeSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-datetime-selection').html()),
    initialize: function(options) {
        // bind events to member function
        this.model.on("change", this.onDateTimeChange, this);
    },
    events: {
        "change #inp-begin-date": "onBeginDateTimeChange",
        "change #inp-end-date": "onEndDateTimeChange"
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
    },

    /// internal events
    
    onBeginDateTimeChange: function() {
        try {
            var date = $.datepicker.parseDate("yy-mm-dd", this.$beginDate.val());
            this.model.set("begin", date);
            this.$beginDate.removeClass("error");
        }
        catch(e) {
            this.$beginDate.addClass("error");
        }
    },
    onEndDateTimeChange: function() {
        try {
            var date = $.datepicker.parseDate("yy-mm-dd", this.$endDate.val());
            this.model.set("end", date);
            this.$endDate.removeClass("error");
        }
        catch(e) {
            this.$endDate.addClass("error");
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

views.BoundingBoxSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-bbox-selection').html()),
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
            _.each(this.model.get("values"), function(v, i) {
                $($inputs[i]).val(v);
            });
        }
    },
    onBBoxSelectStop: function() {
        if (this.$drawBBox.is(":checked")) {
            this.$drawBBox.trigger("click");
        }
    }
});

views.ServiceInfoView = Backbone.View.extend({
    template: _.template($('#tpl-server-info').html()),
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

views.HelpView = Backbone.View.extend({
    template: _.template($('#tpl-help').html()),
    render: function() {
        this.$el.html(this.template());
    }
});

/**
 *  view DownloadSelectionView
 *
 * This view displays all coverages associated with the currently viewed
 * dataset series. The user can 
 */

views.DownloadSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-download-selection').html()),
    initialize: function(options) {
        this.router = options.router;
        this.itemViews = this.model.map(function(model) {
            return new views.DownloadSelectionItemView({
                model: model
            });
        });
    },
    events: {
        "dialogclose": "onDialogClose"
    },
    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        this.$el.dialog({
            autoOpen: false,
            width: 'auto',
            modal: true,
            buttons: {
                "Start Download": _.bind(this.onStartDownloadClick, this)
            }
        });
        
        _.each(this.itemViews, function(view) {
            this.$("#coverages").append(view.render().$el);
        }, this);

        this.$el.dialog("open");
    },
    onDialogClose: function() {
        this.router.navigate("", true);
    },
    onStartDownloadClick: function() {
        var selected = _.filter(this.itemViews, function(view) {
            return view.isSelected();
        });

        if (selected.length > 0) {
            _.each(selected, function(view) {
                var coverage = view.model;
                var params = view.getParameters();
                var url = coverage.getDownloadUrl(params);

                // TODO apply bbox and format
                // TODO make download link
                // TODO add iframe to download
            });
            
            this.$el.dialog("destroy");
            this.router.navigate("", true);
        }
    }
});

/**
 *
 *
 *
 *
 *
 */

views.DownloadSelectionItemView = Backbone.View.extend({
    template: _.template($('#tpl-download-selection-item').html()),
    attributes: {
        class: "ui-widget ui-widget-content ui-corner-all ui-coverage-item"
    },
    initialize: function() {
        this.rangetypeSelection = new models.RangeTypeSelectionCollection(
            this.model.getRangeType()
        );
    },
    events: {
        "click .btn-select-rangetype": "onSelectRangeTypeClick",
        "click .btn-show-info": "onShowInfoClick"
    },
    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    },
    isSelected: function() {
        return this.$(".chk-selected").is(":checked");
    },
    getParameters: function() {
        var params = {};
        
        var sizex = parseInt(this.$(".sizex").val());
        var sizey = parseInt(this.$(".sizey").val());
        if(!isNaN(sizex)) params.sizeX = sizex;
        if(!isNaN(sizey)) params.sizeY = sizey;

        // TODO: get selected CRS
        if(!this.rangetypeSelection.all(function(band) { return band.get("selected"); })) {
            params.rangeSubset = this.rangetypeSelection.chain().filter(function(band) {
                return band.get("selected");
            }).map(function(band) {
                return band.get("name")
            }).value();
        }

        var selectedCRS = this.$(".crs").val(); // TODO: find out the correct one
        if (this.model.get("nativeCRS") !== selectedCRS)
            params.outputCRS = selectedCRS;
        
        return params;
    },
    onSelectRangeTypeClick: function() {
        var rangeTypeView = new views.RangeTypeSelectionView({
            model: this.rangetypeSelection
        });
        rangeTypeView.render();
    },
    onShowInfoClick: function() {
        var infoView = new views.CoverageInfoView({
            model: this.model,
        });
        infoView.render();
    }
});


/**
 *
 *
 */

views.RangeTypeSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-rangetype-selection').html()),
    tagName: "table",
    render: function() {
        this.$el.html(this.template({
            rangeType: this.model.toJSON()
        }));
        
        this.$el.dialog({
            autoOpen: true,
            width: 'auto',
            modal: true,
            resizable: false,
            buttons: {
                "Okay": _.bind(this.onOkayClick, this),
                "Cancel": _.bind(this.onCancelClick, this)
            }
        });
    },
    onOkayClick: function() {
        var selected = this.$("input").map(function() {
            return $(this).is(":checked");
        }).get();
        
        if (_.any(selected)) {
            this.model.each(function(band, i) {
                band.set("selected", selected[i]);
            });
            this.$el.dialog("destroy");
            this.remove();
            return;
        }
        // TODO: show better error here!
        alert("At least one band has to be selected!");
    },
    onCancelClick: function() {
        this.$el.dialog("destroy");
        this.remove();
    }
});

/**
 *
 *
 *
 *
 *
 */

views.CoverageInfoView = Backbone.View.extend({
    template: _.template($('#tpl-coverage-info').html()),
    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        
        this.$el.dialog({
            autoOpen: true,
            width: 'auto',
            modal: true,
            resizable: false
        });
        // TODO: show a small map with only the coverage in it
    }
});


/// MODELS

models.DateTimeInterval = Backbone.Model.extend({
    defaults: {
        begin: new Date(),
        end: new Date(),
        min: new Date(),
        max: new Date()
    },
    validate: function(attrs) {
        var beginTime = attrs.begin.getTime(),
            endTime = attrs.end.getTime(),
            minTime = attrs.min.getTime(),
            maxTime = attrs.max.getTime();

        if (minTime > maxTime) {
            return "wrong min/max"
        }
        else if (beginTime < minTime || beginTime > endTime) {
            return "wrong begin"
        }
        else if (endTime > maxTime) {
            return "wrong end"
        }
    },

    _getString: function(date) {
        return $.datepicker.formatDate('yy-mm-ddT', date)
            + date.getHours() + ":" + date.getMinutes() + "Z";
    },
    getBeginString: function() {
        return this._getString(this.get("begin"));
        
    },
    getEndString: function() {
        return this._getString(this.get("end"));
    }
});

models.BoundingBoxModel = Backbone.Model.extend({
    defaults: {
        isSet: false,
        values: [0, 0, 0, 0]
    },
    validate: function(attrs) {
        var values = attrs.values;
        if (values.length != 4) {
            return "wrong number of values";
        }
        else if (_.any(values, isNaN)) {
            return "values must be valid numbers";
        }
        else if (values[0] > values[2] || values[1] > values[3]) {
            return "wrong values"
        }
    }
});

models.BandSelectionModel = Backbone.Model.extend({
    defaults: {
        selected: true
    }
});

models.RangeTypeSelectionCollection = Backbone.Collection.extend({
    model: models.BandSelectionModel
});

/// ROUTER

var app = namespace("App");

app.Router = Backbone.Router.extend({
    initialize: function(options) {
        var caps = new WCS.Backbone.Model.Service({urlRoot: "/ows"});
        var router = this;
        $("#div-busy-indicator").fadeIn();
        caps.fetch({
            success: function() {
                $("#div-busy-indicator").fadeOut();
                router.dtModel = new models.DateTimeInterval({
                    min: options.minDate,
                    max: options.maxDate,
                    begin: options.minDate,
                    end: options.maxDate
                });
                router.bboxModel = new models.BoundingBoxModel({
                    values: options.extent
                });
                
                router.mapView = new views.MapView({
                    el: $("#div-map"),
                    dtModel: router.dtModel,
                    bboxModel: router.bboxModel,
                    layerParams: options.layerParams
                });

                router.controlView = new views.MainControlView({
                    el: $("#div-main"),
                    dtModel: router.dtModel,
                    bboxModel: router.bboxModel,
                    capsModel: caps,
                    router: router
                });

                router.mapView.render();
                router.controlView.render();

                router.eoid = options.eoid;
            },
            error: function() {
                alert("An error occurred!");
            }
        })
    },
    routes: {
        "": "main",
        "select?*kvp": "downloadSelection"
    },
    main: function() {
        //this.controlView.show();
    },
    downloadSelection: function(kvp) {
        var router = this;
        var options = {
            type: "coverages",
            urlRoot: "/ows",
            eoid: this.eoid
        };

        var kvps = parseKvp(Backbone.history.getFragment());
        if (kvps.bbox) {
            var values = kvps.bbox.split(",");
            if (values.length == 4)
                options.bbox =  values;
        }
        if (kvps.begin && kvps.end) {
            options.subsetTime = [kvps.begin, kvps.end];
        }
        
        var eoSet = new WCS.Backbone.Model.EOCoverageSet([], options);
        $("#div-busy-indicator").fadeIn();
        eoSet.fetch({
            success: function() {
                $("#div-busy-indicator").fadeOut();
                var downloadSelection = new views.DownloadSelectionView({
                    el: $("#div-download"),
                    model: eoSet,
                    router: router
                });
                downloadSelection.render();
            },
            error: function(error) {
                $("#div-busy-indicator").hide();
                alert("An error occurred!"); // TODO: improve error message
            }
        });
    }
});

/**
 *  function parseKvp
 *
 * really, really simple KVP-URL parsing function.
 */
var parseKvp = function(string) {
    var kvps = {};
    var mainParts = string.split("?");
    if (mainParts.length != 2) return {};
    var parts = mainParts[1].split("&");
    _.each(parts, function(part) {
        var keyValue = part.split("=");
        kvps[keyValue[0]] = keyValue[1];
    });
    return kvps;
};


});
