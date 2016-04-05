var Backbone = require("base/backbone");
var _ = require("underscore");
var setGetParamDict = require("utils/get_params").setGetParamDict;

var StateModel = Backbone.Model.extend({

    set: function(key, val, options) {
        if (key === "facility" || key.facility) {
            this.set({
                group: undefined,
                group_name: undefined
            });
        }
        if (key === "facility" || key.facility || key === "group" || key.group) {
            this.set({
                topic_ids: undefined
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

function normalizeEndDate(end_date) {
    // We want our date ranges to be inclusive, so send the day + 1
    // to the server in order to do this.
    var output;
    if (end_date) {
        output = new Date(end_date);
        output.setDate(output.getDate() + 1);
        output = output.getFullYear() + "/" + (output.getMonth() + 1) + "/" + output.getDate();
    }
    return output;
}

var CoachReportModel = Backbone.Model.extend({
    initialize: function(options) {
        this.facility = options.facility;
        this.group = options.group;
        this.start_date = options.start_date;
        this.end_date = options.end_date;
        this.topic_ids = options.topic_ids;
    },

    url: function() {
        return setGetParamDict(Urls.learner_logs(), {
            facility_id: this.facility,
            group_id: this.group,
            start_date: this.start_date,
            end_date: normalizeEndDate(this.end_date),
            topic_ids: this.topic_ids
        });
    }
});

var CoachReportAggregateModel = Backbone.Model.extend({
    initialize: function(options) {
        this.facility = options.facility;
        this.group = options.group;
        this.start_date = options.start_date;
        this.end_date = options.end_date;
        this.topic_ids = options.topic_ids;
    },

    url: function() {

        return setGetParamDict(Urls.aggregate_learner_logs(), {
            facility_id: this.facility,
            group_id: this.group,
            start_date: this.start_date,
            end_date: normalizeEndDate(this.end_date),
            topic_ids: this.topic_ids
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
};
