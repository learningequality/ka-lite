var _ = require("underscore");
var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");
var Models = require("./models");
var VideoModels = require("video/models");

var AudioPlayerView = require("audio/views");
var VideoPlayerView = require("video/views");
var PDFViewerView = require("pdf/views");
var ContentBaseView = require("./baseview");

var ContentWrapperView = BaseView.extend({

    events: {
        "click .download-link": "set_full_progress"
    },

    template: require("./hbtemplates/content-wrapper.handlebars"),

    initialize: function(options) {

        _.bindAll(this, "user_data_loaded", "set_full_progress", "render", "setup_content_environment");

        var self = this;

        // load the info about the content itself
        this.data_model = new Models.ContentDataModel({id: options.id});
        if (this.data_model.get("id")) {
            this.data_model.fetch().then(function() {
                window.statusModel.loaded.then(self.setup_content_environment);
            });
        }
        
    },

    setup_content_environment: function() {

        // This is a hack to support the legacy VideoLog, separate from other ContentLog
        // TODO-BLOCKER (rtibbles) 0.14: Remove this

        if (this.data_model.get("kind") == "Video") {
            LogCollection = VideoModels.VideoLogCollection;
        } else {
            LogCollection = Models.ContentLogCollection;
        }

        this.log_collection = new LogCollection([], {content_model: this.data_model});

        if (window.statusModel.get("is_logged_in")) {

            this.log_collection.fetch().then(this.user_data_loaded);

        } else {
            this.user_data_loaded();
        }

        this.listenToOnce(window.statusModel, "change:is_logged_in", this.setup_content_environment);

    },

    user_data_loaded: function() {
        this.log_model = this.log_collection.get_first_log_or_new_log();
        this.render();
    },

    set_full_progress: function() {
        if (this.data_model.get("kind") === "Document" && !("PDFJS" in window)) {
            this.content_view.set_progress(1);
            this.content_view.log_model.save();
        }
    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        var ContentView;

        switch(this.data_model.get("kind")) {

            case "Audio":
                ContentView = AudioPlayerView;
                break;

            case "Document":
                if ("PDFJS" in window) {
                    ContentView = PDFViewerView;
                } else {
                    ContentView = ContentBaseView;
                }
                break;

            case "Video":
                ContentView = VideoPlayerView;
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

var ContentPointsView = BaseView.extend({

    template: require("./hbtemplates/content-points.handlebars"),

    initialize: function() {
        this.starting_points = this.model.get("points") || 0;
        this.listenTo(this.model, "change", this.render);
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        window.statusModel.update_total_points(this.model.get("points") - this.starting_points);
        this.starting_points = this.model.get("points");
    }
});

module.exports = {
    ContentWrapperView: ContentWrapperView,
    ContentPointsView: ContentPointsView
}
