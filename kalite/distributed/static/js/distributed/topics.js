// Models
window.TopicNode = Backbone.Model.extend({
    url: ALL_TOPICS_URL
});

// Collections 
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode
}); 

// Views
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
        var new_topic = new TopicContainerInner({
            model: node
        });
        this.$el.append(new_topic.el);
        if (this.inner_views.length > 0) {
            this.inner_views[0].$el.hide();     
        }
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

window.TopicContainerInner = Backbone.View.extend({

    class: "topic-container-inner",

    template: HB.template("topics/topic_container_inner"),

    initialize: function() { 
        this.model.set("children", new TopicCollection(this.model.get("children")));
        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        var self = this;
        
        self.node_views = [];
        this.model.get("children").each(function(node) {
            var node_view = new TopicNodeView({ model: node });
            self.$('.topic-container-node-list').append(node_view.el);
            self.listenTo(node_view, 'topic_node_clicked', self.topic_node_clicked)
        });
    }, 

    events: {
        'click a.back-to-parent': 'backToParent'
    },

    backToParent: function(ev) {
        this.trigger('back_button_clicked', this.model);
    },

    topic_node_clicked: function(node) {
        this.trigger('topic_node_clicked', node);
    }
});

window.TopicNodeView = Backbone.View.extend({

    template: HB.template("topics/topic_node"),

    initialize: function() {
        this.render()
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