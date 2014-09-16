// Views

window.ContentAreaView = Backbone.View.extend({

    template: HB.template("topics/content-area"),

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
        if (this.currently_shown_view) {
            // try calling the close method if available, otherwise remove directly
            if (_.isFunction(this.currently_shown_view.close)) {
                this.currently_shown_view.close();
            } else {
                this.currently_shown_view.remove();
            }
        }
        // set the new view as the current view
        this.currently_shown_view = view;
        // show the view
        this.$(".content").html("").append(view.$el);
    }

});

window.SidebarView = Backbone.View.extend({

    el: "#sidebar-container",

    template: HB.template("topics/sidebar"),

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

        _.defer(function() {
            self.show_sidebar();
        });

        this.topic_node_view = new TopicContainerOuter({
            model: this.model,
            entity_key: this.options.entity_key,
            entity_collection: this.options.entity_collection
        });
        this.listenTo(this.topic_node_view, "hideSidebar", this.hide_sidebar);
        this.listenTo(this.topic_node_view, "showSidebar", this.show_sidebar);

        this.$('.sidebar-content').append(this.topic_node_view.el);

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
    },

    navigate_paths: function(paths) {
        this.topic_node_view.defer_navigate_paths(paths);
    }

});

window.SidebarContentView = Backbone.View.extend({

    template: HB.template("topics/sidebar-content"),

    events: {
        'click .back-to-parent' : 'backToParent'
    },

    initialize: function() {

        var self = this;

        _.bindAll(this);

        this.entity_key = this.options.entity_key;

        this.entity_collection = this.options.entity_collection;

        this._entry_views = [];

        this.has_parent = this.options.has_parent;

        if (!(this.model.get(this.entity_key) instanceof this.entity_collection)) {

            this.model.set(this.entity_key, new this.entity_collection(this.model.get(this.entity_key)));
        }

        this.listenTo(this.model.get(this.entity_key), 'add', this.add_new_entry);
        this.listenTo(this.model.get(this.entity_key), 'reset', this.add_all_entries);

        this.add_all_entries();

    },

    render: function() {
        var self = this;

        this.$el.html(this.template(this.model.attributes));
        
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
        this.$(".sidebar").append(view.render().$el);
        this.listenTo(view, "clicked", this.item_clicked);
        this.load_entry_progress();
    },

    add_all_entries: function() {
        this.render();
        this.model.get(this.entity_key).map(this.add_new_entry);
    },

    load_entry_progress: function() {

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

    show_sidebar: function() {
        this.trigger("showSidebar");
    },

    backToParent: function(ev) {
        this.trigger('back_button_clicked', this.model);
    },

    node_by_slug: function(slug) {
        // Convenience method to return a node by a passed in slug
        console.log(slug);
        return _.find(this.model.get(this.entity_key).models, function(model) {return model.get("slug")==slug;});
    }

});

window.SidebarEntryView = Backbone.View.extend({

    tagName: "li",

    template: HB.template("topics/sidebar-entry"),

    events: {
        "click": "clicked"
    },

    initialize: function() {

        _.bindAll(this);

        this.listenTo(this.model, "change:active", this.toggle_active);

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

    toggle_active: function() {
        this.$(".sidebar-entry").toggleClass("active-entry", this.model.get("active"));
    }

});


window.TopicContainerOuter = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.inner_views = [];
        this.model =  this.model || new TopicNode();
        this.model.fetch().then(this.render);
        this.content_view = new ContentAreaView({
            el: "#content-area"
        });
    },

    render: function() {
        this.show_new_topic(this.model);
    },

    show_new_topic: function(node) {

        var new_topic = this.add_new_topic_view(node);

        this.$el.append(new_topic.el);

        // Listeners
        if(node.get("render_type")=="Tutorial"||node.get("entries")){
            this.listenTo(new_topic, "entry_requested", this.entry_requested);
        } else {
            this.listenTo(new_topic, 'topic_node_clicked', this.show_new_topic);
        }
        this.listenTo(new_topic, 'back_button_clicked', this.back_to_parent);
        this.listenTo(new_topic, 'hideSidebar', this.hide_sidebar);
        this.listenTo(new_topic, 'showSidebar', this.show_sidebar);
    },

    add_new_topic_view: function(node) {
        if(node.get("render_type")=="Tutorial"||node.get("entries")){
            ItemWrapper = PlaylistSidebarView;
        } else {
            ItemWrapper = TopicContainerInner;
        }
        var data = {
            model: node,
            has_parent: this.inner_views.length >= 1,
            entity_key: this.options.entity_key,
            entity_collection: this.options.entity_collection
        };

        var new_topic = new ItemWrapper(data);

        if (this.inner_views.length === 0){
            new_topic.model.set("has_parent", false);
            this.inner_views.unshift(new_topic);
            this.trigger("inner_view_added");
        } else if (this.inner_views.length >= 1) {
            this.inner_views[0].hide();
            this.inner_views.unshift(new_topic);
        }

        return new_topic;
    },

    defer_navigate_paths: function(paths) {
        if (this.inner_views.length === 0){
            var self = this;
            this.listenToOnce(this, "inner_view_added", function() {self.navigate_paths(paths);});
        } else {
            this.navigate_paths(paths);
        }
    },

    navigate_paths: function(paths) {
        paths = _.reject(paths, function(slug) {return slug===null;});
        for (i=0; i < paths.length; i++) {
            var node = this.inner_views[0].node_by_slug(paths[i]);
            if (node!==undefined) {
                if (i == paths.length - 1) {
                    this.show_new_topic(node);
                } else {
                    this.add_new_topic_view(node);
                }
            }
        }
    },

    back_to_parent: function() {
        // Simply pop the first in the stack and show the next one
        this.inner_views[0].remove();
        this.inner_views.shift();
        this.inner_views[0].show();
    },

    entry_requested: function(entry) {
        var kind = entry.get("kind") || entry.get("entity_kind");
        var id = entry.get("id") || entry.get("entity_id");

        switch(kind) {

            case "Exercise":
                var view = new ExercisePracticeView({
                    exercise_id: id,
                    context_type: "playlist",
                    context_id: this.model.get("id")
                });
                this.content_view.show_view(view);
                break;

            case "Video":
                var view = new VideoWrapperView({
                    video_id: id
                });
                this.content_view.show_view(view);
                break;

            case "Quiz":
                var view = new ExerciseQuizView({
                    quiz_model: new QuizDataModel({entry: entry}),
                    context_id: this.model.get("id") // for now, just use the playlist ID as the quiz context_id
                });
                this.content_view.show_view(view);
                break;
        }
    },

    hide_sidebar: function() {
        this.trigger("hideSidebar");
    },

    show_sidebar: function() {
        this.trigger("showSidebar");
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
    },

    load_entry_progress: _.debounce(function() {

        var self = this;

        // load progress data for all videos
        var video_ids = $.map(this.$("[data-video-id]"), function(el) { return $(el).data("video-id"); });
        if (video_ids.length > 0) {
            doRequest(GET_VIDEO_LOGS_URL, video_ids)
                .success(function(data) {
                    $.each(data, function(ind, video) {
                        var newClass = video.complete ? "complete" : "partial";
                        self.$("[data-video-id='" + video.video_id + "']").removeClass("complete partial").addClass(newClass);
                    });
                });
        }

        // load progress data for all exercises
        var exercise_ids = $.map(this.$("[data-exercise-id]"), function(el) { return $(el).data("exercise-id"); });
        if (exercise_ids.length > 0) {
            doRequest(GET_EXERCISE_LOGS_URL, exercise_ids)
                .success(function(data) {
                    $.each(data, function(ind, exercise) {
                        var newClass = exercise.complete ? "complete" : "partial";
                        self.$("[data-exercise-id='" + exercise.exercise_id + "']").removeClass("complete partial").addClass(newClass);
                    });
                });
        }

        // load progress data for quiz; TODO(jamalex): since this is RESTful anyway, perhaps use a model here?
        var quiz_ids = $.map(this.$("[data-quiz-id]"), function(el) { return $(el).data("quiz-id"); });
        if (quiz_ids.length > 0) {
            // TODO(jamalex): for now, we just hardcode the quiz id as being the playlist id, since we don't have a good independent quiz id
            var quiz_id = this.model.get("id");
            doRequest("/api/playlists/quizlog/?user=" + statusModel.get("user_id") + "&quiz=" + quiz_id)
                .success(function(data) {
                    $.each(data.objects, function(ind, quiz) {
                        var newClass = quiz.complete ? "complete" : "partial";
                        // TODO(jamalex): see above; just assume we only have 1 quiz
                        self.$("[data-quiz-id]").removeClass("complete partial").addClass(newClass);
                    });
                });
        }




    }, 100),
});

window.TopicContainerInner = SidebarContentView.extend({

    item_clicked: function(view) {
        this.trigger('topic_node_clicked', view.model);
        window.router.add_slug(view.model.get("slug"));
    }

});