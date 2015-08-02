var Backbone = require("base/backbone");
var StateModel = require("./models").StateModel;
var CoachReportView = require("./views").CoachReportView;
var _ = require("underscore");


module.exports = Backbone.Router.extend({
    initialize: function(options) {
        _.bindAll(this, "set_url");
        this.state_model = new StateModel();
        this.listenTo(this.state_model, "change", this.set_url);
        if (options.facility) {
            this.facility = options.facility;
        }
    },

    routes: {
        "(:facility/)(:group/)(:report/)":    "report"
    },

    report: function(facility, group, report) {
        if (!facility) {
            facility = this.facility;
        }
        this.state_model.set({
            facility: facility,
            group: group,
            report: report
        });
        if (!this.home_view) {
            this.home_view = new CoachReportView({
                model: this.state_model,
                el: "#coachreport_container"
            });
        }
    },

    set_url: function(model) {
        var url = "";
        if (this.state_model.get("facility")) {
            url += this.state_model.get("facility") + "/";
            if (this.state_model.get("group")) {
                url += this.state_model.get("group") + "/";
                if (this.state_model.get("report")) {
                    url += this.state_model.get("report") + "/";
                }
            }
        }
        this.navigate(url, {trigger: false, replace: true});
    }
});