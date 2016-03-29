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
        "click .sm2-progress-track": "progress_track_clicked",
        "click .back_15_sec": "back_15_sec"
    },


    initialize: function (options) {
        ContentBaseView.prototype.initialize.call(this, options);

        _.bindAll(this, "create_audio_object", "check_if_playing");

        this.render();

        this.paper_scope = new Paper.paper.PaperScope();
    },


    render: function () {
        //_.bindAll(this, "on_resize");

        this.$el.html(this.template(this.data_model.attributes));

        this.latest_time = 0;
        this.latest_obj = 0;
        this.latest_stroke = 0;
        this.latest_sub_stroke = 0;
        console.log("make sure this never prints also");

        this.$(".papCanvas").attr("id", Math.random().toString());

        this.initialize_sound_manager();
    },


    initialize_canvas: function () {
        this.json_data = sample_json;

        //console.log("ORIGINAL JSON:");
        //console.log(this.json_data);

        this.modify_json();

        //console.log("NEW JSON: ");
        console.log(this.json_data);

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
        for (var obj = 0; obj < data.operations.length; obj++) {
            var obj_offset_x = parseInt(data.operations[obj].offset_x);
            var obj_offset_y = parseInt(data.operations[obj].offset_y);
            var obj_start_time = parseFloat(data.operations[obj].start);
            var obj_end_time = parseFloat(data.operations[obj].end);
            var obj_dur = obj_end_time - obj_start_time;
            var obj_dist = 0;
            var stroke_distances = [];

            //LOOP THROUGH ALL STROKES IN ONE OBJECT
            for (var stroke = 0; stroke < data.operations[obj].strokes.length; stroke++) {
                var stroke_dist = 0;

                //LOOP THROUGH ALL SUB STROKES IN ONE STROKE
                for (var sub_stroke = 0; sub_stroke < data.operations[obj].strokes[stroke].length - 1; sub_stroke++) {

                    var x_cord = parseInt(data.operations[obj].strokes[stroke][sub_stroke][0]);
                    var y_cord = parseInt(data.operations[obj].strokes[stroke][sub_stroke][1]);
                    var x_cord_nxt = parseInt(data.operations[obj].strokes[stroke][(sub_stroke + 1)][0]);
                    var y_cord_nxt = parseInt(data.operations[obj].strokes[stroke][(sub_stroke + 1)][1]);
                    var sub_stroke_dist = Math.sqrt(Math.pow((x_cord_nxt - x_cord), 2) + Math.pow((y_cord_nxt - y_cord), 2));
                    stroke_dist = stroke_dist + sub_stroke_dist;

                    //ADD EXACT X AND Y COORDINATES TO EVERY SUB STROKE
                    data.operations[obj].strokes[stroke][sub_stroke].x = obj_offset_x + x_cord;
                    data.operations[obj].strokes[stroke][sub_stroke].y = obj_offset_y + y_cord;
                }

                stroke_distances.push(stroke_dist);
                obj_dist = obj_dist + stroke_dist;
            }

            //GO THROUGH ARRAY
            for (var i = 0; i < stroke_distances.length; i++) {
                var stroke_dur = (parseFloat(stroke_distances[i]) / obj_dist) * obj_dur;

                if (i === 0) {
                    data.operations[obj].strokes[i].stroke_start_time = obj_start_time;
                    data.operations[obj].strokes[i].stroke_end_time = obj_start_time + stroke_dur;
                }

                else {
                    data.operations[obj].strokes[i].stroke_start_time = parseFloat(data.operations[obj].strokes[i - 1].stroke_end_time);
                    data.operations[obj].strokes[i].stroke_end_time = parseFloat(data.operations[obj].strokes[i - 1].stroke_end_time) + stroke_dur;
                }

                //LOOP THROUGH ALL SUB STROKES AND ADD SUB STROKE START TIME
                for (var j = 0; j < data.operations[obj].strokes[i].length; j++) {
                    var stroke_start_time = parseFloat(data.operations[obj].strokes[i].stroke_start_time);
                    var ratio = j / parseFloat(data.operations[obj].strokes[i].length);
                    //var eased_ratio = this.ease(ratio);
                    var sub_stroke_start_time = stroke_dur * ratio;
                    data.operations[obj].strokes[i][j].sub_stroke_start_time = stroke_start_time + sub_stroke_start_time;
                }
            }
        }
    },


    ease: function (t) {
        return t;
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
            console.log("Call update_canvas()");
            self.update_canvas();
        }
        //console.log(this.active);
    },


    update_canvas: function () {
        var curr_time = ((parseInt(this.get_position())) / 1000);

        //IF REWINDED
        if (curr_time < this.latest_time) {
            this.latest_obj = 0;
            this.latest_stroke = 0;
            this.latest_sub_stroke = 0;
            this.latest_time = 0;
            this.paper_scope.project.clear();
            console.log("make sure this never prints");
        }

        else {
            this.latest_time = curr_time;

            //LOOP THROUGH OBJECTS
            for (var obj = this.latest_obj; obj < this.json_data.operations.length; obj++) {

                if ((parseFloat(this.json_data.operations[obj].start)) <= this.latest_time) {
                    this.latest_obj = obj;

                    var red = parseInt(this.json_data.operations[obj].color[0]) / 255;
                    var green = parseInt(this.json_data.operations[obj].color[1]) / 255;
                    var blue = parseInt(this.json_data.operations[obj].color[2]) / 255;

                    //LOOP THROUGH STROKES
                    for (var stroke = this.latest_stroke; stroke < this.json_data.operations[obj].strokes.length; stroke++) {

                        if ((parseFloat(this.json_data.operations[obj].strokes[stroke].stroke_start_time)) <= this.latest_time) {
                            this.latest_stroke = stroke;

                            //LOOP THROUGH SUB STROKES
                            for (var sub_stroke = this.latest_sub_stroke; sub_stroke < this.json_data.operations[obj].strokes[stroke].length - 1; sub_stroke++) {

                                if ((parseFloat(this.json_data.operations[obj].strokes[stroke][sub_stroke].sub_stroke_start_time)) <= this.latest_time && sub_stroke) {
                                    this.latest_sub_stroke = sub_stroke;

                                    var curr_sub_stroke = this.json_data.operations[obj].strokes[stroke][sub_stroke];
                                    var nxt_sub_stroke = this.json_data.operations[obj].strokes[stroke][sub_stroke + 1];
                                    var curr_sub_stroke_x = parseFloat(curr_sub_stroke.x);
                                    var curr_sub_stroke_y = parseFloat(curr_sub_stroke.y);
                                    var nxt_sub_stroke_x = parseFloat(nxt_sub_stroke.x);
                                    var nxt_sub_stroke_y = parseFloat(nxt_sub_stroke.y);

                                    //DRAW
                                    var path = new this.paper_scope.Path();
                                    path.strokeColor = new this.paper_scope.Color(red, green, blue);
                                    path.add(new this.paper_scope.Point(curr_sub_stroke_x, curr_sub_stroke_y));
                                    path.add(new this.paper_scope.Point(nxt_sub_stroke_x, nxt_sub_stroke_y));

                                    //TESTING
                                    console.log(obj, stroke, sub_stroke);

                                    //IF LAST SUBSTROKE
                                    if (sub_stroke == this.json_data.operations[obj].strokes[stroke].length - 2) {
                                        this.latest_sub_stroke = 0;
                                    }
                                }
                            }
                            // IF LAST STROKE
                            if (stroke == this.json_data.operations[obj].strokes.length - 1) {
                                this.latest_stroke = 0;
                            }
                        }
                    }
                }
            }
        }
    },

    back_15_sec: function () {
        var curr_time = ((parseInt(this.get_position())) / 1000);
        curr_time = curr_time - 15;
        if (curr_time < 0) {
            curr_time = 0;
        }
        this.set_position(curr_time*1000);
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

    set_position: function (val) {
        this.audio_object.setPosition(val);
    },


    get_time: function (msec, use_string) {
        // convert milliseconds to hh:mm:ss, return as object literal or string
        var nSec = Math.floor(msec / 1000),
            hh = Math.floor(nSec / 3600),
            min = Math.floor(nSec / 60) - Math.floor(hh * 60),
            sec = Math.floor(nSec - (hh * 3600) - (min * 60));
        return (use_string ? ((hh ? hh + ':' : '') + (hh && min < 10 ? '0' + min : min) + ':' + (sec < 10 ? '0' + sec : sec)) : {
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