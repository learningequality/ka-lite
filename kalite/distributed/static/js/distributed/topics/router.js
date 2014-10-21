TopicRouter = Backbone.Router.extend({
    initialize: function(options) {
        this.control_view = new SidebarView({
                channel: options.channel,
                entity_key: "children",
                entity_collection: TopicCollection
        });

        if (options.splat!==undefined) {
            this.navigate_topics(options.splat);
        }
    },

    routes: {
        "*splat":    "navigate_topics"
    },

    navigate_topics: function(splat) {
        this.control_view.navigate_paths((splat || "").split("/"));
    },

    add_slug: function(slug) {
        this.navigate(Backbone.history.getFragment() + slug + "/");
    },

    url_back: function() {
        var current_url = Backbone.history.getFragment();
        var fragments = current_url.split("/").slice(0,-1);
        if (fragments.length > 0) {
            this.navigate(fragments.slice(0,-1).join("/") + "/");
        }
    }
});

ChannelRouter = Backbone.Router.extend({
    routes: {
        ":channel/(*splat)":    "navigate_channel"
    },

    navigate_channel: function(channel, splat) {
        window.topic_router = this.topic_router = new TopicRouter({channel: channel, splat: splat});
    }
});