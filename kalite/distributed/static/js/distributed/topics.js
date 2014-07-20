// Models
window.TopicNode = Backbone.Model.extend({
    url: ALL_TOPICS_URL
});

// Collections 
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode
});

// Views

window.SidebarView = Backbone.View.extend({

    el: ".sidebar-wrapper",

    template: HB.template("distributed/sidebar"),

    events: {
        "click .sidebar-tab": "toggle_sidebar"
    },

    initialize: function() {

        var self = this;

        _.bindAll(this);

        this._entry_views = [];

        this.model.set(this.entries_key, new this.EntryCollection(this.model.get(this.entries_key)));

        this.listenTo(this.model.get(this.entries_key), 'add', this.add_new_entry);
        this.listenTo(this.model.get(this.entries_key), 'reset', this.add_all_entries);

        this.state_model = new Backbone.Model({
            open: false
        });

        this.render();

        this.listenTo(this.state_model, "change:open", this.update_sidebar_visibility);

        this.listenTo(this.model, 'change', this.render);

        // this.$(".sidebar-tab").hide();
        // setTimeout(function() { self.$(".sidebar-tab").show(); }, 5000);

        this.add_all_entries();

    },

    render: function() {
        var self = this;
        this.$el.html(this.template(this.model.attributes));
        this.sidebar = this.$('').bigSlide({
            menu: this.$(".panel"),
            // push: "#page-container, #footer, .sidebar-tab",
            push: ".sidebar-tab",
            menuWidth: "220px"
        });

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


        this._entry_views.forEach(function(entry_view) {
            self.$(".sidebar").append(entry_view.render().$el);
            self.listenTo(entry_view, "clicked", self.item_clicked);
        });
        this.toggle_sidebar();
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

    add_new_entry: function(entry) {
        var view = new SidebarEntryView({model: entry});
        this._entry_views.push(view);
    },

    add_all_entries: function() {
        this.render();
        this.model.get(this.entries_key).map(this.add_new_entry);
    }

});

window.SidebarEntryView = Backbone.View.extend({

    tagName: "li",

    template: HB.template("distributed/sidebar-entry"),

    events: {
        "click": "clicked"
    },

    initialize: function() {

        _.bindAll(this);

        this.listenTo(this.model, "change:active", this.render);

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

});


window.TopicContainerOuter = Backbone.View.extend({

    class: "topic-container-outer",

    initialize: function() {

        _.bindAll(this);

        this.inner_views = [];
        this.model =  new TopicNode();
        this.model.fetch().then(this.render);
    },

    render: function() {
        this.show_new_topic(this.model);
    },

    show_new_topic: function(node) {
        // switch (node) {
        //     case 
        // }
        var new_topic = new TopicContainerInner({
            model: node
        });
        console.log(node.kind);

        // Only hide after we have the first one!
        // if (this.inner_views.length > 0) {
        //     this.inner_views[0].$el.hide();
        // }
        // Only show back button for nodes that have parents
        if (this.inner_views.length === 0){
            new_topic.model.set("has_parent", false);
        } else if (this.inner_views.length >= 1) {
            new_topic.model.set("has_parent", true);
        }
        this.$el.append(new_topic.el);
        this.inner_views.unshift(new_topic);

        // Listeners
        this.listenTo(new_topic, 'topic_node_clicked', this.show_new_topic);
        this.listenTo(new_topic, 'back_button_clicked', this.back_to_parent);
    },

    back_to_parent: function() {
        // Simply pop the first in the stack and show the next one
        this.inner_views[0].$el.hide();
        this.inner_views.shift();
        this.inner_views[0].$el.show();
    }
});

window.TopicContainerInner = SidebarView.extend({

    entries_key: "children",

    EntryCollection: TopicCollection,

    events: function(){
       return _.extend({},SidebarView.prototype.events,{
           'click .back-to-parent' : 'backToParent'
       });
    },

    item_clicked: function(view) {
        this.trigger('topic_node_clicked', view.model);
    },

    render: function() {
        SidebarView.prototype.render.call(this);
        if (this.model.get("has_parent")){
            this.$(".sidebar-navbar").append("<a href='#' title='Back' class='back-to-parent'><span class='glyphicon glyphicon-chevron-left'></span></a>");
        }
    },

    // events: {
    //     'click a.back-to-parent': 'backToParent'
    // },

    backToParent: function(ev) {
        this.trigger('back_button_clicked', this.model);
    }

    // topic_node_clicked: function(node) {
    //     this.trigger('topic_node_clicked', node);
    // }
});

window.TopicNodeView = Backbone.View.extend({

    template: HB.template("topics/topic_node"),

    initialize: function() {
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
    },

    events: {
        'click .topic-container-node-list-item': 'showChildCollection'
    },

    showChildCollection: function(ev) {
        ev.preventDefault();
        // Create the child elements and paste them on top
        this.trigger('topic_node_clicked', this.model);
    }
});