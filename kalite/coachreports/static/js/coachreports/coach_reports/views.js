var BaseView = require("base/baseview");
var _ = require("underscore");
var $ = require("base/jQuery");
var Backbone = require("base/backbone");

var messages = require("utils/messages");
var Models = require("./models");
var TabularReportViews = require("../tabular_reports/views");

/*
Hierarchy of views:
CoachReportView:
    - FacilitySelectView
    - GroupSelectView
    - CoachSummaryView
*/

var CoachSummaryView = BaseView.extend({
    /*
    This view displays summary stats for the currently selected facility (and optionally group)
    */

    template: require("./hbtemplates/landing.handlebars"),

    events: {
        "click #show_tabular_report": "toggle_tabular_view"
    },

    initialize: function() {
        _.bindAll(this, "set_data_model", "render");
        this.listenTo(this.model, "change:facility", this.set_data_model);
        this.listenTo(this.model, "change:group", this.set_data_model);
        this.set_data_model();
    },

    set_data_model: function (){
        if (this.data_model) {
            if (this.data_model.get("facility") !== this.model.get("facility") || this.data_model.get("group") !== this.model.get("group")) {
                delete this.data_model;
            }
        }

        if (!this.data_model) {
            this.data_model = new Models.CoachReportAggregateModel({
                facility: this.model.get("facility"),
                group: this.model.get("group")
            });
            if (this.model.get("facility")) {
                this.listenTo(this.data_model, "sync", this.render);
                this.data_model.fetch();
            }
        }
    },

    render: function() {
        this.$el.html(this.template({
            status:this.model.attributes,
            data: this.data_model.attributes
        }));

        messages.clear_messages();

        // If no user data at all, then show a warning to the user
        var ref, ref1;

        if ((this.data_model != null ? this.data_model.get("learner_events") != null ? this.data_model.get("learner_events").length : void 0 : void 0) === 0) {
          messages.show_message("warning", "No recent learner data for this group is available.");
        }

        delete this.tabular_report_view;

    },

    toggle_tabular_view: _.debounce(function() {
        var self = this;
        if (!this.tabular_report_view) {
            this.$("#show_tabular_report").text("Loading");
            this.$("#show_tabular_report").attr("disabled", "disabled");
            this.tabular_report_view = new TabularReportViews.TabularReportView({model: this.model, complete: function() {
                self.$("#show_tabular_report").text("Hide Tabular Report");
                self.$("#show_tabular_report").removeAttr("disabled");
            }});
            this.$("#detailed_report_view").append(this.tabular_report_view.el);
        } else {
            this.$("#show_tabular_report").text("Show Tabular Report");
            this.tabular_report_view.remove();
            delete this.tabular_report_view;
        }
    }, 100)

});

var FacilitySelectView = Backbone.View.extend({
    /*
    This fetches data for facilities and displays them in a drop down
    */

    template: require("./hbtemplates/facility-select.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
        this.facility_list = new Models.FacilityCollection();
        this.listenTo(this.facility_list, 'sync', this.render);
        this.facility_list.fetch();
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selected: this.model.get("facility")
        }));
        var id = this.model.get("facility");
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        this.model.set({
            "facility_name": this.facility_list.find(function(model){ return model.get("id") === id;}).get("name")
        });
        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function() {
        var id = this.$(":selected").val();
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        this.model.set({
            "facility": id,
            "facility_name": this.facility_list.find(function(model){ return model.get("id") === id;}).get("name")
        });
    }
});

var GroupSelectView = Backbone.View.extend({
    /*
    This fetches group data for facilities and displays them in a drop down
    */

    template: require("./hbtemplates/group-select.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
        this.group_list = new Models.GroupCollection();
        this.listenTo(this.group_list, 'sync', this.render);
        this.fetch_by_facility();
        this.listenTo(this.model, "change:facility", this.fetch_by_facility);
    },

    render: function() {
        var self = this;

        // Add in 'All' and 'Ungrouped' groups if appropriate
        // Might be better to add in to the parse method of the collection
        if (this.group_list.length > 0) {
            this.group_list.add({
                id: "",
                name: gettext("All")
            }, {at: 0, silent: true});
            this.group_list.add({
                id: "Ungrouped",
                name: gettext("Ungrouped")
            }, {silent: true});
        }

        // Remove reference to groups from another facility
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        if (!this.group_list.some(function(model){ return model.get("id") === self.model.get("group");})) {
            this.model.set({
                "group": undefined,
                "group_name": undefined
            }, {silent: true});
        }

        this.$el.html(this.template({
            groups: this.group_list.toJSON(),
            selected: this.model.get("group")
        }));

        var id = this.model.get("group");
        var output, ref;
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        output = (ref = this.group_list.find(function(model) {
          return model.get("id") === id;
        })) != null ? ref.get("name") : void 0;

        if (output) {
            this.model.set({
                "group_name": output
            });
        }

        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function() {
        var id = this.$(":selected").val();
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        this.model.set({
            "group": id,
            "group_name": this.group_list.find(function(model){ return model.get("id") === id;}).get("name")
        });
    },

    fetch_by_facility: function() {
        if (this.model.get("facility")) {
            // Get new facility ID and fetch
            this.group_list.fetch({
                data: $.param({
                    facility_id: this.model.get("facility")
                })
            });
        }
    }
});

var CoachReportView = BaseView.extend({
    /*
    This is the wrapper view for the coach reports
    */

    template: require("./hbtemplates/reports-nav.handlebars"),

    initialize: function(options) {

        this.facility_select_view = new FacilitySelectView({model: this.model});
        this.group_select_view = new GroupSelectView({model: this.model});
        this.coach_summary_view = new CoachSummaryView({model: this.model});

        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        this.$('#group-select-container').append(this.group_select_view.el);
        this.$('#facility-select-container').append(this.facility_select_view.el);
        this.$("#student_report_container").append(this.coach_summary_view.el);
    }
});

module.exports = {
    CoachReportView: CoachReportView,
    CoachSummaryView: CoachSummaryView,
    FacilitySelectView: FacilitySelectView,
    GroupSelectView: GroupSelectView
}
