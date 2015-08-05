var Backbone = require("base/backbone");
var _ = require("underscore");
var setGetParamDict = require("utils/get_params").setGetParamDict

var StateModel = Backbone.Model.extend({

    set: function(key, val, options) {
        if (key === "facility" || key.facility) {
            this.set({
                group: undefined,
                group_name: undefined
            });
        }

        Backbone.Model.prototype.set.call(this, key, val, options);
    }
});

var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var FacilityCollection = Backbone.Collection.extend({
    url: window.FACILITY_RESOURCE_URL
});

var GroupCollection = Backbone.Collection.extend({
    url: window.GROUP_RESOURCE_URL
});

var CoachReportModel = Backbone.Model.extend({
    initialize: function(options) {
        this.facility = options.facility;
        this.group = options.group;
        this.start_date = options.start_date;
        this.end_date = options.end_date;
    },

    url: function() {
        return setGetParamDict(Urls.learner_logs(), {
            facility_id: this.facility,
            group_id: this.group,
            start_date: this.start_date,
            end_date: this.end_date
        });
    }
});

var CoachReportAggregateModel = Backbone.Model.extend({
    initialize: function(options) {
        this.facility = options.facility;
        this.group = options.group;
        this.start_date = options.start_date;
        this.end_date = options.end_date;
    },

    url: function() {
        return setGetParamDict(Urls.aggregate_learner_logs(), {
            facility_id: this.facility,
            group_id: this.group,
            start_date: this.start_date,
            end_date: this.end_date
        });
    }
});

module.exports = {
    StateModel: StateModel,
    FacilityModel: FacilityModel,
    GroupModel: GroupModel,
    FacilityCollection: FacilityCollection,
    GroupCollection: GroupCollection,
    CoachReportModel: CoachReportModel,
    CoachReportAggregateModel: CoachReportAggregateModel
}
