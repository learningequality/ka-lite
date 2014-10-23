window.ContentWrapperView = BaseView.extend({

    template: HB.template("content/content-wrapper"),

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

    user_data_loaded: function() {
        this.log_model = this.log_collection.get_first_log_or_new_log();

        this.render();
    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        var ContentView;

        switch(this.data_model.get("kind")) {

            case "Audio":
                ContentView = AudioPlayerView;
                break;

            case "Document":
                ContentView = PDFViewerView;
                break;
        }

        this.content_view = this.add_subview(ContentView, {
            data_model: this.data_model,
            log_model: this.log_model
        });

        this.content_view.render();

        this.$(".content-player-container").append(this.content_view.el);

        this.points_view = this.add_subview(ContentPointsView, {
            model: this.log_model
        });

        this.points_view.render();

        this.$(".points-wrapper").append(this.points_view.el);

        this.log_model.set("views", this.log_model.get("views") + 1);
    }

});

window.ContentBaseView = BaseView.extend({
    initialize: function(options) {

        _.bindAll(this);

        this.active = false;

        this.possible_points = 500;

        this.REQUIRED_PERCENT_FOR_FULL_POINTS = 0.95;

        this.data_model = options.data_model;
        this.log_model = options.log_model;
    },

    activate: function () {
        this.active = true;
        this.set_last_time();
    },

    deactivate: function () {
        this.active = false;
    },

    set_time_spent: function() {
        var time_now = new Date().getTime();

        var time_engaged = Math.max(0, time_now - this.last_time);
        time_engaged = (isNaN(time_engaged) ? 0 : time_engaged)/1000;

        this.log_model.set({
            time_spent: this.log_model.get("time_spent") + time_engaged
        });

        this.last_time = time_now;
    },

    set_last_time: function() {
        this.last_time = new Date().getTime();
    },

    set_progress: function(progress) {
        if ((progress - (this.log_model.get("completion_counter") || 0)) > this.REQUIRED_PERCENT_FOR_FULL_POINTS) {
            this.log_model.set_complete();
        }
        this.log_model.set({
            points: Math.min(this.possible_points, Math.floor(this.possible_points * progress))
        });
    },

    update_progress: function() {
        if (!window.statusModel.get("is_logged_in") ) {
            return;
        }

        if (window.statusModel.get("is_django_user")) {
            return;
        }

        if (!this.active) {
            return;
        }

        this.set_time_spent();

        var progress = this.content_specific_progress.apply(this, arguments);

        this.set_progress(progress);

        this.log_model.save();
    },

    content_specific_progress: function() {
        return;
    },

    close: function() {
        this.log_model.saveNow();
        this.remove();
    }
});

window.ContentPointsView = BaseView.extend({

    template: HB.template("content/content-points"),

    initialize: function() {
        this.starting_points = this.model.get("points") || 0;
        this.listenTo(this.model, "change", this.render);
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        statusModel.set("newpoints", this.model.get("points") - this.starting_points);
    }
});