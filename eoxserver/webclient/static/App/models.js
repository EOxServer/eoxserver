
namespace("WebClient").Models = (function() {

    /**
     *  model DateTimeIntervalModel
     *
     * Model for date/time intevals, containing of a minumum and maximum and
     * the current begin/end datetime. Min/max are the outer bounds for the
     * mutable begin/end datetime valies.
     */

    var DateTimeIntervalModel = Backbone.Model.extend({
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
                + util.zpad(date.getHours(), 2) + ":" + util.zpad(date.getMinutes(), 2) + "Z";
        },
        getBeginString: function() {
            return this._getString(this.get("begin"));
        },
        getEndString: function() {
            return this._getString(this.get("end"));
        }
    });

    /**
     *  model BoundingBoxModel
     *
     * Model for encapsuling a selected bounding box of the following form
     * [minx, miny, maxx, maxy]. Also the currently viewed extent is saved.
     */
    
    var BoundingBoxModel = Backbone.Model.extend({
        defaults: {
            isSet: false,
            values: [0, 0, 0, 0],
            viewExtent: [0, 0, 0, 0]
        },
        validate: function(attrs) {
            var values = attrs.values;
            var viewExtent = attrs.viewExtent;
            
            if (values.length != 4) {
                return "wrong number of values";
            }
            else if (_.any(values, isNaN)) {
                return "values must be valid numbers";
            }
            else if (values[0] > values[2] || values[1] > values[3]) {
                return "wrong values"
            }

            if (viewExtent.length != 4) {
                return "wrong number of values";
            }
            else if (_.any(viewExtent, isNaN)) {
                return "values must be valid numbers";
            }
            else if (viewExtent[0] > viewExtent[2] || viewExtent[1] > viewExtent[3]) {
                return "wrong values"
            }
        }
    });

    /**
     *  model BandSelectionModel
     *
     * A model for a band selection.
     */

    var BandSelectionModel = Backbone.Model.extend({
        defaults: {
            selected: true
        }
    });

    /**
     *  collection RangeTypeSelectionCollection
     *
     * A collection of BandSelectionModels. In conjunction it represents the
     * range subset.
     */

    var RangeTypeSelectionCollection = Backbone.Collection.extend({
        model: BandSelectionModel
    });

    return {
        DateTimeIntervalModel: DateTimeIntervalModel,
        BoundingBoxModel: BoundingBoxModel,
        BandSelectionModel: BandSelectionModel,
        RangeTypeSelectionCollection: RangeTypeSelectionCollection
    }

})();
