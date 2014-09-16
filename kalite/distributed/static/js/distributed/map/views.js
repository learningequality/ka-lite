var zoomControl = L.Control.extend({
    options: {
        position: 'topleft'
    },

    onAdd: function (map) {

        var container = L.DomUtil.create('div', 'leaflet-control-zoom leaflet-bar');

        L.DomEvent
            .addListener(container, 'click', L.DomEvent.stopPropagation)
            .addListener(container, 'click', L.DomEvent.preventDefault)
            .addListener(container, 'dblclick', L.DomEvent.stopPropagation)
            .addListener(container, 'dblclick', L.DomEvent.preventDefault);

        var plus = L.DomUtil.create('a', 'leaflet-control-zoom-in', container);

        plus.text = "+";
        plus.title = "Zoom in";
        plus.href = "#";

        L.DomEvent.addListener(plus, 'click', function(){map.fire('zoomIn')});
        
        var minus = L.DomUtil.create('a', 'leaflet-control-zoom-out', container);

        minus.text = "-";
        minus.title = "Zoom out";
        minus.href = "#";

        L.DomEvent.addListener(minus, 'click', function(){map.fire('zoomOut')});

        return container;
    }
});

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