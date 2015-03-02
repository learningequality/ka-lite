ChannelRouter = Backbone.Router.extend({
    initialize: function(options) {
        this.default_channel = options.default_channel;
    },

    routes: {
        "":   "navigate_default_channel",
        // This will catch any navigation events to other content items, and...
        ":channel/(*splat)":    "navigate_channel",
        // ...this will catch any other navigation events. We want to make sure
        // points are updated correctly in either case.
        "/(.*)/": "trigger_navigation_callback"
    },

    navigate_default_channel: function() {
        this.navigate(this.default_channel + "/", {trigger: true, replace: true});
    },

    navigate_channel: function(channel, splat) {
        if (this.channel!==channel) {
            this.control_view = new SidebarView({
                channel: channel,
                entity_key: "children",
                entity_collection: TopicCollection
            });
            this.channel = channel;
        }
        splat = splat || "/";
        if (splat.indexOf("/", splat.length - 1)==-1) {
            splat += "/";
            this.navigate(Backbone.history.getFragment() + "/", {replace: true});
        }
        this.control_view.navigate_paths(splat.split("/"));
    },

    add_slug: function(slug) {
        this.navigate(Backbone.history.getFragment() + slug + "/", {trigger: true});
    },

    url_back: function() {
        var current_url = Backbone.history.getFragment();
        var fragments = current_url.split("/").slice(0,-1);
        if (fragments.length > 0) {
            this.navigate(fragments.slice(0,-1).join("/") + "/", {trigger: true});
        }
    },

    navigate_splat: function(splat) {
        splat = splat || "/";
        if (splat.indexOf("/", splat.length - 1)==-1) {
            splat += "/";
            this.navigate(Backbone.history.getFragment() + "/");
        }
        this.control_view.navigate_paths(splat.split("/"));
    },

    trigger_navigation_callback: function() {
        this.trigger("navigation");
    }
});

TopicChannelRouter = ChannelRouter.extend({
    navigate_channel: function(channel, splat) {
        if (this.channel!==channel) {
            this.control_view = new SidebarView({
                channel: channel,
                entity_key: "children",
                entity_collection: TopicCollection
            });
            this.channel = channel;
        }
        this.navigate_splat(splat);
    }
});
