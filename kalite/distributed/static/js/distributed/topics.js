window.TopicContainerView = Backbone.View.extend({

    template: HB.template("topics/topic_container"),

    initialize: function() { 

        this.render();

    },

    render: function() {

        this.$el.html(this.template());

    }

});