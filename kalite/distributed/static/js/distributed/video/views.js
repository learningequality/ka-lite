var _ = require("underscore");
var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");

var vtt = require("videojs-vtt.js");  // Must precede video.js
global.WebVTT = vtt.WebVTT;  // Required to be in the global scope by video.js

var _V_ = require("video.js");
global.videojs = _V_;
require("../../../css/distributed/video-js-override.less");

var ContentBaseView = require("content/baseview");

var VideoPlayerState = {
    UNSTARTED: -1,
    ENDED: 0,
    PLAYING: 1,
    PAUSED: 2,
    BUFFERING: 3,
    VIDEO_CUED: 5
};

var VideoPlayerView = ContentBaseView.extend({

    template: require("./hbtemplates/video-player.handlebars"),

    initialize: function(options) {
        ContentBaseView.prototype.initialize.call(this, options);
        this.flash_only = options.flash_only;
    },


    render: function() {

        _.bindAll(this, "on_resize");

        var that = this;

        this.log_model.set("youtube_id", this.log_model.get("video_id"));
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

        var self = this;

        var player_id = this.$(".video-js").attr("id");

        if (player_id) {
            var video_player_options = {
                "controls": true,
                "playbackRates": [0.5, 1, 1.25, 1.5, 2],
                "html5": {
                    nativeTextTracks: false
                },
                "techOrder": this.flash_only ? ["flash"] : ["html5", "flash"],
                flash: {
                    swf: window.sessionModel.get("STATIC_URL") + "js/distributed/video/video-js.swf"
                }
            };
            if( this.data_model.get("content_urls").thumbnail ) {
                video_player_options['poster'] = this.data_model.get("content_urls").thumbnail;
            }
            this.player = window.player = _V_(player_id, video_player_options);
            this.player.ready(function() {
                window._kalite_debug.video_player_initialized = true;
            });
            this.initialize_listeners();
        } else {
            console.warn("Warning: Could not find Video.JS player!");
        }

        this.data_model.set({width: width, height: height});

        this.on_resize();

    },

    /* Jessica TODO: Use Modernizr to detect when a user is on a tablet, and then apply appropriate CSS changes */
    on_resize: _.throttle(function() {
        var available_width = $(".content-player-container").width();
        var available_height = $(window).height() * 0.9;
        this.set_container_size(available_width, available_height);
    }, 500),

    set_container_size: function(container_width, container_height) {

        var container_ratio = container_width / container_height;

        var width = container_width;
        var height = container_height;

        var ratio = this.data_model.get("width") / (this.data_model.get("height") || 1);

        if (container_ratio > ratio) {
            width = container_height * ratio;
        } else {
            height = container_width / ratio;
        }

        if (this.player) {
            this.player.width(width).height(height);
        }

        this.$("#video-player").height(height);
        this.$(".video-thumb").width(width).height(height);

    },


    initialize_listeners: function() {

        var self = this;

        $(window).resize(this.on_resize);

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
                self.activate();
            })
            .on("pause", function() {
                self.set_player_state(VideoPlayerState.PAUSED);
                self.deactivate();
            })
            .on("timeupdate", function() {
                self.update_progress();
            })
            .on("ended", function() {
                self.set_player_state(VideoPlayerState.ENDED);
            })
            .on("durationchange", function() {

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

        this.log_model.set("total_seconds_watched", this.get_video_position());

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
            // be sure to save the progress if the video has completed
            this.update_progress();
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
        ContentBaseView.prototype.close.apply(this);
    }


});

module.exports = {
    VideoPlayerView: VideoPlayerView
};
