window.KnowledgeMapView = Backbone.View.extend({

    template: HB.template("map/map"),

    initialize: function() {

        _.bindAll(this);

        this.model =  this.model || new TopicNode();

        this.model.fetch().then(this.render);

    },

    render: function() {

        this.$el.html(this.template());

        this.map = L.map('map', {
            center: [51.505, -0.09],
            zoom: 13
        });

        console.log(this.model);
    }
});
