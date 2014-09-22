window.AudioPlayerView = Backbone.View.extend({

    template: HB.template("audio/audio-player"),

    initialize: function() {

        _.bindAll(this);

        var self = this;
        window.statusModel.loaded.then(function() {
            // load the info about the content itself
            self.data_model = new ContentDataModel({id: self.options.id});
            if (self.data_model.get("id")) {
                self.data_model.fetch().then(function() {

                    if (window.statusModel.get("is_logged_in")) {

                        self.log_collection = new ContentLogCollection([], {content_model: self.data_model});
                        self.log_collection.fetch().then(self.user_data_loaded);

                    }
                });
            }

        });

    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.audio_object = audiojs.create(this.$("audio"))[0];

        this.starting_points = this.log_model.get("points");

        this.initialize_listeners();

    },

    initialize_listeners: function() {

        // Dummy for now.

    },


    close: function() {
        this.remove();
    }

});