/*
Hierarchy of views:
CoachReportView:
    - FacilitySelectView
    - GroupSelectView
    - CoachSummaryView:
        - TabularReportView:
            - TabularReportRowView:
                - TabularReportRowCellView
                - DetailPanelInlineRowView:
                    - DetailPanelView:
                        - DetailPanelBodyView
*/

var DetailsPanelBodyView = BaseView.extend({
    /*
    This view displays details of individual attempt logs
    It has a tabbed body which will display all the questions it is passed.
    The number passed to it is determined in its wrapper view above.
    */

    template: HB.template("coach_nav/detailspanelbody"),

    initialize: function (options) {
        _.bindAll(this);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            collection: this.collection.to_objects()
        }));
    }
});

var DetailsPanelView = BaseView.extend({
    /*
    This view handles the pagination for the detail view
    */

    //Number of items to show from the collection
    limit: 4,

    id: "details-panel-view",

    template: HB.template("coach_nav/detailspanel"),

    initialize: function (options) {
        _.bindAll(this);
        this.content_item = options.content_item;
        if (this.content_item.get("kind") === "Exercise") {
            this.collection = new window.AttemptLogCollection([], {
                user: this.model.get("user"),
                limit: this.limit,
                exercise_id: this.model.get("exercise_id"),
                order_by: "timestamp"
            });
            this.collection.fetch();
        }
        this.listenToOnce(this.collection, "sync", this.render);
        this.render();
    },

    render: function() {
        var item_count = 0;
        if (this.collection.meta) {
            item_count = this.collection.meta.total_count;
        }
        this.pages = [];
        if (item_count/this.limit > 1) {
            for (var i=1; i < item_count/this.limit + 1; i++) {
                this.pages.push(i);
            }
        }
        this.$el.html(this.template({
            model: this.model.attributes,
            itemdata: this.content_item.attributes,
            pages: this.pages,
            collection: this.collection.to_objects()
        }));
        this.bodyView = new DetailsPanelBodyView ({
            collection: this.collection,
            el: this.$(".body")
        });
    }
});

var DetailPanelInlineRowView = BaseView.extend({
    /*
    This is a special view that lets the detail view fit in a new row in the tabular report table
    */

    tagName: 'tr',

    className: 'details-row',

    initialize: function(options) {
        this.contents_length = options.contents_length;
        this.content_item = options.content_item;
        this.render();
    },

    render: function() {
        this.detail_view = new DetailsPanelView({
            tagName: 'td',
            model: this.model,
            content_item: this.content_item,
            attributes: {colspan: this.contents_length + 1}
        });
        this.$el.append(this.detail_view.el);
    }
});

var TabularReportRowCellView = BaseView.extend({
    /*
    This renders the data for a particular exercise/learner combination - a single cell
    */

    tagName: 'td',

    events: {
        "click": "show_detail_view"
    },

    status_class: function() {
        var status_class = "partial";
        if (_.isEmpty(this.model.attributes)) {
            status_class = "not-attempted";
        } else if (this.model.get("complete")) {
            status_class = "complete";
        } else if (this.model.get("struggling")) {
            status_class = "struggling";
        }
        return status_class;
    },

    className: function() {
        return sprintf("status data %s", this.status_class());
    },

    attributes: function() {
        return {
            value: this.model.get("exercise_id") || this.model.get("video_id") || this.model.get("content_id"),
            title: this.title_attributes[this.status_class()]
        };
    },

    title_attributes: {
        "not-attempted": gettext("Not Attempted"),
        "partial": gettext("Attempted"),
        "complete": gettext("Complete"),
        "struggling": gettext("Struggling")
    },

    initialize: function() {
        _.bindAll(this);
        this.render();
    },

    render: function() {
        if (this.model.has("streak_progress")) {
            if (this.model.get("streak_progress") < 100) {
                this.$el.html(this.model.get("streak_progress") + "%");
            }
        }
    },

    show_detail_view: function() {
        if (_.isEmpty(this.model.attributes)) {
            return false;
        } else {
            this.trigger("detail_view", this.model);
        }
    }
});

var TabularReportRowView = BaseView.extend({
    /*
    This view renders a row of the table (i.e. all the data for one user)
    */

    template: HB.template("tabular_reports/tabular-view-row"),

    tagName: 'tr',

    className: 'user-data-row',

    id: function() {
        return this.model.get("pk");
    },

    initialize: function(options) {
        _.bindAll(this);

        this.contents = options.contents;
        this.render();
    },

    render: function() {
        var self = this;

        this.$el.html(this.template(this.model.attributes));

        var cell_views = [];
        this.contents.each(function(model){
            var data = self.model.get("logs")[model.get("id")];
            var new_view = self.add_subview(TabularReportRowCellView, {model: new Backbone.Model(data)});
            cell_views.push(new_view);
            self.listenTo(new_view, "detail_view", self.show_detail_view);
        });

        this.append_views(cell_views);
    },

    show_detail_view: function(model) {
        if (this.detail_view) {
            // TODO (rtibbles): Implement Models properly here to reflect server side id attributes
            if (this.detail_view.model.cid === model.cid) {
                delete this.detail_view;
                this.trigger("detail_view");
                return false;
            }
            this.detail_view.remove();
        }


        var model_id = model.get("exercise_id") || model.get("video_id") || model.get("content_id");
        this.detail_view = new DetailPanelInlineRowView({
            model: model,
            contents_length: this.contents.length,
            content_item: this.contents.find(function(item) {return item.get("id") === model_id;})
        });
        this.$el.after(this.detail_view.el);

        this.trigger("detail_view", this.detail_view);

    }

});

var TabularReportView = BaseView.extend({
    /*
    This is the main control view for the Tabular Coach report
    */

    template: HB.template("tabular_reports/tabular-view"),

    initialize: function() {
        _.bindAll(this);
        this.set_data_model();
        this.listenTo(this.model, "change", this.set_data_model);
    },

    render: function() {
        var self = this;

        this.$el.html(this.template({
            contents: this.contents.toJSON(),
            learners: this.contents.length
        }));

        var row_views = [];
        this.learners.each(function(model){
            var row_view = self.add_subview(TabularReportRowView, {model: model, contents: self.contents});
            row_views.push(row_view);
            self.listenTo(row_view, "detail_view", self.set_detail_view);
        });

        this.append_views(row_views, ".student-data");
    },

    no_user_error: function() {
        show_message("warning", "No learner accounts in this group have been created.");
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
                if (self.learners.length > 0) {
                    self.learners.each(function(model){
                        model.set("logs", _.object(
                            _.map(_.filter(self.data_model.get("logs"), function(log) {
                                return log.user === model.get("pk");
                            }), function(item) {
                                return [item.exercise_id || item.video_id || item.content_id, item];
                            })));
                    });
                    self.render();
                } else {
                    self.no_user_error();
                }
            });
        }
    },

    set_detail_view: function(detail_view) {
        if (this.detail_view) {
            this.detail_view.remove();
        }
        if (detail_view) {
            this.detail_view = detail_view;
        }
    }

});

var CoachSummaryView = BaseView.extend({
    /*
    This view displays summary stats for the currently selected facility (and optionally group)
    */

    template: HB.template("coach_nav/landing"),

    events: {
        "click #show_tabular_report": "toggle_tabular_view"
    },

    initialize: function() {
        _.bindAll(this);
        this.listenTo(this.model, "change:facility", this.set_data_model);
        this.listenTo(this.model, "change:group", this.set_data_model);
    },

    set_data_model: function (){
        if (this.data_model) {
            if (this.data_model.get("facility") !== this.model.get("facility") || this.data_model.get("group") !== this.model.get("group")) {
                delete this.data_model;
            }
        }

        if (!this.data_model) {
            this.data_model = new CoachReportAggregateModel({
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
        delete this.fetching;

        this.$el.html(this.template({
            status:this.model.attributes,
            data: this.data_model.attributes
        }));

        clear_messages();

        // If no user data at all, then show a warning to the user
        var ref, ref1;

        if ((this.data_model != null ? this.data_model.get("learner_events") != null ? this.data_model.get("learner_events").length : void 0 : void 0) === 0) {
          show_message("warning", "No recent learner data for this group is available.");
        }

        delete this.tabular_report_view;

    },

    toggle_tabular_view: _.debounce(function() {
        if (!this.tabular_report_view) {
            this.$("#show_tabular_report").text("Hide Tabular Report");
            this.tabular_report_view = new TabularReportView({model: this.model});
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

    template: HB.template('coach_nav/facility-select'),

    initialize: function() {
        _.bindAll(this);
        this.facility_list = new FacilityCollection();
        this.listenTo(this.facility_list, 'sync', this.render);
        this.facility_list.fetch();
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selected: this.model.get("facility")
        }));
        this.facility_changed();
        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function() {
        var id = this.$(":selected").val();
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

    template: HB.template('coach_nav/group-select'),

    initialize: function() {
        this.group_list = new GroupCollection();
        this.listenTo(this.group_list, 'sync', this.render);
        this.fetch_by_facility();
        this.listenTo(this.model, "change:facility", this.fetch_by_facility);
    },

    render: function() {
        var self = this;
        // Remove reference to groups from another facility
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

        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function() {
        var id = this.$(":selected").val();
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
                    facility_id: this.model.get("facility"),
                    // TODO(cpauya): Find a better way to set the kwargs argument of the tastypie endpoint
                    // instead of using GET variables.  This will set it as False on the endpoint.
                    groups_only: ""
                })
            });
        }
    }
});

var CoachReportView = BaseView.extend({
    /*
    This is the wrapper view for the coach reports
    */

    template: HB.template('coach_nav/reports-nav'),

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