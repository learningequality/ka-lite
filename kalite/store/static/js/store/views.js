window.StoreView = Backbone.View.extend({

    template: HB.template("store/store"),

    events: {

    },

    initialize: function() {

        _.bindAll(this);

        // this.listenTo(this.model, "change:active", this.render);

    },

    render: function() {
        this.$el.html(this.template()); // this.model.attributes
        return this;
    },

});

