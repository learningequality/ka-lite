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

    zoomLevels: ["Domains", "Subjects", "Topics", "Tutorials", "Exercises"],

    initialize: function(options) {

        _.bindAll(this);

        this.zoomLevel = options.zoomLevel || 0;

        this.zoom = 3;

        this.zoomLayers = {};

        this.render();

    },

    render: function() {

        this.$el.html(this.template());

        this.map = L.map('map', {
            center: [0, 0],
            zoom: this.zoom,
            zoomControl: false
        });

        this.map.addControl(new zoomControl());

        this.map.on('zoomIn', this.zoomIn);

        this.map.on('zoomOut', this.zoomOut);

        this.showCurrentLayer();
        
    },

    zoomIn: function() {
        if (this.zoomLevel < this.zoomLevels.length - 1) {
            this.zoomLevel += 1;
            this.showCurrentLayer();
        }
    },

    zoomOut: function() {
        if (this.zoomLevel > 0) {
            this.zoomLevel = this.zoomLevel - 1;
            this.showCurrentLayer();
        }
    },

    showCurrentLayer: function() {
        if (this.current_layer!==undefined) {
            this.current_layer.hideLayer();
        }

        if (this.zoomLayers[this.zoomLevels[this.zoomLevel]]===undefined) {
            collection = new TopicCollection([{that:"this"}], {url: TOPIC_DATA_URLS[this.zoomLevels[this.zoomLevel]]});
            this.zoomLayers[this.zoomLevels[this.zoomLevel]] = new KnowledgeMapLayerView({collection: collection, map: this.map, zoom: this.zoom, zoomLevel: this.zoomLevels[this.zoomLevel]});
        } else {
            this.zoomLayers[this.zoomLevels[this.zoomLevel]].showLayer();
        }

        this.current_layer =  this.zoomLayers[this.zoomLevels[this.zoomLevel]];
    }
});

window.KnowledgeMapLayerView = Backbone.View.extend({

    initialize: function(options) {

        _.bindAll(this);

        this.map = options.map;
        this.zoom = options.zoom;
        this.zoomLevel = options.zoomLevel;

        this.collection.fetch().then(this.render);

    },

    render: function() {

        this.subviews = {};

        this.layerGroup = L.featureGroup();

        for (i=0; i < this.collection.length; i++) {
            model = this.collection.models[i];
            this.addSubView(model);
        }

        this.showLayer();
    },

    addSubView: function(model) {
        if (model.coordinates()) {
            this.subviews[model.get("id")] = new KnowledgeMapItemView({model: model, map: this.map, zoom: this.zoom, zoomLevel: this.zoomLevel});
            this.layerGroup.addLayer(this.subviews[model.get("id")].marker);
        }
    },

    hideLayer: function() {
        this.map.removeLayer(this.layerGroup);
    },

    showLayer: function() {
        this.map.addLayer(this.layerGroup);
        this.layerGroup.on("click", this.hideLayer);
    }
});

window.KnowledgeMapItemView = Backbone.View.extend({

    initialize: function(options) {

        _.bindAll(this);

        this.map = options.map;
        this.zoom = options.zoom;
        this.zoomLevel = options.zoomLevel;

        this.model = options.model;

        this.render();

    },

    render: function() {
        this.marker = L.marker(this.model.coordinates(), {icon: L.divIcon({className: 'map-icon', html: "<div>" + this.model.get("title") + "</div>", iconSize: [100,100]}), title: this.model.get("title")});
        if (this.zoomLevel=="Exercises") {
            this.marker.on("click", this.navigateToExercise);
        } else {
            this.marker.on("click", this.zoomToSubLayer);
        }
    },

    zoomToSubLayer: function() {
        this.collection = this.collection || new TopicCollection(this.model.get("children"));
        this.map.panTo(this.collection.centerOfMass());
        this.map.fire("zoomIn");
    }
});