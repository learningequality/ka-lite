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

        this.model =  new TopicNode();
        this.model.fetch().then(this.render);
    },

    render: function() {
        this.inner_view = new TopicContainerInner({
            model: this.model
        });
        this.$el.append(this.inner_view.el);
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
        });
    }
});

window.TopicNodeView = Backbone.View.extend({

    template: HB.template("topics/topic_node"),



    initialize: function() {
        this.render()
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
    }

});