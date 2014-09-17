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

        this.map.on('zoom_in', this.zoom_in);

        this.map.on('zoom_out', this.zoom_out);

        this.map.on('zoomOut', this.zoomOut);

        this.showCurrentLayer();
        
    },

    zoomIn: function() {
    zoom_in: function(data) {
        if (this.zoomLevel < this.zoomLevels.length - 1) {
            this.zoomLevel += 1;
            this.show_current_layer();
            if (data.slug_modified!==true) {
                window.router.add_slug(this.zoomLevels[this.zoomLevel]);
            }
        }
    },

    zoom_out: function() {
        if (this.zoomLevel > 0) {
            this.zoomLevel = this.zoomLevel - 1;
            this.show_current_layer();
            window.router.url_back();
        }
    },

    show_current_layer: function() {
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
            this.add_subview(model);
        }

        this.show_layer();
    },

    add_subview: function(model) {
        if (model.coordinates()) {
            this.subviews[model.get("id")] = new KnowledgeMapItemView({model: model, map: this.map, zoom: this.zoom, zoomLevel: this.zoomLevel});
            this.layerGroup.addLayer(this.subviews[model.get("id")].marker);
        }
    },

    hide_layer: function() {
        if (this.layerGroup!==undefined) {
            this.map.removeLayer(this.layerGroup);
        }
    },

    show_layer: function() {
        this.map.addLayer(this.layerGroup);
        this.layerGroup.on("click", this.hide_layer);
    },
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
            this.marker.on("click", this.navigate_to_exercise);
        } else {
            this.marker.on("click", this.zoom_to_sub_layer);
        }
    },

    zoom_to_sub_layer: function() {
        this.collection = this.collection || new TopicCollection(this.model.get("children"));
        this.map.panTo(this.collection.centerOfMass());
        this.map.fire("zoomIn");
    }
});