var StateModel = Backbone.Model.extend({
    defaults: {
        group_id: window.GROUP_ID || "",
        facility_id: window.FACILITY_ID || ""
    }
});

var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var FacilityCollection = Backbone.Collection.extend({
    url: FACILITY_RESOURCE_URL
});

var GroupCollection = Backbone.Collection.extend({
    url: GROUP_RESOURCE_URL
});

var CoachReportModel = Backbone.Model.extend({
    initialize: function(options) {
        this.facility = options.facility;
        this.group = options.group;
    },

    url: function() {
        return setGetParamDict(Urls.learner_logs(), {
            facility_id: this.facility,
            group_id: this.group
        });
    }
});

var CoachReportAggregateModel = Backbone.Model.extend({
    initialize: function(options) {
        this.facility = options.facility;
        this.group = options.group;
    },

    url: function() {
        return setGetParamDict(Urls.aggregate_learner_logs(), {
            facility_id: this.facility,
            group_id: this.group
        });
    }
});