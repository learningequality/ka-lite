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
});

var DetailPanelInlineRowView = BaseView.extend({

    tagName: 'tr',

    className: 'details-row',

    initialize: function(options) {
        this.contents_length = options.contents_length;
        this.content_item = options.content_item;
        this.render();
    },

    render: function() {
        this.detail_view = new detailsPanelView({
            tagName: 'td',
            model: this.model,
            content_item: this.content_item,
            attributes: {colspan: this.contents_length + 1}
        });
        this.$el.append(this.detail_view.el);
    }
})
        
var detailsPanelView = BaseView.extend({
    
    //Number of items to show from the collection
    limit: 4,
    
    template: HB.template("coach_nav/detailspanel"),
    
    initialize: function (options) {
        _.bindAll(this);
        this.content_item = options.content_item;
        if (this.content_item.get("kind") === "Exercise") {
            this.collection = new window.AttemptLogCollection([], {
                user: this.model.get("user"),
                limit: this.limit,
                exercise_id: this.model.get("exercise_id")
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
        this.bodyView = new detailsPanelBodyView ({
            collection: this.collection,
            el: this.$(".body")
        });
    }
});


var detailsPanelBodyView = BaseView.extend({
    
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

var TabularReportView = BaseView.extend({

    template: HB.template("tabular_reports/tabular-view"),

    initialize: function() {
        _.bindAll(this);
        this.set_data_model();
        this.listenTo(this.model, "change", this.set_data_model);
    },

    render: function() {
        this.$el.html(this.template({
            contents: this.contents.toJSON(),
            learners: this.contents.length
        }));
        var row_views = [];
        for (var i = 0; i < this.learners.length; i++) {
            var row_view = this.add_subview(TabularReportRowView, {model: this.learners.at(i), contents: this.contents})
            row_views.push(row_view);
            this.listenTo(row_view, "detail_view", this.set_detail_view);
        }
        this.append_views(row_views, ".student-data");
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

var TabularReportRowView = BaseView.extend({

    template: HB.template("tabular_reports/tabular-view-row"),

    tagName: 'tr',

    initialize: function(options) {
        _.bindAll(this);

        this.contents = options.contents;
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));

        var cell_views = [];
        for (var i = 0; i < this.contents.length; i++) {
            var data = this.model.get("logs")[this.contents.at(i).get("id")];
            var new_view = this.add_subview(TabularReportRowCellView, {model: new Backbone.Model(data)});
            cell_views.push(new_view);
            this.listenTo(new_view, "detail_view", this.show_detail_view);
        }
        this.append_views(cell_views);
    },

    show_detail_view: function(model) {
        if (this.detail_view) {
            // TODO (rtibbles): Implement Models properly here to reflect server side id attributes
            if (this.detail_view.model.cid === model.cid) {
                delete this.detail_view;
                this.trigger("detail_view");
                return false
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

var TabularReportRowCellView = BaseView.extend({

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

    title_attributes: {
        "not-attempted": gettext("Not Attempted"),
        "partial": gettext("Attempted"),
        "complete": gettext("Complete"),
        "struggling": gettext("Struggling")
    },

    attributes: function() {
        return {title: this.title_attributes[this.status_class()]};
    },

    initialize: function() {
        this.render();
    },

    render: function() {
        if (this.model.has("streak_progress")) {
            this.$el.html(this.model.get("streak_progress") + "%");
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
