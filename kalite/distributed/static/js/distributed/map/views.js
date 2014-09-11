window.KnowledgeMapView = Backbone.View.extend({

    template: HB.template("map/map"),

    initialize: function() {

        _.bindAll(this);

        this.collection =  this.collection || new ExerciseCollection();

        this.collection.fetch().then(this.render);

        this.LeafIcon = L.icon({
                iconUrl: '/static/images/distributed/default-60x60.png',
                iconSize:     [38, 95],
                shadowSize:   [50, 64],
                iconAnchor:   [22, 94],
                shadowAnchor: [4, 62],
                popupAnchor:  [-3, -76]
        });

    },

    render: function() {

        this.$el.html(this.template());

        this.map = L.map('map', {
            center: [0, 0],
            zoom: 13
        });

        for (i=0; i < this.collection.length; i++) {
            model = this.collection.models[i];
            L.marker([model.get("h_position"), model.get("v_position")], {icon: this.LeafIcon}).addTo(this.map);
        }
    }
});
