// Models
window.TopicNode = Backbone.Model.extend({
    url: ALL_TOPICS_URL
});

// Collections
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode
});

// Views

window.ContentAreaView = Backbone.View.extend({

    template: HB.template("distributed/content-area"),

    initialize: function() {

        _.bindAll(this);

        this.model = new Backbone.Model();

        this.render();

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    show_view: function(view) {

        // hide any messages being shown for the old view
        clear_messages();

        // close the currently shown view, if possible
        if (this.currently_shown_view && _.isFunction(this.currently_shown_view.close)) {
            this.currently_shown_view.close();
        }
        // set the new view as the current view
        this.currently_shown_view = view;
        // show the view
        this.$(".content").html("").append(view.$el);
    }

});

window.SidebarView = Backbone.View.extend({

    el: "#topic-container",

    template: HB.template("distributed/sidebar"),

    events: {
        "click .sidebar-tab": "toggle_sidebar"
    },

    initialize: function() {

        var self = this;

        _.bindAll(this);

        this.state_model = new Backbone.Model({
            open: false
        });

        this.render();

        this.listenTo(this.state_model, "change:open", this.update_sidebar_visibility);

        this.topic_node_view = new TopicContainerOuter();

        this.$('.sidebar-content').append(this.topic_node_view.el);
        this.listenTo(this.topic_node_view, "hideSidebar", this.hide_sidebar);

    },

    render: function() {
        var self = this;
        
        this.$el.html(this.template());

        this.sidebar = this.$('').bigSlide({
            menu: this.$(".panel"),
            // push: "#page-container, #footer, .sidebar-tab",
            push: ".sidebar-tab",
            menuWidth: "220px"
        });

        this.toggle_sidebar();

        return this;
    },

    toggle_sidebar: function(ev) {
        // this.$(".sidebar-tab").css("color", this.state_model.get("open") ? "red" : "blue")
        this.state_model.set("open", !this.state_model.get("open"));

        // TODO (rtibbles): Get render to only run after all listenTos have been bound and remove this.
        if (ev !== undefined) {
            ev.preventDefault();
        }
        return false;
    },

    update_sidebar_visibility: function() {
        if (this.state_model.get("open")) {
            this.sidebar.open();
        } else {
            this.sidebar.close();
        }
    },

    show_sidebar: function() {
        this.state_model.set("open", true);
    },

    hide_sidebar: function() {
        this.state_model.set("open", false);
    }

});

window.SidebarContentView = Backbone.View.extend({

    template: HB.template("distributed/sidebar-content"),

    events: {
        'click .back-to-parent' : 'backToParent'
    },

    initialize: function() {

        var self = this;

        _.bindAll(this);

        this._entry_views = [];

        this.has_parent = this.options.has_parent;

        if (!(this.model.get("children") instanceof TopicCollection)) {

            this.model.set("children", new TopicCollection(this.model.get("children")));
        }

        this.listenTo(this.model.get("children"), 'add', this.add_new_entry);
        this.listenTo(this.model.get("children"), 'reset', this.add_all_entries);

        this.add_all_entries();

        this.render();

    },

    render: function() {
        var self = this;

        this.$el.html(this.template(this.model.attributes));
        
        this._entry_views.forEach(function(entry_view) {
            self.$(".sidebar").append(entry_view.render().$el);
            self.listenTo(entry_view, "clicked", self.item_clicked);
        });

        this.$(".sidebar").slimScroll({
            height: "auto",
            color: "#033000",
            size: "8px",
            distance: "2px",
            disableFadeOut: true
        });

        // resize the scrollable part of sidebar to the page height
        $(window).resize(_.throttle(function() {
            var height = $(window).height() - self.$(".slimScrollDiv").position().top;
            self.$(".slimScrollDiv, .sidebar").height(height);
        }, 200));
        $(window).resize();

        if (this.has_parent){
            this.$(".back-to-parent").show();
        } else {
            this.$(".back-to-parent").hide();
        }
        return this;
    },

    add_new_entry: function(entry) {
        var view = new SidebarEntryView({model: entry});
        this._entry_views.push(view);
    },

    add_all_entries: function() {
        this.render();
        this.model.get("children").map(this.add_new_entry);
    },

    show: function() {
        this.$el.show();
    },

    hide: function() {
        this.$el.hide();
    },

    hide_sidebar: function() {
        this.trigger("hideSidebar");
    },

    backToParent: function(ev) {
        this.trigger('back_button_clicked', this.model);
    }

});

window.SidebarEntryView = Backbone.View.extend({

    tagName: "li",

    template: HB.template("distributed/sidebar-entry"),

    events: {
        "click": "clicked"
    },

    initialize: function() {

        _.bindAll(this);

        this.listenTo(this.model, "change:active", this.render);

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    clicked: function(ev) {
        ev.preventDefault();
        this.trigger("clicked", this);
        return false;
    },

});


window.TopicContainerOuter = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.inner_views = [];
        this.model =  new TopicNode();
        this.model.fetch().then(this.render);
        this.content_view = new ContentAreaView({
            el: "#content-area"
        });
    },

    render: function() {
        this.show_new_topic(this.model);
    },

    show_new_topic: function(node) {
        if(node.get("render_type")=="Tutorial"){
            ItemWrapper = PlaylistSidebarView;
        } else {
            ItemWrapper = TopicContainerInner;
        }
        var new_topic = new ItemWrapper({
            model: node,
            has_parent: this.inner_views.length >= 1
        });

        // Only hide after we have the first one!
        // if (this.inner_views.length > 0) {
        //     this.inner_views[0].$el.hide();
        // }
        // Only show back button for nodes that have parents
        if (this.inner_views.length === 0){
            new_topic.model.set("has_parent", false);
        } else if (this.inner_views.length >= 1) {
            this.inner_views[0].hide();
        }

        this.$el.append(new_topic.el);
        this.inner_views.unshift(new_topic);

        // Listeners
        if(node.get("render_type")=="Tutorial"){
            this.listenTo(new_topic, "entry_requested", this.entry_requested);
        } else {
            this.listenTo(new_topic, 'topic_node_clicked', this.show_new_topic);
        }
        this.listenTo(new_topic, 'back_button_clicked', this.back_to_parent);
        this.listenTo(new_topic, 'hideSidebar', this.hide_sidebar)
    },

    back_to_parent: function() {
        // Simply pop the first in the stack and show the next one
        this.inner_views[0].remove();
        this.inner_views.shift();
        this.inner_views[0].show();
    },

    entry_requested: function(entry) {
        switch(entry.get("kind")) {

            case "Exercise":
                var view = new ExercisePracticeView({
                    exercise_id: entry.get("id")
                });
                this.content_view.show_view(view);
                break;

            case "Video":
                var view = new VideoWrapperView({
                    video_id: entry.get("id")
                });
                this.content_view.show_view(view);
                break;

            case "Quiz":
                var view = new ExerciseQuizView({
                    quiz_model: new QuizDataModel({entry: entry})
                });
                this.content_view.show_view(view);
                break;
        }
    },

    hide_sidebar: function() {
        this.trigger("hideSidebar");
    }
});

window.PlaylistSidebarView = SidebarContentView.extend({

    item_clicked: function(view) {
        this.hide_sidebar();
        // only trigger an entry_requested event if the item wasn't already active
        if (!view.model.get("active")) {
            this.trigger("entry_requested", view.model);
        }
        // mark the clicked view as active, and unmark all the others
        _.each(this._entry_views, function(v) {
            v.model.set("active", v == view);
        });
    }
});

window.TopicContainerInner = SidebarContentView.extend({


    item_clicked: function(view) {
        this.trigger('topic_node_clicked', view.model);
    }

});