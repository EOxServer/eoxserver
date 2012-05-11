/**
 *  module WCS.Backbone.Model
 *
 * Main Backbone integration for libcoverage.js. Provides means to access WCS
 * services in a MVC-style manner.
 *
 * Limitations:
 *  - as with the current state of the WCS standard, it is currently not easily
 *    possible to alter data hosted on a server via WCS-T functions. So these
 *    classes all provide a read access only.
 */

namespace("WCS.Backbone").Model = function() {
    var getValue = function(object, prop) {
        if (!(object && object[prop])) return null;
        return _.isFunction(object[prop]) ? object[prop]() : object[prop];
    };
    
    /**
     *  class XmlModel
     *
     * Utility class for Models that use XML to retrieve data.
     */
    
    var XmlModel = Backbone.Model.extend({
        initialize: function(attributes) {
            if (attributes.urlRoot) {
                this.urlRoot = attributes.urlRoot;
                delete attributes.urlRoot;
            }
        },
        fetch: function(options) {
            options || (options = {});
            options.dataType = "xml";
            Backbone.Model.prototype.fetch.call(this, options);
        }
    });

    /**
     *  class XmlModel
     *
     * Utility class for Collections that use XML to retrieve data.
     */

    var XmlCollection = Backbone.Collection.extend({
        fetch: function(options) {
            options || (options = {});
            options.dataType = "xml";
            Backbone.Collection.prototype.fetch.call(this, options);
        }
    });

    var classes = {};

    /**
     *  class WCS.Backbone.Service
     *
     * This class provides access to service meta-data and contents
     *
     * @method fetchAdvertisedCoverages: return a WCS.Backbone.CoverageSet of
     *                                   all advertised coverages.
     */
    
    classes.Service = XmlModel.extend({
        url: function() {
            return WCS.Core.KVP.getCapabilitiesURL(getValue(this, "urlRoot"));
        },
        parse: function(response) {
            return WCS.Core.Parse.parse(response);
        },
        fetchAdvertisedCoverages: function(options) {
            var contents = this.get("contents");
            var ids = [];
            if (contents)
                ids = _.pluck(contents.coverages, "coverageId");
                
            var cset = new CoverageSet([], {
                urlRoot: this.urlRoot,
                coverageIds: ids
            });
            cset.fetch(options);
            return cset;
        }
    });

    /**
     *  class WCS.Backbone.Coverage
     *
     * This class provides access to coverages
     *
     * @method getDownloadUrl: return a download URL for this coverage with
     *                         specified options
     */

    classes.Coverage = XmlModel.extend({
        idAttribute: "coverageId",
        
        url: function() {
            var url = getValue(this, 'urlRoot') || getValue(this.collection, 'url');
            if (this.id)
                return WCS.Core.KVP.describeCoverageURL(url, this.id);
            // TODO: raise Error?
        },
        parse: function(response) {
            if (_.has(response, "coverageId"))
                return response;
            return WCS.Core.Parse.parse(response).coverageDescriptions[0];
        },
        getRangeType: function() {
            return this.get("rangeType");
        },
        getDownloadUrl: function(options) {
            var url = getValue(this, 'urlRoot') || getValue(this.collection, 'urlRoot');
            return WCS.Core.KVP.getCoverageURL(url, this.id, options);
        }
    });

    classes.CoverageSet = XmlCollection.extend({
        model: classes.Coverage,
        initialize: function(models, options) {
            if (models.length == 0) {
                this._ids = options.coverageIds || [];
            }
            else {
                this._ids = _.pluck(models, id);
            }

            this.urlRoot = options.urlRoot || this.urlRoot;
        },
        url: function() {
            return WCS.Core.KVP.describeCoverageURL(this.urlRoot, this._ids);
        },
        parse: function(response){
            return WCS.Core.Parse.parse(response).coverageDescriptions;
        }
    });

    // Add EOCoverageSet to the classes, if EO extension is included
    if (namespace("WCS").EO) {
        classes.EOCoverageSet = XmlCollection.extend({
            initialize: function(models, options) {
                this.options = options || {};
                this.type = options.type || this.type;
                if(this.type) {
                    delete options.type;
                    if (this.type === "coverages")
                        this.model = classes.Coverage
                    else if (this.type === "datasetSeries")
                        this.model = classes.DatasetSeries
                }
                this.urlRoot = options.urlRoot || this.urlRoot;
                this.eoid = options.eoid || this.eoid;
            },
            url: function() {
                return WCS.EO.KVP.describeEOCoverageSetURL(
                    this.urlRoot, this.eoid, this.options
                );
            },
            parse: function(response){
                var result = WCS.Core.Parse.parse(response);
                this.coverageDescriptions = result.coverageDescriptions;
                this.datasetSeriesDescriptions = result.datasetSeriesDescriptions;
                switch(this.type) {
                    case "coverages": return result.coverageDescriptions;
                    case "datasetSeries": return result.datasetSeriesDescriptions;
                    default: return _.union(result.coverageDescriptions, result.datasetSeriesDescriptions);
                }
            }
        });
    }
    
    return classes;
} ();
