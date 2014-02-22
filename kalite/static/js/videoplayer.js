    window.VideoPlayerState = {
    UNSTARTED: -1,
    ENDED: 0,
    PLAYING: 1,
    PAUSED: 2,
    BUFFERING: 3,
    VIDEO_CUED: 5
};

window.VideoPlayerModel = Backbone.Model.extend({

    REQUIRED_PERCENT_FOR_FULL_POINTS: 0.95,

    defaults: {
        percent_last_saved: 0.0,
        seconds_watched_since_save: 0.0,
        total_seconds_watched: 0.0,
        points: 0,
        possible_points: 750,
        starting_points: 0,
        youtube_id: "",
        video_id: "",
        player_state: VideoPlayerState.UNSTARTED,
        seconds_between_saves: 30,
        percent_between_saves: 0.1
    },

    initialize: function() {
        _.bindAll(this);

        this.pointsSaved = 0;

        this.set({
            wall_time_last_saved: new Date()
        });

        this.fetch();

    },

    fetch: function() {

        var self = this;

        doRequest("/api/get_video_logs", [this.get("video_id")])
            .success(function(data) {
                if (data.length === 0) {
                    return;
                }
                self.set({
                    total_seconds_watched: data[0].total_seconds_watched,
                    points: data[0].points,
                    starting_points: data[0].points,
                    complete: data[0].complete
                });
                self.pointsSaved = data[0].points;
            })
    },

    save: function() {

        var self = this;

        if (this.saving) {
            return;
        }

        this.saving = true;

        this._updateSecondsWatchedSinceSave();

        var lastSavedBeforeError = this.get("wall_time_last_saved");

        data = {
            video_id: this.get("video_id"),
            youtube_id: this.get("youtube_id"),
            seconds_watched: this.get("seconds_watched_since_save"),
            total_seconds_watched: this.get("total_seconds_watched"),
            points: this.get("points")
        }

        var xhr = doRequest("/api/save_video_log", data)
            .success(function(data) {
                self.pointsSaved = data.points;
                self.saving = false;
                // Show all messages in "messages" object
                show_api_messages(data.messages, "id_student_logs");
                // update the top-right points display to show the newly earned points
                userModel.set("newpoints", data.points - self.get("starting_points"));
            })
            .fail(function(resp) {
                self.set({ wall_time_last_saved: lastSavedBeforeError });
                self.saving = false;
            });

        this.set({
            wall_time_last_saved: new Date(),
            percent_last_saved: this.getPercentWatched(),
            seconds_watched_since_save: 0
        });

        return xhr;
    },

    getVideoPosition: function() {
        if (!this.player || !this.player.currentTime) return 0;
        return this.player.currentTime() || 0;
    },

    _updateSecondsWatchedSinceSave: function() {

        var wallTimeCurrent = new Date();
        var wallTimeDelta =
            (wallTimeCurrent - this.get("wallTimeLastPoll")) / 1000.0;
        this.set("wallTimeLastPoll", wallTimeCurrent);

        var videoPositionCurrent = this.getVideoPosition();
        var videoPositionDelta =
             videoPositionCurrent - this.get("videoPositionLastPoll");
        this.set("videoPositionLastPoll", videoPositionCurrent);

        // Estimate the playback speed by taking the ratio of delta
        // API-reported seconds to delta wall clock seconds, and clamp it
        // between [0, 2].
        var speedFactor = Math.max(0,
            Math.min(2.0, videoPositionDelta / wallTimeDelta));

        var secondsWatchedSinceLastPoll = wallTimeDelta * speedFactor;

        var seconds_watched_since_save = this.get("seconds_watched_since_save");

        if (secondsWatchedSinceLastPoll > 0) {
            seconds_watched_since_save += secondsWatchedSinceLastPoll;
            this.set({
                seconds_watched_since_save: seconds_watched_since_save,
                total_seconds_watched: this.get("total_seconds_watched") + secondsWatchedSinceLastPoll
            });
        }

        return seconds_watched_since_save;

    },

    _updatePointsEstimate: function() {

        var duration = this.getDuration();
        if (duration === 0) return;

        var percentTotal = this.get("total_seconds_watched") / duration;
        if (percentTotal > this.REQUIRED_PERCENT_FOR_FULL_POINTS) {
            percentTotal = 1.0;
        }

        var estimate = Math.floor(this.get("possible_points") * percentTotal);

        this.set({ points: estimate });
    },

    /**
     * We want to save no more frequently than every certain percentage of the
     * way through the video, and no more than every certain number of seconds.
     */
    _isAutoSaveIntervalExceeded: function() {
        var secsPercent = this.getDuration() * this.get("percent_between_saves");
        var interval = Math.max(secsPercent, this.get("seconds_between_saves"));
        return this.get("seconds_watched_since_save") > interval;
    },

    updateAndSaveIfNeeded: function() {

        this._updateSecondsWatchedSinceSave();

        // Save after we hit certain intervals of video watching
        if (this._isAutoSaveIntervalExceeded()) {
            this.save();
        } else {
            // If we hit max video points for the first time, force save,
            // since showing estimate might entice user to close the browser
            // thinking they finished (and it not having actually saved).
            var percent = this.getPercentWatched();
            var last_percent = this.get("percent_last_saved");
            var threshold = this.REQUIRED_PERCENT_FOR_FULL_POINTS;
            if (last_percent < threshold && percent >= threshold) {
                this.save();
            } else {
                this._updatePointsEstimate();
            }
        }
    },

    getPercentWatched: function() {

        var duration = this.getDuration();
        if (duration === 0) return 0;

        return Math.min(1.0, this.getVideoPosition() / duration);
    },

    getDuration: function() {

        if (!this.player || !this.player.duration) {
            return 0;
        }

        var duration = this.player.duration() || this.get("duration") || 0;

        return Math.max(0, duration);
    },

    setPlayerState: function(state) {

        this._updateSecondsWatchedSinceSave();
        this._updatePointsEstimate();

        var oldState = this.get("player_state");

        // set player_state attribute on the model, so we maintain current state
        this.set({ player_state: state });

        if (state === VideoPlayerState.ENDED) {
            // save the points if the video has completed
            this.save();
        } else if (state === VideoPlayerState.PAUSED) {
            // whenever video is paused, save points, unless only 1 sec watched
            if (this.get("seconds_watched_since_save") > 1) {
                this.save();
            }
        }

    },

    whenPointsIncrease: function(callback) {
        callback = _.debounce(callback, 500);
        this.bind("change:points", function() {
            var old_points = this.previous("points");
            var points = this.get("points");
            if (points > old_points) {
                callback(points);
            }
        });
    }

});


window.VideoView = Backbone.View.extend({

    _readyDeferred: null,

    initialize: function() {

        _.bindAll(this);

        this._readyDeferred = new $.Deferred();

        this.model = new VideoPlayerModel(this.options);

        this._pointView = new PointView({model: this.model});

        var player_id = this.$(".video-js").attr("id");

        if (player_id) { // if it's using mplayer, there won't be a player here
            this.player = this.model.player = _V_(player_id);
            this._beginIntervalUpdate();
            this._initializeEventListeners();
        }
    },

    _initializeEventListeners: function() {
        
        var self = this;

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
                self.model.setPlayerState(VideoPlayerState.PLAYING);
            })
            .on("pause", function() {
                self.model.setPlayerState(VideoPlayerState.PAUSED);
            })
            // .on("timeupdate", function() {

            // })
            .on("ended", function() {
                self.model.setPlayerState(VideoPlayerState.ENDED);
            })
            .on("durationchange", function() {
                self.model.set("duration", self.player.duration());
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

    setContainerSize: function(container_width, container_height) {

        var container_ratio = container_width / container_height;

        var width = container_width;
        var height = container_height;

        var ratio = this.model.get("width") / this.model.get("height");

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

    _beginIntervalUpdate: function() {
        // Every 10 seconds, update the point estimate, and save if needed
        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = setInterval(this.model.updateAndSaveIfNeeded, 10000);
    },

    /**
     * Adds callback to be invoked when the player is fully loaded and ready.
     */
    whenReady: function(callback) {
        this._readyDeferred.then(callback);
    },

    playerReady: function() {
        this._readyDeferred.resolve();
    },

    play: function() {
        if (this.model.player && this.model.player.play) {
            this.model.player.play();
        }
    },

    pause: function() {
        if (this.model.player && this.model.player.pause) {
            this.model.player.pause();
        }
    },

    seek: function(seconds) {
        this.model.player.currentTime(seconds);
    },

    close: function() {
        if (this.intervalId) clearInterval(this.intervalId);
        this.remove();
    }

});


window.PointView = Backbone.View.extend({
    /*
    Passively display the point count to the user (and listen to changes on the model to know when to update).
    */

    el: ".points-container",

    initialize: function() {

        _.bindAll(this);

        this.model = this.options.model || new VideoPlayerModel(this.options);

        this.model.whenPointsIncrease(this._updatePoints);

    },

    _updatePoints: function(points) {
        this.$(".points").text(points);
        this.$el.toggle(points > 0);
    }

});


function initialize_video(video_id, youtube_id) {

    var create_video_view = _.once(function(width, height) {

        window.videoView = new VideoView({
            el: $("#video-player"),
            video_id: video_id,
            youtube_id: youtube_id,
            width: width,
            height: height
        });

        var resize_video = _.throttle(function() {
            var available_width = $("article").width();
            var available_height = $(window).height() * 0.9;
            videoView.setContainerSize(available_width, available_height);
        }, 500);

        $(window).resize(resize_video);

        resize_video();

    });

    $("video").bind("loadedmetadata", function() {

        var width = $(this).prop("videoWidth");
        var height = $(this).prop("videoHeight");

        create_video_view(width, height);

    });

    $(".video-thumb").load(function() {

        var width = $(".video-thumb").width();
        var height = $(".video-thumb").height();

        create_video_view(width, height);

    });

    $("#launch_mplayer").click(_.throttle(function() {
        // launch mplayer in the background to play the video
        doRequest("/api/launch_mplayer?youtube_id=" + youtube_id)

        // after mplayer closes and focus returns to the website, refresh the points from the server
        $(window).focus(function() {
            $(window).unbind("focus");
            videoView.model.fetch();
        });
        return false;
    }, 5000));

}
