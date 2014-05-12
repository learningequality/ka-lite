window.VideoWrapperView = Backbone.View.extend({

    template: HB.template("video/video-player"),

    initialize: function() {
        this.render();
        // TODO(jamalex): incorporate the logic from initialize_video into this wrapper
        initialize_video(this.model.get("id"), this.model.get("youtube_id"));
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
    }

});

