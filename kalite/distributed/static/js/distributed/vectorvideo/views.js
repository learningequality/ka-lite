var soundManager = require("soundmanager2").soundManager;
var ContentBaseView = require("content/baseview");
var Handlebars = require("base/handlebars");
var Paper = require("../../../../../../node_modules/paper/dist/paper-full.min.js");
require("../../../css/distributed/vectorvideo.css");

var sample_json = require("../../../js/distributed/vectorvideo/sample_json.json");

var VectorVideoView = ContentBaseView.extend({
    template: require("./hbtemplates/video-vectorization.handlebars"),


    events: {
        "click .play-pause": "play_pause_clicked",
        "click .sm2-progress-track": "progress_track_clicked"
    },


    initialize: function (options) {
        ContentBaseView.prototype.initialize.call(this, options);

        //TODO: move this to the other place
        this.data_model.set("previous_time", 0);
        this.data_model.set("previous_object", 0);
        this.data_model.set("previous_stroke", 0);
        this.data_model.set("previous_substroke", 0);

        _.bindAll(this, "create_audio_object", "check_if_playing");

        this.render();

        this.paper_scope = new Paper.paper.PaperScope();
    },


    render: function () {
        //_.bindAll(this, "on_resize");

        this.$el.html(this.template(this.data_model.attributes));

        this.$(".papCanvas").attr("id", Math.random().toString());

        this.initialize_sound_manager();
    },


    initialize_canvas: function () {
        this.json_data = sample_json;

        //console.log("ORIGINAL JSON:");
        //console.log(this.json_data);

        this.modify_json();

        //console.log("NEW JSON: ");
        //console.log(this.json_data);

        var papCanvas = this.$(".papCanvas");
        this.paper_scope.setup(papCanvas[0]);

        //TODO - When there are two canvasses, paperscope references the second object
        //It is a problem with paper.js itself. 

        //console.log("Before");
        this.paper_scope.view.onFrame = this.check_if_playing;
        //console.log("After");
    },


    modify_json: function () {
        var data = this.json_data;

        //LOOP THROUGH ALL OBJECTS
        for (var object = 0; object < data.operations.length; object++) {
            var object_start_time = parseFloat(data.operations[object].start);
            var object_end_time = parseFloat(data.operations[object].end);
            var object_duration = object_end_time - object_start_time;
            var object_distance = 0;

            var object_offset_x = parseInt(data.operations[object].offset_x);
            var object_offset_y = parseInt(data.operations[object].offset_y);

            var stroke_distances_array = [];

            //LOOP THROUGH ALL STROKES IN ONE OBJECT
            for (var stroke = 0; stroke < data.operations[object].strokes.length; stroke++) {

                var stroke_distance = 0;

                //LOOP THROUGH ALL SUBSTROKES IN ONE STROKE
                for (var sub_stroke = 0; sub_stroke < data.operations[object].strokes[stroke].length - 1; sub_stroke++) {

                    var x_cord = parseInt(data.operations[object].strokes[stroke][sub_stroke][0]);
                    var y_cord = parseInt(data.operations[object].strokes[stroke][sub_stroke][1]);
                    var x_cord_next = parseInt(data.operations[object].strokes[stroke][(sub_stroke + 1)][0]);
                    var y_cord_next = parseInt(data.operations[object].strokes[stroke][(sub_stroke + 1)][1]);
                    var substroke_distance = Math.sqrt((( x_cord_next - x_cord ) * ( x_cord_next - x_cord)) + (( y_cord_next - y_cord) * ( y_cord_next - y_cord)));
                    stroke_distance = stroke_distance + substroke_distance;

                    //add full x and y to substroke
                    data.operations[object].strokes[stroke][sub_stroke].x = x_cord + object_offset_x;
                    data.operations[object].strokes[stroke][sub_stroke].y = y_cord + object_offset_y;
                }

                object_distance = object_distance + stroke_distance;
                stroke_distances_array.push(stroke_distance);
            }


            for (var i = 0; i < stroke_distances_array.length; i++) {
                var stroke_duration = (parseFloat(stroke_distances_array[i]) / object_distance) * object_duration;
                var stroke_start_time = object_start_time;

                //IF FIRST STROKE
                if (i === 0) {
                    data.operations[object].strokes[i].stroke_start_time = stroke_start_time;
                    data.operations[object].strokes[i].stroke_end_time = object_start_time + stroke_duration;
                }

                else {
                    var before_stroke_start_time = parseFloat(data.operations[object].strokes[i - 1].stroke_start_time);
                    var before_stroke_end_time = parseFloat(data.operations[object].strokes[i - 1].stroke_end_time);
                    data.operations[object].strokes[i].stroke_start_time = stroke_duration + before_stroke_start_time;
                    data.operations[object].strokes[i].stroke_end_time = stroke_duration + before_stroke_end_time;
                }

                //LOOP THROUGH ALL SUBSTROKES and apply easing function
                for (var j = 0; j < data.operations[object].strokes[i].length; j++) {
                    var percent = j / parseFloat(data.operations[object].strokes[i].length);
                    var eased_percent = this.ease(percent);
                    var substroke_start_time = eased_percent * stroke_duration;
                    data.operations[object].strokes[i][j].substroke_start_time = substroke_start_time + stroke_start_time;
                }
            }
        }
    },


    ease: function (t) {
        if (t < 0.5) {
            return 2 * t * t;
        }
        else {
            return -1 + (4 - (2 * t)) * t;
        }
        //SHORT VERSION FOR REFERENCE:
        //return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    },


    check_if_playing: function () {
        var self = this;
        var is_playing = this.data_model.get("is_playing");

        if (is_playing === false) {
            return;
        }

        //playing
        if (is_playing === true) {
            // get time and draw up until this time.
            //console.log("starting to draw");
            self.update_canvas();
        }
        //console.log(this.active);
    },


    update_canvas: function () {
        var current_time = (parseInt(this.get_position())) / 1000;
        var previous_time = this.data_model.get("previous_time");

        var previous_object = this.data_model.get("previous_object");

        var previous_stroke = this.data_model.get("previous_stroke");
        var previous_substroke = this.data_model.get("previous_substroke");

        //IF PLAYING BACKWARDS
        if (current_time < previous_time) {
            //erase canvas
            //reset current object = 0
            //current stroke =0
            //reset substroke to 0
            //previous_time = 0
            this.data_model.set("previous_object", 0);
            this.data_model.set("previous_stroke", 0);
            this.data_model.set("previous_substroke", 0);
            this.data_model.set("previous_time", 0);
            this.paper_scope.project.clear();
        }

        //IF PLAYING FORWARD
        else {
            this.data_model.set("previous_time", current_time);
            //loop through all objects
            //loop through all strokes
            //loop through all substrokes and draw based on start time
            for (var object = previous_object; object < this.json_data.operations.length; object++) {
                var current_object = this.json_data.operations[object];
                var object_color_r = parseInt(current_object.color[0]) / 255;
                var object_color_g = parseInt(current_object.color[1]) / 255;
                var object_color_b = parseInt(current_object.color[2]) / 255;

                for (var stroke = previous_stroke; stroke < this.json_data.operations[object].strokes.length; stroke++) {
                    for (var sub_stroke = previous_substroke; sub_stroke < this.json_data.operations[object].strokes[stroke].length - 1; sub_stroke++) {

                        var sub_stroke_curr = this.json_data.operations[object].strokes[stroke][sub_stroke];

                        var sub_stroke_curr_x = parseFloat(sub_stroke_curr.x);
                        var sub_stroke_curr_y = parseFloat(sub_stroke_curr.y);
                        var sub_stroke_curr_start = parseFloat(sub_stroke_curr.substroke_start_time);

                        if (sub_stroke_curr_start <= current_time) {

                            //x-1 then use x+1
                            //if (wlocation !== undefined)
                            //if next exists aka not the last stroke
                            var path = new this.paper_scope.Path();
                            path.strokeColor = new this.paper_scope.Color(object_color_r, object_color_g, object_color_b);
                            path.add(new this.paper_scope.Point(sub_stroke_curr_x, sub_stroke_curr_y));

                            //if (this.json_data.operations[object].strokes[stroke][sub_stroke + 1]) {
                            var sub_stroke_next = this.json_data.operations[object].strokes[stroke][sub_stroke + 1];
                            var sub_stroke_next_x = parseFloat(sub_stroke_next.x);
                            var sub_stroke_next_y = parseFloat(sub_stroke_next.y);
                            path.add(new this.paper_scope.Point(sub_stroke_next_x, sub_stroke_next_y));

                            this.paper_scope.view.update();

                            this.data_model.set("previous_object", object);
                            this.data_model.set("previous_stroke", stroke);
                            this.data_model.set("previous_substroke", sub_stroke);
                        }
                        else {
                            return;
                        }
                    }
                    this.data_model.set("previous_substroke", 0);
                }
                this.data_model.set("previous_stroke", 0);
            }
        }
    },


    initialize_sound_manager: function () {
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


    initialize_listeners: function () {
        var self = this;
        this.$(".sm2-progress-ball").draggable({
            axis: "x",
            start: function () {
                self.dragging = true;
            },
            stop: function (ev) {
                self.dragging = false;
                self.progress_track_clicked({offsetX: self.$(".sm2-progress-ball").position().left});
            }
        }).css("position", "absolute");
        //$(window).resize(this.on_resize);
    },


    content_specific_progress: function (event) {
        var percent = this.audio_object.position / this.audio_object.duration;
        this.log_model.set("last_percent", percent);
        var progress = this.log_model.get("time_spent") / (this.audio_object.duration / 1000);
        console.log("here" + progress);
        return progress;
    },


    loaded: function () {
        this.$(".sm2-inline-duration").text(this.get_time(this.audio_object.duration, true));
        if ((this.log_model.get("last_percent") || 0) > 0) {
            this.set_position_percent(this.log_model.get("last_percent"));
        }
    },


    played: function () {
        this.$el.addClass("playing");
        this.activate();
        this.data_model.set("is_playing", true);
    },


    paused: function () {
        this.$el.removeClass("playing");
        this.deactivate();
        this.data_model.set("is_playing", false);
    },


    finished: function () {
        this.audio_object.setPosition(0);
        this.paused();
    },


    progress: function () {
        this.update_progress();
        // display the current position time
        this.$(".sm2-inline-time").text(this.get_time(this.audio_object.position, true));
        if (!this.dragging) {
            var left = this.get_position_percent() * this.$(".sm2-progress-track").width();
            this.$(".sm2-progress-ball")[0].style.left = left + "px";
        }
    },


    play_pause_clicked: function () {
        if (this.audio_object.playState === 0) {
            this.audio_object.setPosition(0);
            this.audio_object.play();
        } else if (this.audio_object.paused) {
            this.audio_object.play();
        } else {
            this.audio_object.pause();
        }
    },


    progress_track_clicked: function (ev) {
        this.set_position_percent(ev.offsetX / this.$(".sm2-progress-track").width());
    },


    set_position_percent: function (percent) {
        this.audio_object.setPosition(percent * this.audio_object.duration);
    },


    get_position_percent: function (percent) {
        return this.audio_object.position / this.audio_object.duration;
    },


    get_position: function () {
        return this.audio_object.position;
    },


    get_time: function (msec, use_string) {
        // convert milliseconds to hh:mm:ss, return as object literal or string
        var nSec = Math.floor(msec / 1000),
            hh = Math.floor(nSec / 3600),
            min = Math.floor(nSec / 60) - Math.floor(hh * 60),
            sec = Math.floor(nSec - (hh * 3600) - (min * 60));
        return (use_string ? ((hh ? hh + ':' : '') + (hh && min < 10 ? '0' + min : min) + ':' + ( sec < 10 ? '0' + sec : sec ) ) : {
            'min': min,
            'sec': sec
        });
    },


    close: function () {
        this.audio_object.stop();
        this.audio_object.destruct();
        window.ContentBaseView.prototype.close.apply(this);
    }
});


module.exports = {
    VectorVideoView: VectorVideoView
};
