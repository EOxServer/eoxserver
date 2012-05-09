$(document).ready(function() {

var views = namespace("App.Views");
var models = namespace("App.Models");

views.MapView = Backbone.View.extend({
    initialize: function(options) {
        this.bboxModel = options.bboxModel;
        this.dtModel = options.dtModel;

        this.bboxModel.on("change", this.onBBoxChange, this);
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
                "done": function (bounds) {
                    //$("#btn_draw_bbox").trigger("click");
                    
                    var ll = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.left, bounds.bottom)); 
                    var ur = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top));
                    
                    //setBBOXValues([ll.lon, ll.lat, ur.lon, ur.lat], true); // TODO:
                }
            })
        });

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
                wms_layer
            ]
        };

        this.map = new OpenLayers.Map(this.el, map_params);

        this.map.zoomToExtent(new OpenLayers.Bounds.fromArray(this.bboxModel.get("values")));
    },

    /// event handler here

    onBBoxChange: function() {
        if (this.bboxModel.get("isSet")) {
            // TODO: (re-)draw the bbox
        }
    },
    onDateTimeChange: function() {
        
    }
});

views.MainControlView = Backbone.View.extend({
    template: _.template($('#tpl-main-control').html()),
    initialize: function(options) {
        this.dtModel = options.dtModel;
        this.bboxModel = options.bboxModel;

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
        
        this.helpView = new views.HelpView();

        this.views = [
            this.dateSliderView,
            this.dtSelectionView,
            this.bboxSelectionView,
            this.helpView
        ];
    },
    events: {
        "click #btn-download": function() {alert("Download clicked");}
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
            width: 500,
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
        this.helpView.setElement(this.$("#frg-help"));

        _.each(this.views, function(view) { view.render(); });
    },
    show: function() {}, // TODO
    hide: function() {},
});

views.DateSliderView = Backbone.View.extend({
    initialize: function(options) {
        // bind events to member function
        this.model.on("change:begin change:end", this.onDateChange, this);
    },
    events: {
        "slide": "onSlide",
        "slidestop": "onSlideStop",
        "mousedown .ui-slider-handle": function() {}, // TODO: show tooltip
        "mouseup .ui-slider-handle": function() {}, // TODO: hide tooltip
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

        // TODO: setup tooltip
    },

    /// event handlers

    onSlide: function(event, ui) {
        var begin = new Date(ui.values[0]);
        var end = new Date(ui.values[1]);
        // TODO: set tooltip
    },
    onSlideStop: function(event, ui) {
        this.model.set({
            begin: new Date(ui.values[0]),
            end: new Date(ui.values[1])
        });
    },
    onDateChange: function() {
        // don't rerender here, just set the values
        this.$el.slider(
            "option", "values",
            [this.model.get("begin"), this.model.get("end")]
        );
        // TODO: set the values on the tooltip also
    }
});

views.DateTimeSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-datetime-selection').html()),
    initialize: function(options) {
        // bind events to member function
        this.model.on("change", this.onDateTimeChange, this);
    },
    events: {
        //"#begin_date #end_date": "" // TODO
    },
    render: function() {
        this.$el.html(this.template(this.model.toJSON()));

        var minDate = this.model.get("min"),
            maxDate = this.model.get("max"),
            beginDate = this.model.get("begin"),
            endDate = this.model.get("end");
        
        this.$("#begin_date #end_date").datepicker({
            showOn: 'focus',
            minDate: minDate,
            maxDate: maxDate,
            dateFormat: 'yy-mm-dd',
            onClose: function(dateText, inst) {
                // TODO: parse dates and set them to the datetime model

                

                
                var begin = $.datepicker.parseDate("yy-mm-dd", dateText);
                var end = $(this).datepicker("option", "maxDate");
                $.event.trigger(
                    'datetime_changed',
                    [begin, end]
                );
            }
        });
        this.$("#begin_date").datepicker("setDate", beginDate);
        this.$("#end_date").datepicker("setDate", endDate);
    },
    onDateTimeChange: function() {
        var model = this.model;
        if (model.hasChanged("begin")) {
            this.$("#begin_date").datepicker("setDate", model.get("begin"));
        }
        if (model.hasChanged("end")) {
            this.$("#end_date").datepicker("setDate", model.get("end"));
        }
        // TODO: min/max
    }
});

views.BoundingBoxSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-bbox-selection').html()),
    initialize: function(options) {
        // bind events to member function
        this.model.on("change", this.onBBoxChange, this);
    },
    events: {
        "change #minx,#miny,#maxx,#maxy": "onBBoxInput"
    },
    render: function() {
        this.$el.html(this.template());
    },
    onBBoxInput: function() {
        var values = this.$("#minx,#miny,#maxx,#maxy").map(function(){
            return parseFloat($(this).val());
        }).get();
        
        if(!_.any(values, isNaN)) {
            this.model.set({
                values: values,
                isSet: true
            });
        }
    },
    onBBoxChange: function() {
        if (this.model.get("isSet")) {
            var $inputs = this.$("#minx,#miny,#maxx,#maxy");
            
            _.each(this.model.get("values"), function(v, i) {
                $($inputs[i]).val(v);
            });
        }
    }
});

views.HelpView = Backbone.View.extend({
    template: _.template($('#tpl-help').html()),
    render: function() {
        this.$el.html(this.template());
    }
});

views.DownloadSelectionView = Backbone.View.extend({
    template: _.template($('#tpl-bbox-selection').html()),
    events: {
        "click download": "", // TODO
        "click cancel": ""
    },
    render: function() {
        
    }
});

views.DownloadSelectionItemView = Backbone.View.extend({
    
});

views.CoverageDetailView = Backbone.View.extend({
    
});


/// MODELS

models.DateTimeInterval = Backbone.Model.extend({
    defaults: {
        begin: new Date(),
        end: new Date(),
        min: new Date(),
        max: new Date()
    }
});

models.BoundingBoxModel = Backbone.Model.extend({
    defaults: {
        isSet: false,
        values: [0, 0, 0, 0]
    }
});

/// ROUTER

var app = namespace("App");

app.Router = Backbone.Router.extend({
    initialize: function(options) {
        this.dtModel = new models.DateTimeInterval({
            min: options.minDate,
            max: options.maxDate,
            begin: options.minDate,
            end: options.maxDate
        });
        this.bboxModel = new models.BoundingBoxModel({
            values: options.extent
        });
        
        this.mapView = new views.MapView({
            el: $("#div-map"),
            dtModel: this.dtModel,
            bboxModel: this.bboxModel
        });

        this.controlView = new views.MainControlView({
            el: $("#div-main"),
            dtModel: this.dtModel,
            bboxModel: this.bboxModel
        });

        this.mapView.render();
        this.controlView.render();
    },
    routes: {
        "": "main",
        "/select": "downloadSelection"
    },
    main: function() {
        this.controlView.show();
    },
    downloadSelection: function() { // TODO: parameters
        var eoSet = new WCS.Backbone.Model.EOCoverageSet([], {
            type: "coverages",
            // TODO fill in parameters
        });
        eoSet.fetch({async: false});
        
        var downloadSelection = new DownloadSelectionView({
            el: $("#div-download"),
            model: eoSet
        });
        downloadSelection.render();
    }
});


});
