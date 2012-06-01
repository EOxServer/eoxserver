
namespace("WebClient").Application = (function() {

    var models = namespace("WebClient.Models");
    var views = namespace("WebClient.Views");

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

    /**
     *  router Router
     *
     * The main WebClient router.
     */

    var Router = Backbone.Router.extend({
        initialize: function(options) {
            this.options = options;
            this.owsUrl = options.owsUrl;
            this.eoid = options.eoid;

            this.dtModel = new models.DateTimeIntervalModel({
                min: options.minDate,
                max: options.maxDate,
                begin: options.minDate,
                end: options.maxDate
            });
            this.bboxModel = new models.BoundingBoxModel({
                values: options.extent
            });

            this.ajaxBegin();
            this.serviceModel = new WCS.Backbone.Model.Service({urlRoot: this.owsUrl});
            this.serviceModel.fetch({
                success: _.bind(this.onServiceFetchSuccess, this),
                error: _.bind(this.onAjaxError, this)
            })
        },
        routes: {
            "": "main",
            "select?*kvp": "downloadSelection"
        },
        main: function() {
            // TODO: anything to do?
        },
        downloadSelection: function(kvp) {
            var router = this;
            var options = {
                type: "coverages",
                urlRoot: this.owsUrl,
                eoid: this.eoid
            };

            var kvps = parseKvp(Backbone.history.getFragment());
            if (kvps.bbox) {
                var values = kvps.bbox.split(",");
                if (values.length == 4) {
                    options.bbox = values;
                }
            }
            if (kvps.begin && kvps.end) {
                options.subsetTime = [kvps.begin, kvps.end];
            }

            this.ajaxBegin();
            var eoSet = new WCS.Backbone.Model.EOCoverageSet([], options);
            eoSet.fetch({
                success: _.bind(this.onEoCoverageSetFetchSuccess, this),
                error: _.bind(this.onAjaxError, this)
            });
        },

        /**
         * Functions for displaying data retrieval.
         */

        ajaxBegin: function() {
            $("#div-busy-indicator").fadeIn();
        },

        ajaxEnd: function() {
            $("#div-busy-indicator").fadeOut();
        },

        /**
         * Callback function for a successful retrieval of the services
         * capabilities.
         */
        
        onServiceFetchSuccess: function(model) {
            this.ajaxEnd();
            
            this.mapView = new views.MapView({
                el: $("#div-map"),
                dtModel: this.dtModel,
                bboxModel: this.bboxModel,
                layerParams: this.options.layerParams
            });

            this.controlView = new views.MainControlView({
                el: $("#div-main"),
                dtModel: this.dtModel,
                bboxModel: this.bboxModel,
                capsModel: model
            });

            this.mapView.render();
            this.controlView.render();
        },

        /**
         * Callback function for a successful retrieval of an EOCoverageSet.
         */
        
        onEoCoverageSetFetchSuccess: function(collection) {
            this.ajaxEnd();

            if (collection.size() > 0) {
                var downloadSelection = new views.DownloadSelectionView({
                    el: $("#div-download"),
                    service: this.serviceModel,
                    model: collection,
                    bbox: collection.options.bbox,
                    owsUrl: this.owsUrl
                });
                downloadSelection.render();
            }
            else {
                alert("Your search did not match any coverages.");
                Backbone.history.navigate("", true);
            }
        },

        /**
         * Callback function for ajax errors. Tries to parse and show an
         * ows:ExceptionReport.
         */
        
        onAjaxError: function(model, response) {
            $("#div-busy-indicator").hide();
            var exceptionReport = WCS.Core.Parse.parse(response.responseXML);
            alert(
                "An Exception occurred. \n" +
                "Message: " + exceptionReport.text + " \n" +
                "Locator: " + exceptionReport.locator + "\n" +
                "Code: " + exceptionReport.code
            );
        }
    });

    /**
     *  function run
     *
     * Utility function to run the main application.
     */

    var run = function(options) {
        var app = new Router(options);
        Backbone.history.start();
    }

    return {
        Router: Router,
        run: run
    };

})();
