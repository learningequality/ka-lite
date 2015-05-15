// Views

window.ContentAreaView = BaseView.extend({

    template: HB.template("topics/content-area"),

    initialize: function() {
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

        this.close();
        // set the new view as the current view
        this.currently_shown_view = view;
        // show the view
        this.$(".content").html("").append(view.$el);
    },

    close: function() {
        // This does not actually close this view. If you *really* want to get rid of this view,
        // you should call .remove()!
        // This is to allow the child view currently_shown_view to act consistently with other
        // inner_views for the sidebar InnerTopicsView.
        if (this.currently_shown_view) {
            // try calling the close method if available, otherwise remove directly
            if (_.isFunction(this.currently_shown_view.close)) {
                this.currently_shown_view.close();
            } else {
                this.currently_shown_view.remove();
            }
        }

        this.model.set("active", false);
    }

});

window.SidebarView = BaseView.extend({
    el: "#sidebar-container",
    template: HB.template("topics/sidebar"),

    events: {
        "click .sidebar-tab": "toggle_sidebar",
        "click .sidebar-fade": "check_external_click",
        "click .sidebar-back": "sidebar_back_one_level"
    },

    initialize: function(options) {
        var self = this;
        var navbarCollapsed = true;

        // Fancy algorithm to run a resize sidebar when window width 
        // changes significantly (100px steps) to avoid unnecessary computation
        var windowWidth = $(window).width();
        $(window).on("resize", function() {
            newWindowWidth = $(window).width();
            if (Math.floor(newWindowWidth/100) != Math.floor(windowWidth/100)) {
                self.resize_sidebar();
                windowWidth = $(window).width();
            }

            if ($(window).width() > 768) {
                self.show_sidebar_tab();
            }

            else {
                if (navbarCollapsed) {
                    self.show_sidebar_tab();
                }
                else {
                    self.hide_sidebar_tab();   
                }
            }
        });

        $(".navbar-collapse").on("show.bs.collapse", function() {
            self.hide_sidebar_tab();
            navbarCollapsed = false;
        }).on("hide.bs.collapse", function() {
            self.show_sidebar_tab();
            navbarCollapsed = true;
        });

        this.entity_key = options.entity_key;
        this.entity_collection = options.entity_collection;

        this.channel = options.channel;

        this.state_model = new Backbone.Model({
            open: false,
            current_level: 0
        });

        this.render();

        this.listenTo(this.state_model, "change:open", this.update_sidebar_visibility);
        this.listenTo(this.state_model, "change:current_level", this.resize_sidebar);
    },

    render: function() {
        var self = this;

        this.$el.html(this.template());

        this.sidebar = this.$(".sidebar-panel");
        this.sidebarTab = this.$(".sidebar-tab");
        this.sidebarBack = this.$(".sidebar-back");

        _.defer(function() {
            self.show_sidebar();
        });

        this.topic_node_view = new TopicContainerOuterView({
            channel: this.channel,
            model: this.model,
            entity_key: this.entity_key,
            entity_collection: this.entity_collection,
            state_model: this.state_model
        });
        this.listenTo(this.topic_node_view, "hideSidebar", this.hide_sidebar);
        this.listenTo(this.topic_node_view, "showSidebar", this.show_sidebar);

        this.$('.sidebar-content').append(this.topic_node_view.el);

        this.set_sidebar_back();

        return this;
    },

    resize_sidebar: function() {
        if (this.state_model.get("open")) {
            if ($(window).width() < 1260) {
                this.resize_for_narrow();
            } else {
                this.resize_for_wide();
            }
        }
    },

    resize_for_narrow: _.debounce(function() {
        var current_level = this.state_model.get("current_level");
        var column_width = this.$(".topic-container-inner").width();
        var last_column_width = this.$(".topic-container-inner:last-child").width();
        // Hack to give the last child of .topic-container-inner to be 1.5 times the 
        // width of their parents. Also, sidebar overflow out of the left side of screen
        // is computed and set here.

        // THE magic variable that controls number of visible panels
        var numOfPanelsToShow = 4;

        if ($(window).width() < 1120)
            numOfPanelsToShow = 3;

        if ($(window).width() < 920)
            numOfPanelsToShow = 2;

        if ($(window).width() < 620)
            numOfPanelsToShow = 1;

        // Used to get left value in number form
        var sidebarPanelPosition = this.sidebar.position();
        var sidebarPanelLeft = sidebarPanelPosition.left;

        this.width = (current_level - 1) * column_width + last_column_width + 10;
        this.sidebar.width(this.width);
        var sidebarPanelNewLeft = -(column_width * (current_level - numOfPanelsToShow)) + this.sidebarBack.width();
        if (sidebarPanelNewLeft > 0) sidebarPanelNewLeft = 0;

        // Signature color flash (also hides a slight UI glitch)
        var originalBackColor = this.sidebarBack.css('background-color');
        this.sidebarBack.css('background-color', this.sidebarTab.css('background-color')).animate({'background-color': originalBackColor});
        
        var self = this;
        this.sidebar.animate({"left": sidebarPanelNewLeft}, 115, function() {
            self.set_sidebar_back();
        });

        this.sidebarTab.animate({left: this.sidebar.width() + sidebarPanelNewLeft}, 115);
    }, 100),

    // Pretty much the code for pre-back-button sidebar resize
    resize_for_wide: _.debounce(function() {
        var current_level = this.state_model.get("current_level");
        var column_width = this.$(".topic-container-inner").width();
        var last_column_width = 400;
        
        this.width = (current_level-1) * column_width + last_column_width + 10;
        this.sidebar.width(this.width);
        this.sidebar.css({left: 0});
        this.sidebarTab.css({left: this.width});
        
        this.set_sidebar_back();
    }, 100),

    check_external_click: function(ev) {
        if (this.state_model.get("open")) {
            this.state_model.set("open", false);
        }
    },

    toggle_sidebar: function(ev) {
        this.state_model.set("open", !this.state_model.get("open"));

        // TODO (rtibbles): Get render to only run after all listenTos have been bound and remove this.
        if (ev !== undefined) {
            ev.preventDefault();
        }
        return false;
    },

    update_sidebar_visibility: _.debounce(function() {
        if (this.state_model.get("open")) {
            // Used to get left value in number form
            var sidebarPanelPosition = this.sidebar.position();
            this.sidebar.css({left: 0});
            this.resize_sidebar();
            this.sidebarTab.css({left: this.sidebar.width() + sidebarPanelPosition.left}).html('<span class="icon-circle-left"></span>');
            this.$(".sidebar-fade").show();
        } else {
            this.sidebar.css({left: - this.width});
            this.sidebarTab.css({left: 0}).html('<span class="icon-circle-right"></span>');
            this.$(".sidebar-fade").hide();
        }

        this.set_sidebar_back();
    }, 100),

    set_sidebar_back: function() {
        if (!this.state_model.get("open")) {
            this.sidebarBack.offset({left: -(this.sidebarBack.width())});
            
            this.sidebarBack.hover(
            function() {
                $(this).addClass("sidebar-back-hover");
            },
            function() {
                $(this).removeClass("sidebar-back-hover");
            });

            return;
        }

        // Used to get left value in number form
        var sidebarPanelPosition = this.sidebar.position();
        if (sidebarPanelPosition.left != 0) {
            this.sidebarBack.offset({left: 0});
        }
        else {
            this.sidebarBack.offset({left: -(this.sidebarBack.width())});
        }
    },

    sidebar_back_one_level: function() {
        this.topic_node_view.back_to_parent();
    },

    show_sidebar: function() {
        this.state_model.set("open", true);
    },

    hide_sidebar: function() {
        this.state_model.set("open", false);
    },

    show_sidebar_tab: function() {
        this.sidebarTab.fadeIn(115);
    },

    hide_sidebar_tab: function() {
        this.sidebarTab.fadeOut(115);
    },

    navigate_paths: function(paths, callback) {
        // Allow callback here to let the 'title' of the node be returned to the router
        // This will allow the title of the page to be updated during navigation events
        this.topic_node_view.defer_navigate_paths(paths, callback);
    }

});

window.TopicContainerInnerView = BaseView.extend({
    className: "topic-container-inner",
    template: HB.template("topics/sidebar-content"),

    initialize: function(options) {
        var self = this;

        this.state_model = options.state_model;
        this.entity_key = options.entity_key;
        this.entity_collection = options.entity_collection;
        this.level = options.level;
        this._entry_views = [];
        this.has_parent = options.has_parent;

        if (!(this.model.get(this.entity_key) instanceof this.entity_collection)) {

            this.model.set(this.entity_key, new this.entity_collection(this.model.get(this.entity_key)));
        }

        this.listenTo(this.model.get(this.entity_key), 'add', this.add_new_entry);
        this.listenTo(this.model.get(this.entity_key), 'reset', this.add_all_entries);

        this.add_all_entries();

        this.state_model.set("current_level", options.level);
    },

    render: function() {
        var self = this;

        this.$el.html(this.template(this.model.attributes));

        this.$(".sidebar").slimScroll({
            color: "#083505",
            opacity: 0.2,
            size: "6px",
            distance: "1px",
            alwaysVisible: true
        });

        // resize the scrollable part of sidebar to the page height
        $(window).resize(_.throttle(function() {
            var height = $(window).height();
            self.$(".slimScrollDiv, .sidebar").height(height);
        }, 200));
        $(window).resize();

        return this;
    },

    add_new_entry: function(entry) {
        var view = new SidebarEntryView({model: entry});
        this.listenTo(view, "hideSidebar", this.hide_sidebar);
        this.listenTo(view, "showSidebar", this.show_sidebar);
        this._entry_views.push(view);
        this.$(".sidebar").append(view.render().$el);
        if (window.statusModel.get("is_logged_in")) {
            this.load_entry_progress();
        }
    },

    add_all_entries: function() {
        this.render();
        this.model.get(this.entity_key).forEach(this.add_new_entry, this);
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
        return _.find(this.model.get(this.entity_key).models, function(model) {return model.get("slug")==slug;});
    },

    close: function() {
        _.each(this._entry_views, function(view) {
            view.model.set("active", false);
        });
        this.remove();
    },

    load_entry_progress: _.debounce(function() {

        var self = this;

        // load progress data for all videos
        var video_ids = $.map(this.$(".icon-Video[data-content-id]"), function(el) { return $(el).data("content-id"); });
        if (video_ids.length > 0) {
            videologs = new VideoLogCollection([], {content_ids: video_ids});
            videologs.fetch().then(function() {
                videologs.models.forEach(function(model) {
                    var newClass = model.get("complete") ? "complete" : "partial";
                    self.$("[data-video-id='" + model.get("video_id") + "']").removeClass("complete partial").addClass(newClass);
                });
            });
        }

        // load progress data for all exercises
        var exercise_ids = $.map(this.$(".icon-Exercise[data-content-id]"), function(el) { return $(el).data("content-id"); });
        if (exercise_ids.length > 0) {
            exerciselogs = new ExerciseLogCollection([], {exercise_ids: exercise_ids});
            exerciselogs.fetch()
                .then(function() {
                    exerciselogs.models.forEach(function(model) {
                        var newClass = model.get("complete") ? "complete" : "partial";
                        self.$("[data-exercise-id='" + model.get("exercise_id") + "']").removeClass("complete partial").addClass(newClass);
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
                    data.objects.forEach(function(ind, quiz) {
                        var newClass = quiz.complete ? "complete" : "partial";
                        // TODO(jamalex): see above; just assume we only have 1 quiz
                        self.$("[data-quiz-id]").removeClass("complete partial").addClass(newClass);
                    });
                });
        }

        // load progress data for all content
        var content_ids = $.map(this.$(".sidebar-icon:not(.icon-Exercise, .icon-Video, .icon-Topic)"), function(el) { return $(el).data("content-id"); });
        if (content_ids.length > 0) {
            contentlogs = new ContentLogCollection([], {content_ids: content_ids});
            contentlogs.fetch()
                .then(function() {
                    contentlogs.models.forEach(function(model) {
                        var newClass = model.get("complete") ? "complete" : "partial";
                        self.$("[data-content-id='" + content.get("content_id") + "']").removeClass("complete partial").addClass(newClass);
                    });
                });
        }

    }, 100)

});

window.SidebarEntryView = BaseView.extend({

    tagName: "li",

    template: HB.template("topics/sidebar-entry"),

    events: {
        "click": "clicked"
    },

    initialize: function() {

        this.listenTo(this.model, "change:active", this.toggle_active);

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    clicked: function(ev) {
        ev.preventDefault();
        if (!this.model.get("active")) {
            window.channel_router.navigate(this.model.get("path"), {trigger: true});
        } else if (this.model.get("kind") !== "Topic") {
            this.trigger("hideSidebar");
        }
        return false;
    },

    toggle_active: function() {
        this.$(".sidebar-entry").toggleClass("active-entry", this.model.get("active"));
    }

});


window.TopicContainerOuterView = BaseView.extend({

    initialize: function(options) {

        this.render = _.bind(this.render, this);

        this.state_model = options.state_model;

        this.entity_key = options.entity_key;
        this.entity_collection = options.entity_collection;

        this.inner_views = [];
        this.model = this.model || new TopicNode({channel: options.channel});
        this.model.fetch().then(this.render);
        this.content_view = new ContentAreaView({
            el: "#content-area"
        });

    },

    render: function() {
        this.show_new_topic(this.model);
        this.trigger("render_complete");
    },

    show_new_topic: function(node) {

        var new_topic = this.add_new_topic_view(node);

        this.$el.append(new_topic.el);

        // Listeners
        this.listenTo(new_topic, 'back_button_clicked', this.back_to_parent);
        this.listenTo(new_topic, 'hideSidebar', this.hide_sidebar);
        this.listenTo(new_topic, 'showSidebar', this.show_sidebar);
    },

    add_new_topic_view: function(node) {

        this.state_model.set("current_level", this.state_model.get("current_level") + 1);

        var data = {
            model: node,
            has_parent: this.inner_views.length >= 1,
            entity_key: this.entity_key,
            entity_collection: this.entity_collection,
            state_model: this.state_model,
            level: this.state_model.get("current_level")
        };

        var new_topic = new TopicContainerInnerView(data);

        if (this.inner_views.length === 0){
            new_topic.model.set("has_parent", false);
            this.inner_views.unshift(new_topic);
        } else if (this.inner_views.length >= 1) {
            // this.inner_views[0].hide();
            this.inner_views.unshift(new_topic);
        }

        return new_topic;
    },

    defer_navigate_paths: function(paths, callback) {
        if (this.inner_views.length === 0){
            var self = this;
            this.listenToOnce(this, "render_complete", function() {self.navigate_paths(paths, callback);});
        } else {
            this.navigate_paths(paths, callback);
        }
    },

    navigate_paths: function(paths, callback) {
        var check_views = [];
        for (var i = this.inner_views.length - 2; i >=0; i--) {
            check_views.push(this.inner_views[i]);
        }
        // Should only ever remove a bunch of inner_views once during the whole iteration
        var pruned = false;
        for (i = 0; i < paths.length; i++) {
            var check_view = check_views[i];
            if (paths[i]!=="") {
                if (check_view!==undefined) {
                    if (check_view.model.get("slug")==paths[i]) {
                        continue;
                    } else {
                        check_view.model.set("active", false);
                        if (!pruned) {
                            this.remove_topic_views(check_views.length - i);
                            pruned = true;
                        }
                    }
                }
                var node = this.inner_views[0].node_by_slug(paths[i]);
                if (node!==undefined) {
                    if (node.get("kind")==="Topic") {
                        this.show_new_topic(node);
                    } else {
                        this.entry_requested(node);
                    }
                    node.set("active", true);
                }
            } else if (!pruned) {
                if (check_view!==undefined) {
                    check_view.model.set("active", false);
                    this.remove_topic_views(check_views.length - i);
                }
            }
        }
        if (callback) {
            callback(this.inner_views[0].model.get("title"));
        }
    },

    remove_topic_views: function(number) {
        for (var i=0; i < number; i++) {
            if (this.inner_views[0]) {
                this.inner_views[0].model.set("active", false);
                if (_.isFunction(this.inner_views[0].close)) {
                    this.inner_views[0].close();
                } else {
                    this.inner_views[0].remove();
                }
                this.inner_views.shift();
            }
        }
        if (this.state_model.get("content_displayed")) {
            number--;
            this.state_model.set("content_displayed", false);
        }
        this.state_model.set("current_level", this.state_model.get("current_level") - number);
        this.show_sidebar();
    },

    back_to_parent: function() {
        this.remove_topic_views(1);
        window.channel_router.url_back();
    },

    entry_requested: function(entry) {
        var kind = entry.get("kind") || entry.get("entity_kind");
        var id = entry.get("id") || entry.get("entity_id");

        var view;

        switch(kind) {

            case "Exercise":
                view = new ExercisePracticeView({
                    exercise_id: id,
                    context_type: "playlist",
                    context_id: this.model.get("id")
                });
                this.content_view.show_view(view);
                break;

            case "Quiz":
                view = new ExerciseQuizView({
                    quiz_model: new QuizDataModel({entry: entry}),
                    context_id: this.model.get("id") // for now, just use the playlist ID as the quiz context_id
                });
                this.content_view.show_view(view);
                break;

            default:
                view = new ContentWrapperView({
                    id: id,
                    context_id: this.model.get("id")
                });
                this.content_view.show_view(view);
                break;
        }
        this.content_view.model = entry;
        this.inner_views.unshift(this.content_view);
        this.state_model.set("content_displayed", true);
        this.hide_sidebar();
    },

    hide_sidebar: function() {
        this.trigger("hideSidebar");
    },

    show_sidebar: function() {
        this.trigger("showSidebar");
    }
});
