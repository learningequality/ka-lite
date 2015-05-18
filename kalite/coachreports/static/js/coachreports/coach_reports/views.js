var CoachReportView = BaseView.extend({

    template: HB.template('coach_nav/reports-nav'),

    initialize: function(options) {

        this.facility_select_view = new FacilitySelectView({model: this.model});
        this.group_select_view = new GroupSelectView({model: this.model});

        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        this.$('#group-select-container').append(this.group_select_view.$el);
        this.$('#facility-select-container').append(this.facility_select_view.$el);
        this.tabular_view = new TabularReportView({model: this.model});
        this.$("#student_report_container").append(this.tabular_view.$el);
    }
})

var TabularReportView = BaseView.extend({

    template: HB.template("tabular_reports/tabular-view"),

    initialize: function() {
        _.bindAll(this);
        this.set_data_model();
        this.listenTo(this.model, "change", this.set_data_model);
    },

    render: function() {
        this.$el.html(this.template({
            learners: this.learners.toJSON(),
            contents: this.contents.toJSON()
        }));
    },

    set_data_model: function (){
        var self = this;
        this.data_model = new CoachReportModel({
            facility: this.model.get("facility"),
            group: this.model.get("group")
        });
        if (this.model.get("facility")) {
            this.data_model.fetch().then(function() {
                self.learners = new Backbone.Collection(self.data_model.get("learners"));
                self.contents = new Backbone.Collection(self.data_model.get("contents"));
                for (var i = 0; i < self.learners.length; i++) {
                    self.learners.models[i].set("logs", _.object(
                        _.map(_.filter(self.data_model.get("logs"), function(log) {
                            return log.user === self.learners.models[i].get("pk");
                        }), function(item) {
                            return [item.exercise_id || item.video_id || item.content_id, item];
                        })));
                }
                self.render();
            });
        }
    }

});

var FacilitySelectView = Backbone.View.extend({
    template: HB.template('coach_nav/facility-select'),

    initialize: function() {
        _.bindAll(this);
        this.facility_list = new FacilityCollection();
        this.facility_list.fetch();
        this.listenTo(this.facility_list, 'sync', this.render);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selected: this.model.get("facility")
        }));
        if (!this.model.get("facility")) {
            this.facility_changed();
        }
        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function() {
        this.model.set("facility", this.$(":selected").val());
    }
});

var GroupSelectView = Backbone.View.extend({
    template: HB.template('coach_nav/group-select'),

    initialize: function() {
        this.group_list = new GroupCollection();
        this.fetch_by_facility();
        this.listenTo(this.group_list, 'sync', this.render);
        this.listenTo(this.model, "change:facility", this.fetch_by_facility);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            groups: this.group_list.toJSON(),
            selected: this.model.get("group")
        }));
        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function() {
        this.model.set("group", this.$(":selected").val());
    },

    fetch_by_facility: function() {
        if (this.model.get("facility")) {
            // Get new facility ID and fetch
            this.group_list.fetch({
                data: $.param({
                    facility_id: this.model.get("facility"),
                    // TODO(cpauya): Find a better way to set the kwargs argument of the tastypie endpoint
                    // instead of using GET variables.  This will set it as False on the endpoint.
                    groups_only: ""
                })
            });
        }
    }
});
