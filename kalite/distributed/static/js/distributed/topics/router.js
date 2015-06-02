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
        var addParam;
        if (window.location.toString().split("?").length > 1) {
            addParam = "?" + window.location.toString().split("?")[1];
        } else {
            addParam = "";
        }
        this.navigate(this.default_channel + "/" + addParam, {trigger: true, replace: true});
    },

    intercept_learn_nav: function(event){
        this.navigate(this.default_channel + "/", {trigger: true});
        return false;
    },

    navigate_channel: function(channel, splat) {
        if (this.channel!==channel) {
            React.render(
                React.createElement(SidebarView, {
                    channel: channel, 
                    entity_key: "children", 
                    entity_collection: TopicCollection}),
                document.getElementById('sidebar-container')
            );
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
        if(splat){
            splat = splat || "/";
            splat = 'root/' + splat;
        }else{
            splat = 'root/';
        }
        if (splat.indexOf("/", splat.length - 1)==-1) {
            splat += "/";
            this.navigate(Backbone.history.getFragment() + "/");
        }
        var selected_path = splat.split("/").slice(0,-1);
        sidebar_columns_model.set('columns', selected_path);
    },

    set_page_title: function(title) {
        document.title = document.title.replace(/(\w+)( |:[^|]*)(\|)/, sprintf("$1: %s $3", title));
    },

    trigger_navigation_callback: function() {
        this.trigger("navigation");
    }
});

