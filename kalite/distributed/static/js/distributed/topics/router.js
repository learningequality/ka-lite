TopicChannelRouter = Backbone.Router.extend({
    initialize: function(options) {
        _.bindAll(this);
        this.default_channel = options.default_channel;
        $("#nav_learn").click(this.intercept_learn_nav);
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

    intercept_learn_nav: function(event){
        event.preventDefault();
        this.navigate_default_channel();
        return false;
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
        this.navigate_splat(splat);
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
        this.control_view.navigate_paths(splat.split("/").slice(0,-1));
    },

    trigger_navigation_callback: function() {
        this.trigger("navigation");
    }
});

