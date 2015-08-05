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

var date_string = function(date) {
    if (date) {
        return date.getFullYear() + "/" + (date.getMonth() + 1) + "/" + date.getDate();
    }
};

var DetailsPanelBodyView = BaseView.extend({
    /*
    This view displays details of individual attempt logs
    It has a tabbed body which will display all the questions it is passed.
    The number passed to it is determined in its wrapper view above.
    */

    template: HB.template("coach_nav/detailspanelbody"),

    initialize: function (options) {
        _.bindAll(this);
        // Track the number of the first Question in this panel.
        this.start_number = options.start_number;
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            collection: this.collection.to_objects(),
            start_number: this.start_number
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

    events: {
        "click .pagination-link": "change_page"
    },

    initialize: function (options) {
        _.bindAll(this);
        this.content_item = options.content_item;
        this.page = 1;
        if (this.content_item.get("kind") === "Exercise") {
            this.instantiate_collection();
        } else {
            this.render();
        }
    },

    instantiate_collection: function() {
        // Instantiate a collection, with the right attributes to fetch just the AttemptLogs needed
        // for the currently requested page and no more.
        this.collection = new window.AttemptLogCollection([], {
            user: this.model.get("user"),
            limit: this.limit,
            offset: (this.page - 1)*this.limit,
            exercise_id: this.model.get("exercise_id"),
            order_by: "timestamp"
        });
        this.listenToOnce(this.collection, "sync", this.render);
        this.collection.fetch();
    },

    change_page: function(event) {
        var page = this.$(event.currentTarget).attr("value");
        switch (page) {
            case "next":
                this.page++;
                break;
            case "previous":
                this.page--;
                break;
            default:
                this.page = Number(page);
                break;
        }
        this.instantiate_collection();
        return false;
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
            page: this.page,
            collection: this.collection.to_objects()
        }));
        this.bodyView = new DetailsPanelBodyView ({
            collection: this.collection,
            // Question number of first question on this page
            start_number: (this.page - 1)*this.limit + 1,
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
        this.content_item_place = options.content_item_place;
        this.render();
    },

    render: function() {
        this.detail_view = new DetailsPanelView({
            tagName: 'td',
            model: this.model,
            content_item: this.content_item,
            attributes: {colspan: this.contents_length - this.content_item_place}
        });

        // Add in a view that spans the columns up to the selected cell.
        this.spacer_view = new BaseView({
            tagName: 'td',
            attributes: {colspan: this.content_item_place + 1}
        });

        this.spacer_view.render();

        this.$el.append(this.spacer_view.el);
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
        } else if (this.model.has("video_id") || this.model.has("content_id")) {
            // Calculate progress from points if not an exercise.
            if (this.model.get("points") < ds.distributed.points_per_video) {
                this.$el.html(Math.round(100*this.model.get("points")/ds.distributed.points_per_video) + "%");
            }
        }
    },

    show_detail_view: function() {
        if (_.isEmpty(this.model.attributes)) {
            return false;
        } else {
            this.listenToOnce(this.model, "selected", function() {
                this.$el.addClass("selected");
            });
            this.listenToOnce(this.model, "deselected", function() {
                this.$el.removeClass("selected");
            });
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
        var content_item = this.contents.find(function(item) {return item.get("id") === model_id;});
        this.detail_view = new DetailPanelInlineRowView({
            model: model,
            contents_length: this.contents.length,
            content_item: content_item,
            content_item_place: this.contents.indexOf(content_item)
        });
        this.$el.after(this.detail_view.el);

        this.trigger("detail_view", this.detail_view, model);

    }

});

var TabularReportView = BaseView.extend({
    /*
    This is the main control view for the Tabular Coach report
    */

    template: HB.template("tabular_reports/tabular-view"),

    initialize: function(options) {
        _.bindAll(this);
        this.complete_callback = options.complete;
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

        this.$('.headrowuser').css("min-width", this.$('.headrow.data').outerWidth());

        if(this.complete_callback) {
            this.complete_callback();
        }

    },

    no_user_error: function() {
        show_message("warning", "No learner accounts in this group have been created.");
    },

    set_data_model: function (){
        var self = this;
        this.data_model = new CoachReportModel({
            facility: this.model.get("facility"),
            group: this.model.get("group"),
            start_date: date_string(this.model.get("start_date")),
            end_date: date_string(this.model.get("end_date"))
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

    set_detail_view: function(detail_view, model) {
        if (this.detail_view) {
            this.detail_view.model.trigger("deselected");
            this.detail_view.remove();
        }
        if (detail_view) {
            model.trigger("selected");
            this.detail_view = detail_view;
        }
    }

});

var TimeSetView = BaseView.extend({
    template: HB.template("coach_nav/datepicker"),

    events: {
        "click .setrange": "set_range"
    },

    initialize: function () {
        var server_date_now = new Date(new Date().getTime() - window.statusModel.get("client_server_time_diff"));
        var default_start_date = new Date(server_date_now.getTime())
        default_start_date = new Date(default_start_date.setDate(default_start_date.getDate()-ds.coachreports.default_coach_report_day_range));

        this.model.set({
            "start_date": default_start_date,
            "end_date": server_date_now
        });
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            start_date: icu.getDateFormat("SHORT").format(this.model.get("start_date")),
            end_date: icu.getDateFormat("SHORT").format(this.model.get("end_date"))
        }));

        var format = icu.getDateFormatSymbols().order_short;

        format = format[0] + "/" + format[1] + "/" + format[2];

        format = format.toLowerCase().replace("y", "yy");

        this.datepicker = this.$('.date-range').each(function(){
            $(this).datepicker({
                format: format,
                endDate: "0d",
                todayBtn: "linked",
                todayHighlight: true
            });
        });
    },

    set_range: function() {
        this.model.set({
            start_date: this.$("#start").datepicker("getDate"),
            end_date: this.$("#end").datepicker("getDate")
        });
        this.model.trigger("set_time");
        return false;
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
        this.listenTo(this.model, "set_time", this.set_data_model);
        this.set_data_model();
    },

    set_data_model: function (){
        if (this.data_model) {
            var check_fields = ["facility", "group", "start_date", "end_date"];
            var data_fields = _.pick(this.data_model.attributes, check_fields);
            var status_fields = _.pick(this.model.attributes, check_fields);
            if (!_.isEqual(data_fields, status_fields)) {
                delete this.data_model;
            }
        }

        if (!this.data_model) {
            this.data_model = new CoachReportAggregateModel({
                facility: this.model.get("facility"),
                group: this.model.get("group"),
                start_date: date_string(this.model.get("start_date")),
                end_date: date_string(this.model.get("end_date"))
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
            data: this.data_model.attributes,
            start_date: icu.getDateFormat("SHORT").format(this.model.get("start_date")),
            end_date: icu.getDateFormat("SHORT").format(this.model.get("end_date"))
        }));

        clear_messages();

        // If no user data at all, then show a warning to the user
        var ref, ref1;

        if ((this.data_model != null ? this.data_model.get("learner_events") != null ? this.data_model.get("learner_events").length : void 0 : void 0) === 0) {
            show_message("warning", gettext("No recent learner data for this group is available."));
        }

        delete this.tabular_report_view;

    },

    toggle_tabular_view: _.debounce(function() {
        var self = this;
        if (!this.tabular_report_view) {
            this.$("#show_tabular_report").text("Loading");
            this.$("#show_tabular_report").attr("disabled", "disabled");
            this.tabular_report_view = new TabularReportView({model: this.model, complete: function() {
                self.$("#show_tabular_report").text(gettext("Hide Tabular Report"));
                self.$("#show_tabular_report").removeAttr("disabled");
            }});
            this.$("#detailed_report_view").append(this.tabular_report_view.el);
        } else {
            this.$("#show_tabular_report").text(gettext("Show Tabular Report"));
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

    template: HB.template('coach_nav/group-select'),

    initialize: function() {
        this.group_list = new GroupCollection();
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

    template: HB.template('coach_nav/reports-nav'),

    initialize: function(options) {

        this.facility_select_view = new FacilitySelectView({model: this.model});
        this.group_select_view = new GroupSelectView({model: this.model});
        this.coach_summary_view = new CoachSummaryView({model: this.model});
        this.time_set_view = new TimeSetView({model: this.model});

        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        this.$('#group-select-container').append(this.group_select_view.el);
        this.$('#facility-select-container').append(this.facility_select_view.el);
        this.$("#time-set-container").append(this.time_set_view.el);
        this.$("#student_report_container").append(this.coach_summary_view.el);
    }
});
