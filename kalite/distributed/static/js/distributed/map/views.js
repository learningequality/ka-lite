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
            minZoom: this.zoom,
            maxZoom: this.zoom + this.zoomLevels.length - 1
        });

        this.map.on('zoom_in', this.zoom_in);

        this.map.on('zoom_out', this.zoom_out);

        this.map.on('zoomend', this.zoom_modify);

        this.map.on('dblclick', this.zoom_in);

        this.map.on('contextmenu', this.zoom_out);
      
    },

    zoom_modify: _.debounce(function(event) {
        if (this.map.getZoom() > this.zoom + this.zoomLevel || event.zoomtype === "zoom_in") {
            if (this.map.getZoom() > this.zoom + this.zoomLevel) {
                for (i=0; i < this.map.getZoom() - (this.zoom + this.zoomLevel); i++) {
                    this.zoom_in(event);
                }
            } else {
                this.zoom_in(event);
            }
        } else if (this.map.getZoom() < this.zoom + this.zoomLevel || event.zoomtype === "zoom_out") {
            if (this.map.getZoom() < this.zoom + this.zoomLevel) {
                for (i=0; i < (this.zoom + this.zoomLevel) - this.map.getZoom(); i++) {
                    this.zoom_out(event);
                }
            } else {
                this.zoom_out(event);
            }
        }
    }, 500),

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
            this.current_layer.hide_layer();
        }

        if (this.zoomLayers[this.zoomLevels[this.zoomLevel]]===undefined) {
            collection = new TopicCollection([], {url: TOPIC_DATA_URLS[this.zoomLevels[this.zoomLevel]]});
            this.zoomLayers[this.zoomLevels[this.zoomLevel]] = new KnowledgeMapLayerView({collection: collection, map: this.map, zoom: this.zoom, zoomLevel: this.zoomLevels[this.zoomLevel]});
        } else {
            this.zoomLayers[this.zoomLevels[this.zoomLevel]].show_layer();
        }

        this.current_layer =  this.zoomLayers[this.zoomLevels[this.zoomLevel]];

        this.map.setZoom(this.zoom + this.zoomLevel);

        return this.current_layer;
    },

    navigate_paths: function(paths) {
        var exercise = false;
        paths = _.reject(paths, function(slug) {return slug===null;});
        this.zoomLevel = paths.length;
        if (this.zoomLevel > this.zoomLevels.length - 1) {
            this.zoomLevel = this.zoomLevels.length - 1;
            exercise = true;
        }
        current_layer = this.show_current_layer();
        collection = new TopicCollection(_.filter(current_layer.collection.models, function(model){
            return model.get("ancestor_ids").slice(-1)===paths.slice(-1);
        }));
        if (collection.length > 0) {
            this.map.panTo(collection.center_of_mass());
        }
        if (exercise) {
            current_layer.defer_show_exercise_by_slug(paths.slice(-1)[0]);
        }
    }
});

window.KnowledgeMapLayerView = Backbone.View.extend({

    initialize: function(options) {

        _.bindAll(this);

        this.rendered = false;
        this.map = options.map;
        this.zoom = options.zoom;
        this.zoomLevel = options.zoomLevel;

        this.collection.fetch().then(this.render);

    },

    render: function() {

        var self = this;

        this.map.panTo(this.collection.center_of_mass());

        this.subviews = {};

        this.layerGroup = L.featureGroup();

        for (i=0; i < this.collection.length; i++) {
            model = this.collection.models[i];
            this.add_subview(model);
        }

        this.show_layer();

        _.defer(function(){
            self.rendered=true;
            self.trigger("rendered");
        });
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

    defer_show_exercise_by_slug: function(slug) {
        var self = this;
        if (this.rendered) {
            show_exercise_by_slug(slug);
        } else {
            this.listenToOnce(this, "rendered", function() {self.show_exercise_by_slug(slug);});
        }
    },

    show_exercise_by_slug: function(slug) {
        /* Note: this will break if used for anything other than the exercise item layer */
        model = _.find(this.collection.models, function(model) {return model.get("slug")===slug;});
        this.subviews[model.get("id")].show_exercise();
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
        this.map.panTo(this.model.coordinates());
        window.router.add_slug(this.model.get("slug"));
        this.map.fire("zoomend", {slug_modified: true, zoomtype: "zoom_in"});
    },

    navigate_to_exercise: function() {
        window.router.add_slug(this.model.get("slug"));
        this.show_exercise();
    },

    show_exercise: function() {
        this.exercise_view = new ExercisePracticeView({
            exercise_id: this.model.get("id"),
            context_type: "knowledgemap"
        });
        $(".content").append(this.exercise_view.$el);
        $("#overlay").show();
        $("#fade").show();
        $(".close").click(this.close_exercise);
    },

    close_exercise: function() {
        window.router.url_back();
        if (_.isFunction(this.exercise_view.close)) {
            this.exercise_view.close();
        } else {
            this.exercise_view.remove();
        }
        $("#overlay").hide();
        $("#fade").hide();
    }
});