window.AudioPlayerView = ContentBaseView.extend({

    template: HB.template("audio/audio-player"),

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.audio_object = audiojs.create(this.$("audio"))[0];

        if ((this.log_model.get("last_percent") || 0) > 0) {
            this.audio_object.skipTo(this.log_model.get("last_percent"));
        }

        this.initialize_listeners();
    },

    initialize_listeners: function() {

        var self = this;

        this.listenToDOM(this.audio_object.wrapper, "timeupdate", self.update_progress);
        this.listenToDOM(this.audio_object.wrapper, "play", self.set_last_time);

    },

    update_progress: function(event) {

        ContentBaseView.prototype.update_progress.call(this, arguments);
        
        var percent = event.percent;

        this.log_model.set("last_percent", percent);

        var progress = this.log_model.get("total_time")/this.audio_object.duration;

        this.set_progress(progress);

        this.log_model.save();

    }

});