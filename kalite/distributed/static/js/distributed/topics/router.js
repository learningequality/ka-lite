TopicRouter = Backbone.Router.extend({
    initialize: function(options) {
        this.control_view = options.control_view;
    },

    routes: {
        "(:domain/)(:subject/)(:topic/)(:tutorial/)":    "navigate_topics"
    },

    navigate_topics: function() {
        this.control_view.navigate_paths(arguments);
    }
});