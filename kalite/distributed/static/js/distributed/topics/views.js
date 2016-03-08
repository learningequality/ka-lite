var BaseView = require("base/baseview");
var _ = require("underscore");
var $ = require("base/jQuery");
require("jquery-slimscroll/jquery.slimscroll");
var Backbone = require("base/backbone");
var messages = require("utils/messages");
var $script = require("scriptjs");

require("../../../css/distributed/sidebar.less");

var ContentViews = require("content/views");
var Models = require("./models");

var RatingView = require("rating/views");
var RatingModels = require("rating/models");
var RatingModel = RatingModels.RatingModel;
var ContentRatingCollection = RatingModels.ContentRatingCollection;

// Views

var ContentAreaView = BaseView.extend({

    template: require("./hbtemplates/content-area.handlebars"),

    initialize: function() {
        this.model = new Backbone.Model();
        this.render();

        this.content_rating_collection = new ContentRatingCollection();
        var self = this;
        this.content_rating_collection.url = function() {
            return sessionModel.get("CONTENT_RATING_LIST_URL") + "/?" + $.param({
                "user": window.statusModel.get("user_id"),
                "content_kind": self.model.get("kind"),
                "content_id": self.model.get("id")
            });
        };
        this.listenTo(window.statusModel, "change:user_id", this.show_rating);
        _.bindAll(this, "show_rating");
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    show_view: function(view) {
        // hide any messages being shown for the old view
        messages.clear_messages();

        this.close();
        // set the new view as the current view
        this.currently_shown_view = view;

        // show the view
        this.$(".content").html("").append(view.$el);
    },

    should_show_rating: function() {
        /*
        This function determines whether a rating should be shown for the content item.
        returns: true or false
        */
        var entry_available = (typeof this.model !== "undefined") && !!this.model.get("available");
        var logged_in = window.statusModel.has("user_id");
        return logged_in && entry_available;
    },

    remove_rating_view: function() {
        // Remove the rating view if it exists.
        if (typeof this.rating_view !== "undefined") {
            this.rating_view.remove();
            delete this.rating_view;
        }
    },

    show_rating: function() {
        // First, determine whether we should show the rating at all.
        // If it should not be shown, be sure to remove the rating_view; subsequent logic depends on that.
        if ( !this.should_show_rating() ) {
            this.remove_rating_view();
            return;
        }

        // Secondly, if the rating_view is previously deleted or never shown before at all, then define it.
        if( typeof this.rating_view === "undefined" ) {
            this.rating_view = this.add_subview(RatingView, {});
            this.$("#rating-container-wrapper").append(this.rating_view.el);
        }

        // Finally, handle the actual display logic
        if( this.rating_view.model === null || this.rating_view.model.get("content_id") !== this.model.get("id") ) {
            var self = this;
            this.content_rating_collection.fetch().done(function(){
                // Queue up a save on the model we're about to switch out, in case it hasn't been synced.
                if (self.rating_view.model !== null && self.rating_view.model.hasChanged()) {
                    self.rating_view.model.debounced_save();
                }
                if(self.content_rating_collection.models.length === 1) {
                    self.rating_view.model = self.content_rating_collection.pop();
                    self.rating_view.render();
                } else if ( self.content_rating_collection.models.length === 0 ) {
                    self.rating_view.model = new RatingModel({
                            "user": window.statusModel.get("user_uri"),
                            "content_kind": self.model.get("kind"),
                            "content_id": self.model.get("id")
                    });
                    self.rating_view.render();
                } else {
                    messages.show_message("error", "Server Error: More than one rating found for this user and content item!", "too-many-ratings-msg");
                    self.remove_rating_view();
                }
            }).error(function(){
                console.log("content rating collection failed to fetch");
            });
        }
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
    }

});

var SidebarView = BaseView.extend({
    el: "#sidebar-container",
    template: require("./hbtemplates/sidebar.handlebars"),

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
            current_level: 0,
            channel: this.channel
        });

        this.render();

        this.listenTo(this.state_model, "change:open", this.update_sidebar_visibility);
        this.listenTo(this.state_model, "change:current_level", this.update_sidebar_visibility);
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

    resize_for_narrow: function() {
        if (this.state_model.get("open")) {
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
            this.sidebar.animate({"left": sidebarPanelNewLeft}, 115, function () {
                self.set_sidebar_back();
            });

            this.sidebarTab.animate({left: this.sidebar.width() + sidebarPanelNewLeft}, 115);
        }
    },

    // Pretty much the code for pre-back-button sidebar resize
    resize_for_wide: function() {
       if (this.state_model.get("open")) {
           var current_level = this.state_model.get("current_level");
           var column_width = this.$(".topic-container-inner").width();
           var last_column_width = 400;

           this.width = (current_level-1) * column_width + last_column_width + 10;
           this.sidebar.width(this.width);
           this.sidebar.css({left: 0});
           this.sidebarTab.css({left: this.width});

            this.set_sidebar_back();
       }
    },

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
            this.sidebar.css({left: 0});
            this.resize_sidebar();
            // Used to get left value in number form
            var sidebarPanelPosition = this.sidebar.position();
            this.sidebarTab.css({left: this.sidebar.width() + sidebarPanelPosition.left}).html('<span class="icon-circle-left"></span>');
            this.$(".sidebar-fade").show();
        } else {
            // In an edge case, this.width may be undefined -- if so, then just make sure a sufficiently high
            // numerical value is set to hide the sidebar
            this.sidebar.css({left: -(this.width || $(window).width())});
            this.sidebarTab.css({left: 0}).html('<span class="icon-circle-right"></span>');
            this.$(".sidebar-fade").hide();
        }
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
        if (sidebarPanelPosition.left !== 0) {
            this.sidebarBack.offset({left: 0});
        }
        else {
            this.sidebarBack.offset({left: -(this.sidebarBack.width())});
        }

        // Disable or enable the back button depending on whether it is visible or not.
        if (this.sidebarBack.position().left <= 0) {
            this.disable_back_button();
        } else {
            this.enable_back_button();
        }
    },

    enable_back_button: function() {
        this.sidebarBack.find("button").removeAttr("disabled");
    },

    disable_back_button: function() {
        this.sidebarBack.find("button").attr("disabled", "disabled");
    },

    sidebar_back_one_level: function() {
        this.topic_node_view.back_to_parent();
    },

    show_sidebar: function() {
        if (!this.state_model.get("open")) {
            this.state_model.set("open", true);
        }
    },

    hide_sidebar: function() {
        if (this.state_model.get("open")) {
            this.state_model.set("open", false);
        }
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

var TopicContainerInnerView = BaseView.extend({
    className: "topic-container-inner",
    template: require("./hbtemplates/sidebar-content.handlebars"),

    initialize: function(options) {

        _.bindAll.apply(_, [this].concat(_.functions(this)));

        var self = this;

        this.state_model = options.state_model;
        this.entity_key = options.entity_key;
        this.entity_collection = options.entity_collection;
        this.level = options.level;
        this._entry_views = [];
        this.has_parent = options.has_parent;

        this.collection = new this.entity_collection({parent: this.model.get("id"), channel: this.state_model.get("channel")});

        this.collection.fetch().then(this.add_all_entries);

        this.state_model.set("current_level", options.level);

        // resize the scrollable part of sidebar to the page height
        $(window).resize(self.window_resize_callback);

        // When scrolling, increase the height of the element
        // until it fills up the sidebar panel
        $(window).scroll(self.window_scroll_callback);
    },

    window_scroll_callback: _.throttle(function() {
        var sidebarHeight = $(".sidebar-panel").height();
        var deltaHeight = $(window).scrollTop() + self.$(".slimScrollDiv, .sidebar").height();
        var height = Math.min(sidebarHeight, deltaHeight);
        self.$(".slimScrollDiv, .sidebar").height(height);
    }, 200),

    window_resize_callback: _.throttle(function() {
        var height = $(window).height();
        self.$(".slimScrollDiv, .sidebar").height(height);
    }, 200),

    render: function() {
        var self = this;

        this.$el.html(this.template(this.model.attributes));

        $(this.$(".sidebar")).slimScroll({
            color: "#083505",
            opacity: 0.2,
            size: "6px",
            distance: "1px",
            alwaysVisible: true
        });

        // Ensure these are called once in order to get the right size initially.
        _.defer( function() {
            self.window_resize_callback();
            self.window_scroll_callback();
        });

        return this;
    },

    add_new_entry: function(entry) {
        var view = new SidebarEntryView({model: entry});
        this.listenTo(view, "hideSidebar", this.hide_sidebar);
        this.listenTo(view, "showSidebar", this.show_sidebar);
        this._entry_views.push(view);
        this.$(".sidebar").append(view.render().$el);
    },

    add_all_entries: function() {
        this.render();
        this.collection.forEach(this.add_new_entry, this);
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

    deferred_node_by_slug: function(slug, callback) {
        // Convenience method to return a node by a passed in slug
        if (this.collection.loaded === true) {
            this.node_by_slug(slug, callback);
        } else {
            var self = this;
            this.listenToOnce(this.collection, "sync", function() {self.node_by_slug(slug, callback);});
        }
    },

    node_by_slug: function(slug, callback) {
        callback(this.collection.findWhere({slug: slug}));
    },

    close: function() {
        _.each(this._entry_views, function(view) {
            view.model.set("active", false);
        });
        this.remove();
    }

});

var SidebarEntryView = BaseView.extend({

    tagName: "li",

    template: require("./hbtemplates/sidebar-entry.handlebars"),

    events: {
        "click": "clicked"
    },

    initialize: function() {

        _.bindAll(this, "render");

        this.listenTo(this.model, "change", this.render);

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
    }

});


var TopicContainerOuterView = BaseView.extend({

    initialize: function(options) {

        this.render = _.bind(this.render, this);

        this.state_model = options.state_model;

        this.entity_key = options.entity_key;
        this.entity_collection = options.entity_collection;

        this.model = new Models.TopicNode({"id": "root", "title": "Khan"});

        this.inner_views = [];
        this.render();
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

        this.trigger("inner_view_added");

        // Listeners
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

        this.inner_views.unshift(new_topic);

        this.trigger("length_" + this.inner_views.length);

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

        var self = this;

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
                this.defer_add_topic(paths[i], i);
            } else if (!pruned) {
                if (check_view!==undefined) {
                    check_view.model.set("active", false);
                    this.remove_topic_views(check_views.length - i);
                }
            }
        }
        if (!pruned && (paths.length < check_views.length)) {
            // Double check that paths and check_views are the same length
            this.remove_topic_views(check_views.length - paths.length);
        }
        if (callback) {
            this.stopListening(this, "inner_view_added");

            this.listenTo(this, "inner_view_added", function() {
                callback(self.inner_views[0].model.get("title"));
            });
        }
    },

    defer_add_topic: function(path, view_length) {
        var self = this;
        if (this.inner_views.length==view_length + 1) {
            this.add_topic_from_inner_view(path);
        } else {
            this.listenToOnce(this, "length_" + (view_length + 1), function() {self.add_topic_from_inner_view(path);});
        }
    },

    add_topic_from_inner_view: function(path) {
        var self = this;

        this.inner_views[0].deferred_node_by_slug(path, function(node){
            /*
            Ultimately this will be called once for each TopicNode in the encapsulating SidebarView's TopicCollection
            corresponding to the given path.

            If no path is found, e.g. because an invalid url was entered (or because we're using the testing
            framework) then node will be undefined. We still request the entry in order to complete the Sidebar
            display logic, even though nothing will be shown.
             */
            if (node!==undefined) {
                if (node.get("kind")==="Topic") {
                    self.show_new_topic(node);
                } else {
                    self.entry_requested(node);
                }
                node.set("active", true);
            } else {
                self.entry_requested(node);
            }
        });
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
        window.channel_router.url_back();
    },

    entry_requested: function(entry) {
        // entry could be undefined if we've requested a content item that *doesn't exist*, either through a bad url
        // or more likely because we're using the testing framework. In this case, just pretend like we finished
        // without actually showing anything.
        var kind;
        var id;
        if( entry !== undefined ) {
            kind = entry.get("kind") || entry.get("entity_kind");
            id = entry.get("id") || entry.get("entity_id");
        } else {
            kind = "Video";
            id = "undefined_entry_id";
            entry = new Models.TopicNode();
        }

        this.content_view.model = entry;
        // The rating subview depends on the content_view.model, but we can't just listen to events on the model
        // to trigger show_rating, since the actual object is swapped out here. We must call it explicitly.
        this.content_view.show_rating();

        var view = new ContentViews.ContentWrapperView({
            id: id,
            kind: kind,
            context_id: this.model.get("id"),
            channel: window.channel_router.channel
        });

        this.content_view.show_view(view);

        this.inner_views.unshift(this.content_view);
        this.trigger("inner_view_added");
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

module.exports = {
    SidebarView: SidebarView,
    SidebarEntryView: SidebarEntryView,
    TopicContainerInnerView: TopicContainerInnerView,
    TopicContainerOuterView: TopicContainerOuterView,
    ContentAreaView: ContentAreaView
};
