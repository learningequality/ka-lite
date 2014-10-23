ChannelRouter = Backbone.Router.extend({
    initialize: function(options) {
        this.default_channel = options.default_channel;
    },

    routes: {
        "":   "navigate_default_channel",
        ":channel/(*splat)":    "navigate_channel"
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
