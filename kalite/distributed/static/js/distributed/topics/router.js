TopicRouter = Backbone.Router.extend({
    initialize: function(options) {
        this.control_view = options.control_view;
    },

    routes: {
        "(:domain/)(:subject/)(:topic/)(:tutorial/)(:content/)":    "navigate_topics"
    },

    navigate_topics: function() {
        this.control_view.navigate_paths(arguments);
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