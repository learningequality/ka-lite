var BaseView = require("base/baseview");
var _ = require("underscore");
var Backbone = require("base/backbone");
var Handlebars = require("base/handlebars");
var sprintf = require("sprintf-js").sprintf;

var ExerciseModels = require("exercises/models");
var Models = require("../coach_reports/models");

var date_string = require("utils/datestring").date_string;

/*
Hierarchy of views:
- TabularReportView:
    - TabularReportRowView:
        - TabularReportRowCellView
        - DetailPanelInlineRowView:
            - DetailPanelView:
                - DetailPanelBodyView
*/



var DetailPanelBodyView = BaseView.extend({
    /*
    This view displays details of individual attempt logs
    It has a tabbed body which will display all the questions it is passed.
    The number passed to it is determined in its wrapper view above.
    */

    template: require("./hbtemplates/detailspanelbody.handlebars"),

    initialize: function (options) {
        _.bindAll(this, "render");
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

var DetailPanelView = BaseView.extend({
    /*
    This view handles the pagination for the detail view
    */

    //Number of items to show from the collection
    limit: 4,

    id: "details-panel-view",

    template: require("./hbtemplates/detailspanel.handlebars"),

    events: {
        "click .pagination-link": "change_page"
    },

    initialize: function (options) {
        _.bindAll(this, "render");
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
        this.collection = new ExerciseModels.AttemptLogCollection([], {
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
        if (this.collection && this.collection.meta) {
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
            collection: this.collection ? this.collection.to_objects() : []
        }));
        if (this.collection) {
            this.bodyView = new DetailPanelBodyView ({
                collection: this.collection,
                // Question number of first question on this page
                start_number: (this.page - 1)*this.limit + 1,
                el: this.$(".body")
            });
        }
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
        this.detail_view = new DetailPanelView({
            tagName: 'td',
            model: this.model,
            content_item: this.content_item,
            attributes: {colspan: Math.min(this.contents_length - this.content_item_place, 6)}
        });

        // Add in a view that spans the columns up to the selected cell.
        this.left_spacer_view = new BaseView({
            tagName: 'td',
            attributes: {colspan: this.content_item_place + 1}
        });

        this.left_spacer_view.render();

        this.$el.append(this.left_spacer_view.el);
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

    template: require("./hbtemplates/tabular-view-row.handlebars"),

    tagName: 'tr',

    className: 'user-data-row',

    id: function() {
        return this.model.get("pk");
    },

    initialize: function(options) {
        _.bindAll(this, "show_detail_view");

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

    template: require("./hbtemplates/tabular-view.handlebars"),

    initialize: function(options) {
        _.bindAll(this, "set_data_model", "scroll_bottom", "scroll_top");
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

        this.$(".scroller").css("width", this.$("table").outerWidth());

        if(this.complete_callback) {
            this.complete_callback();
        }

        this.$("#displaygrid").scroll(this.scroll_bottom);

        this.$(".top-scroll").scroll(this.scroll_top);

    },

    scroll_bottom: function() {
        this.scroll(".top-scroll", "#displaygrid");
    },

    scroll_top: function() {
        this.scroll("#displaygrid", ".top-scroll");
    },

    scroll: function(set, from) {
        this.$(set).scrollLeft(this.$(from).scrollLeft());
    },

    no_user_error: function() {
        show_message("warning", "No learner accounts in this group have been created.");
    },

    set_data_model: function (){
        var self = this;
        this.data_model = new Models.CoachReportModel({
            facility: this.model.get("facility"),
            group: this.model.get("group"),
            start_date: date_string(this.model.get("start_date")),
            end_date: date_string(this.model.get("end_date")),
            topic_ids: this.model.get("topic_ids")
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

module.exports = {
    TabularReportView: TabularReportView,
    TabularReportRowView: TabularReportRowView,
    TabularReportRowCellView: TabularReportRowCellView,
    DetailPanelInlineRowView: DetailPanelInlineRowView,
    DetailPanelView: DetailPanelView,
    DetailPanelBodyView: DetailPanelBodyView
};
