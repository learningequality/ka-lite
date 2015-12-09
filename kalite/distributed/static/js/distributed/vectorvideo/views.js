var soundManager = require("soundmanager2").soundManager;
var ContentBaseView = require("content/baseview");
var Handlebars = require("base/handlebars");

require("../../../../../../bower_components/paper/dist/paper-full.min.js");

require("../../../css/distributed/vectorvideo.css");

var VectorVideoView = ContentBaseView.extend({

    template: require("./hbtemplates/video-vectorization.handlebars"),

    events: {
        "click .play-pause": "play_pause_clicked",
        "click .sm2-progress-track": "progress_track_clicked"
    },

    initialize: function(options) {

        ContentBaseView.prototype.initialize.call(this, options);

        _.bindAll(this, "create_audio_object");

    },

    render: function() {

        //_.bindAll(this, "on_resize");

        this.$el.html(this.template(this.data_model.attributes));

        this.initialize_sound_manager();
    },

    initialize_sound_manager: function() {
        var self = this;
        window.soundManager.setup({
          url: window.sessionModel.get("STATIC_URL") + "soundmanager/",
          preferFlash: false,
          onready: self.create_audio_object
        });
        //this.on_resize();
    },

    create_audio_object: function () {
        window.audio_object = this.audio_object = soundManager.createSound({
            url: this.data_model.get("content_urls").stream,
            onload: this.loaded.bind(this),
            onplay: this.played.bind(this),
            onresume: this.played.bind(this),
            onpause: this.paused.bind(this),
            onfinish: this.finished.bind(this),
            whileplaying: this.progress.bind(this)
        });

        this.initialize_listeners();
    },

    /*on_resize: _.throttle(function() {
        var available_width = $(".content-player-container").width();
        var available_height = $(window).height() * 0.9;
        this.set_container_size(available_width, available_height);
    }, 500),

    set_container_size: function(container_width, container_height) {

        var container_ratio = container_width / container_height;

        var width = container_width;
        var height = container_height;

        var ratio = this.data_model.get("width") / this.data_model.get("height");

        console.log(ratio);

        if (container_ratio > ratio) {
            width = container_height * ratio;
        } else {
            height = container_width / ratio;
        }

        if (this.player) {
            console.log("meep");
            this.player.width(width).height(height);
        }

        this.$("#video-player").height(height);
    },
*/
    initialize_listeners: function() {

        var self = this;

        this.$(".sm2-progress-ball").draggable({
            axis: "x",
            start: function() {
                self.dragging = true;
            },
            stop: function(ev) {
                self.dragging = false;
                self.progress_track_clicked({offsetX: self.$(".sm2-progress-ball").position().left});
            }
        }).css("position", "absolute");

        //$(window).resize(this.on_resize);


    },

    content_specific_progress: function(event) {

        var percent = this.audio_object.position / this.audio_object.duration;

        this.log_model.set("last_percent", percent);

        var progress = this.log_model.get("time_spent") / (this.audio_object.duration / 1000);
console.log("here" + progress);
        return progress;

    },

    loaded: function() {
        this.$(".sm2-inline-duration").text(this.get_time(this.audio_object.duration, true));
        if ((this.log_model.get("last_percent") || 0) > 0) {
            this.set_position_percent(this.log_model.get("last_percent"));
        }
    },

    played: function() {
        this.$el.addClass("playing");
        this.activate();
    },

    paused: function() {
        this.$el.removeClass("playing");
        this.deactivate();
    },

    finished: function() {
        this.audio_object.setPosition(0);
        this.paused();
    },

    progress: function() {
        this.update_progress();
        // display the current position time
        this.$(".sm2-inline-time").text(this.get_time(this.audio_object.position, true));
        if (!this.dragging) {
            var left = this.get_position_percent() * this.$(".sm2-progress-track").width();
            this.$(".sm2-progress-ball")[0].style.left = left + "px";
        }
    },

    play_pause_clicked: function() {
        if (this.audio_object.playState === 0) {
            this.audio_object.setPosition(0);
            this.audio_object.play();
        } else if (this.audio_object.paused) {
            this.audio_object.play();
        } else {
            this.audio_object.pause();
        }
    },

    progress_track_clicked: function(ev) {
        this.set_position_percent(ev.offsetX / this.$(".sm2-progress-track").width());
    },

    set_position_percent: function(percent) {
        this.audio_object.setPosition(percent * this.audio_object.duration);
    },

    get_position_percent: function(percent) {
        return this.audio_object.position / this.audio_object.duration;
    },

    get_position: function() {
        return this.audio_object.position;
    },

    get_time: function(msec, use_string) {

        // convert milliseconds to hh:mm:ss, return as object literal or string

        var nSec = Math.floor(msec/1000),
            hh = Math.floor(nSec/3600),
            min = Math.floor(nSec/60) - Math.floor(hh * 60),
            sec = Math.floor(nSec -(hh*3600) -(min*60));

        return (use_string ? ((hh ? hh + ':' : '') + (hh && min < 10 ? '0' + min : min) + ':' + ( sec < 10 ? '0' + sec : sec ) ) : { 'min': min, 'sec': sec });

    },

    close: function() {
        this.audio_object.stop();
        this.audio_object.destruct();
        window.ContentBaseView.prototype.close.apply(this);
    }



});

module.exports = {
    VectorVideoView: VectorVideoView
};