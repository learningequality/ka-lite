window.VideoPlayerState = {
    UNSTARTED: -1,
    ENDED: 0,
    PLAYING: 1,
    PAUSED: 2,
    BUFFERING: 3,
    VIDEO_CUED: 5
};

window.VideoPlayerView = ContentBaseView.extend({

    template: HB.template("video/video-player"),

    render: function() {

        var that = this;

        this.data_model.set("random_id", "video-" + Math.random().toString().slice(2));

        this.$el.html(this.template(this.data_model.attributes));

        this.$("video").bind("loadedmetadata", function() {

            var width = $(this).prop("videoWidth");
            var height = $(this).prop("videoHeight");

            that.initialize_player(width, height);

        });

        this.$(".video-thumb").load(function() {

            var width = $(".video-thumb").width();
            var height = $(".video-thumb").height();

            that.initialize_player(width, height);

        });
    },

    initialize_player: function(width, height) {

        // avoid initializing more than once
        if (this._loaded) {
            return;
        }
        this._loaded = true;

        var player_id = this.$(".video-js").attr("id");

        if (player_id) {
            this.player = this.player = _V_(player_id);
            this.initialize_listeners();
        } else {
            console.warn("Warning: Could not find Video.JS player!");
        }

        this.data_model.set({width: width, height: height});

        this.on_resize();

    },

    on_resize: _.throttle(function() {
        var available_width = $(".content-player-container").width();
        var available_height = $(window).height() * 0.9;
        this.set_container_size(available_width, available_height);
    }, 500),

    set_container_size: function(container_width, container_height) {

        var container_ratio = container_width / container_height;

        var width = container_width;
        var height = container_height;

        var ratio = this.data_model.get("width") / this.data_model.get("height");

        if (container_ratio > ratio) {
            width = container_height * ratio;
        } else {
            height = container_width / ratio;
        }

        if (this.player) {
            this.player.width(width).height(height);
        }

        this.$(".video-thumb").width(width).height(height);

    },


    initialize_listeners: function() {

        var self = this;

        $(window).resize(this.on_resize);
        this.on_resize();

        this.player
            .on("loadstart", function() {

            })
            .on("loadedmetadata", function() {

            })
            .on("loadeddata", function() {

            })
            .on("loadedalldata", function() {

            })
            .on("play", function() {
                self.set_player_state(VideoPlayerState.PLAYING);
            })
            .on("pause", function() {
                self.set_player_state(VideoPlayerState.PAUSED);
            })
            // .on("timeupdate", function() {

            // })
            .on("ended", function() {
                self.set_player_state(VideoPlayerState.ENDED);
            })
            .on("durationchange", function() {
                self.update_progress();
            })
            .on("progress", function() {

            })
            .on("resize", function() {

            })
            .on("volumechange", function() {

            })
            .on("error", function() {

            })
            .on("fullscreenchange", function() {

            });

    },

    content_specific_progress: function(event) {

        var percent = this.get_video_position() / this.get_duration();

        this.log_model.set("last_percent", percent);

        var progress = this.log_model.get("time_spent") / (this.get_duration());

        return progress;

    },

    get_duration: function() {

        if (!this.player || !this.player.duration) {
            return 0;
        }

        var duration = this.player.duration() || this.data_model.get("duration") || 0;

        return Math.max(0, duration);
    },

    get_video_position: function() {
        if (!this.player || !this.player.currentTime) return 0;
        return this.player.currentTime() || 0;
    },

    set_player_state: function(state) {

        // set player_state attribute on the model, so we maintain current state
        this.data_model.set({ player_state: state });

        if (state === VideoPlayerState.ENDED) {
            // save the points if the video has completed
            this.log_model.saveNow();
        }

    },

    play: function() {
        if (this.player && this.player.play) {
            this.player.play();
        }
    },

    pause: function() {
        if (this.player && this.player.pause) {
            this.player.pause();
        }
    },

    seek: function(seconds) {
        this.player.currentTime(seconds);
    },

    close: function() {
        if (this.intervalId) clearInterval(this.intervalId);
        window.ContentBaseView.prototype.close.apply(this);
    }


});