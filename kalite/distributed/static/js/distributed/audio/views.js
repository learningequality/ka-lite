window.AudioPlayerView = ContentBaseView.extend({

    template: HB.template("audio/audio-player"),

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.audio_object = soundManager.createSound({
            url: this.data_model.get("content_urls").stream,
        });

        this.audio_object.play();

        // This should be refactored to record 'last_time', rather than last_percent.
        // The 'last_time' (in ms) can then be fed into the setup above as a 'position' argument.
        // if ((this.log_model.get("last_percent") || 0) > 0) {
        //     this.audio_object.skipTo(this.log_model.get("last_percent"));
        // }

        this.initialize_listeners();
    },

    initialize_listeners: function() {

        var self = this;

        // this.listenToDOM(this.audio_object.wrapper, "timeupdate", self.update_progress);
        // this.listenToDOM(this.audio_object.wrapper, "play", self.activate);
        // this.listenToDOM(this.audio_object.wrapper, "pause", self.deactivate);

    },

    content_specific_progress: function(event) {
  
        var percent = event.percent;

        this.log_model.set("last_percent", percent);

        var progress = this.log_model.get("time_spent")/this.audio_object.duration;

        return progress;

    }

});