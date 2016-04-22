//var soundManager = require("soundmanager2").soundManager;
var soundManager = require("../../../js/distributed/vectorvideo/soundmanager2_tester.js").soundManager;
var ContentBaseView = require("content/baseview");
var Handlebars = require("base/handlebars");
var Paper = require("../../../../../../node_modules/paper/dist/paper-full.min.js");
require("../../../js/distributed/vectorvideo/material.min.css");
require("../../../js/distributed/vectorvideo/material.min.js");
require("../../../css/distributed/vectorvideo.less");
var sample_json = require("../../../js/distributed/vectorvideo/sample_json.json");

var VectorVideoView = ContentBaseView.extend({
    template: require("./hbtemplates/video-vectorization.handlebars"),
    events: {
        "click .vector_canvas": "toggle_play_pause",
        "click .vector_play_pause_btn": "toggle_play_pause",
        "click .vector_replay_btn": "replay",
        "input .vector_seek": "seek",
        "click .vector_playback_rate_25": "change_playback_rate",
        "click .vector_playback_rate_50": "change_playback_rate",
        "click .vector_playback_rate_100": "change_playback_rate",
        "click .vector_playback_rate_125": "change_playback_rate",
        "click .vector_playback_rate_150": "change_playback_rate",
        "click .vector_playback_rate_200": "change_playback_rate",
        "click .vector_zoom_input": "toggle_zoom",
        "click .vector_cc_input": "toggle_cc",
        "click .vector_volume_input": "toggle_volume",
        "click .vector_full_screen_input": "toggle_full_screen"
    },

    /////////////EVENTS FUNCTIONS//////////////////////////////

    toggle_play_pause: function () {
        if (this.audio_object.playState === 0) {
            this.audio_object.setPosition(0);
            this.audio_object.play();
        } else if (this.audio_object.paused) {
            this.audio_object.play();
        } else {
            this.audio_object.pause();
        }
    },


    replay: function () {
        var curr_time = ((parseInt(this.get_position())) / 1000);
        curr_time = curr_time - 10;
        if (curr_time < 0) {
            curr_time = 0;
        }
        this.set_position(curr_time * 1000);
    },


    seek: function () {
        var seek_value = document.querySelector('.vector_seek').value;
        if (seek_value) {
            this.set_position_percent(seek_value / 1000);
        }
    },


    change_playback_rate: function (e) {
        var new_playback_rate;

        if ($(e.target).hasClass('vector_playback_rate_25')) {
            new_playback_rate = 0.25;
        }
        else if ($(e.target).hasClass('vector_playback_rate_50')) {
            new_playback_rate = 0.5;
        }
        else if ($(e.target).hasClass('vector_playback_rate_125')) {
            new_playback_rate = 1.25;
        }
        else if ($(e.target).hasClass('vector_playback_rate_150')) {
            new_playback_rate = 1.5;
        }
        else if ($(e.target).hasClass('vector_playback_rate_200')) {
            new_playback_rate = 2;
        }
        else {
            new_playback_rate = 1;
        }

        this.audio_object.setPlaybackRate(new_playback_rate);
    },


    toggle_zoom: function () {
        if (this.zoom_enabled) {
            this.zoom_level = 1;
            this.paper_scope.view.zoom = this.zoom_level;
            this.zoom_enabled = false;
            this.paper_scope.view.center = new this.paper_scope.Point(this.paper_scope.view.viewSize.width / 2, this.paper_scope.view.viewSize.height / 2);
            this.resize_canvas(false);
        }
        else {
            this.zoom_level = 2;
            this.paper_scope.view.zoom = this.zoom_level;//depend on zoom level
            this.zoom_enabled = true;
        }
    },


    toggle_cc: function () {
        console.log("toggle_cc");
    },


    toggle_volume: function () {
        if ($(document.querySelector('.vector_volume_label')).hasClass('is-checked')) {
            this.audio_object.setVolume(100);
        }
        else {
            this.audio_object.setVolume(0);
        }
    },


    toggle_full_screen: function () {
        if (!document.fullscreenElement && !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {

            this.full_screen_enabled = true;
            var el = document.querySelector('.vector_wrapper');

            if (el.requestFullscreen) {
                el.requestFullscreen();
            } else if (el.msRequestFullscreen) {
                el.msRequestFullscreen();
            } else if (el.mozRequestFullScreen) {
                el.mozRequestFullScreen();
            } else if (el.webkitRequestFullscreen) {
                el.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
            }
        } else {
             
            this.full_screen_enabled = false;

            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
        }
    },


    ////////////////////INITIALIZATION////////////////////////////

    initialize: function (options) {
        ContentBaseView.prototype.initialize.call(this, options);
        _.bindAll(this, "init_audio_object", "check_if_playing", "resize_canvas", "toggle_zoom");
        this.render();
        this.paper_scope = new Paper.paper.PaperScope();


        //TODO: MOVE THIS ELSEWHERE
        var vector_bar_items;
        window.onload = function () {
            vector_bar_items = $('.vector_bar_items').width();
            adjust_bar_width();
            $('.mdl-slider__background-flex').css('width', 'calc(100% - 52px');
        };
        $(window).resize(function () {
            adjust_bar_width();
        });
        function adjust_bar_width() {
            $('.vector_seek_wrapper').width($('.vector_bar').width() - vector_bar_items - 1);
        }
    },


    render: function () {
        this.$el.html(this.template(this.data_model.attributes));
        this.init_sound_manager();

        this.latest_time = 0;
        this.latest_obj = 0;
        this.latest_stroke = 0;
        this.latest_sub_stroke = 0;

        this.zoom_enabled = false;
        this.zoom_level = 1;
        this.full_screen_enabled = false;
    },


//////////////////////////AUDIO/////////////////////////////////

    init_sound_manager: function () {
        window.soundManager.setup({
            url: window.sessionModel.get("STATIC_URL") + "soundmanager/",
            preferFlash: false,
            debugMode: false,
            html5PollingInterval: 15,
            onready: this.init_audio_object
        });
    },


    init_audio_object: function () {
        window.audio_object = this.audio_object = soundManager.createSound({
            url: this.data_model.get("content_urls").stream,
            onload: this.loaded.bind(this),
            onplay: this.played.bind(this),
            onpause: this.paused.bind(this),
            onresume: this.played.bind(this),
            whileplaying: this.playing.bind(this),
            onfinish: this.finished.bind(this)
        });
    },


    loaded: function () {
        $(".vector_total_time").text(this.format_time(this.audio_object.duration, true));
    },


    played: function () {
        this.data_model.set("is_playing", true);
        $('.vector_play_pause_btn').addClass('vector_play_pause_btn_pause');
    },


    paused: function () {
        this.data_model.set("is_playing", false);
        $('.vector_play_pause_btn').removeClass('vector_play_pause_btn_pause');
    },


    playing: function () {
        $(".vector_current_time").text(this.format_time(this.audio_object.position, true));
        if (this.get_position_percent()) {
            document.querySelector('.vector_seek').MaterialSlider.change(this.get_position_percent() * 1000);
        }
    },


    finished: function () {
        this.audio_object.setPosition(0);
        this.paused();
    },


    set_position: function (val) {
        this.audio_object.setPosition(val);
    },


    get_position: function () {
        return this.audio_object.position;
    },


    set_position_percent: function (percent) {
        this.audio_object.setPosition(percent * this.audio_object.duration);
    },


    get_position_percent: function () {
        return this.audio_object.position / this.audio_object.duration;
    },


    format_time: function (msec, use_string) {
        // convert milliseconds to hh:mm:ss, return as object literal or string
        var nSec = Math.floor(msec / 1000);
        var hh = Math.floor(nSec / 3600);
        var min = Math.floor(nSec / 60) - Math.floor(hh * 60);
        var sec = Math.floor(nSec - (hh * 3600) - (min * 60));
        return (use_string ? ((hh ? hh + ':' : '') + (hh && min < 10 ? '0' + min : min) + ':' + (sec < 10 ? '0' + sec : sec)) : {
            'min': min,
            'sec': sec
        });
    },


////////////////////CANVAS///////////////////////////////

    init_canvas: function () {
        this.json_data = sample_json;
        this.modify_json();

        this.paper_scope.setup($(".vector_canvas")[0]);
        this.paper_scope.view.onFrame = this.check_if_playing;
        this.paper_scope.view.onResize = this.resize_canvas;
        this.resize_canvas();
    },


    resize_canvas: function (call_clear_canvas) {
        this.paper_scope.view.viewSize = new Paper.Size($(".vector_canvas_wrapper").width(), $(".vector_canvas_wrapper").height());

        if (call_clear_canvas) {
            this.clear_canvas();
        }
    },


    clear_canvas: function () {
        this.latest_obj = 0;
        this.latest_stroke = 0;
        this.latest_sub_stroke = 0;
        this.latest_time = 0;
        this.cursor = null;
        this.paper_scope.project.clear();
        this.add_desc();
    },


    add_desc: function () {
        var text = new this.paper_scope.PointText(new this.paper_scope.Point(30, 40));
        text.fillColor = 'yellow';
        text.content = 'Find the value of 5^3';
        text.fontSize = 20;
    },


    modify_json: function () {
        var data = this.json_data;

        //TODO: ORIGINAL DIMENSIONS SHOULD BE IN THE JSON. HERE I AM ASSUMING 1280 x 720
        var orig_width = 1280;
        var orig_height = 720;
        this.data_model.set("orig_width", orig_width);
        this.data_model.set("orig_height", orig_height);


        //CALCULATE FPS AND HOW OFTEN, IN TERMS OF TIME, THE CURSOR SHOULD BE UPDATES
        data.actual_fps = data.cursor.length / parseFloat(data.total_time);
        data.cursor_update_rate = parseFloat(data.total_time) / data.cursor.length;


        //LOOP THROUGH ALL OBJECTS
        for (var obj = 0; obj < data.operations.length; obj++) {
            var obj_offset_x = parseInt(data.operations[obj].offset_x);
            var obj_offset_y = parseInt(data.operations[obj].offset_y);
            var obj_start_time = parseFloat(data.operations[obj].start);
            var obj_end_time = parseFloat(data.operations[obj].end);
            //TODO: ADJUST THE OBJECT DURATION BY DIVIDING OR SUBTRACTING BY SOMETHING
            var obj_dur = (obj_end_time - obj_start_time);
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
                    var sub_stroke_start_time = stroke_dur * ratio;
                    data.operations[obj].strokes[i][j].sub_stroke_start_time = stroke_start_time + sub_stroke_start_time;
                }
            }
        }
    },


    check_if_playing: function () {
        if (this.data_model.get("is_playing") === true) {
            this.update_canvas();
        }
    },


    update_canvas: function () {
        var curr_time = ((parseInt(this.get_position())) / 1000);


        //GET CURRENT WIDTH AND HEIGHT
        var width_adjust = ($(".vector_canvas_wrapper").width()) / this.data_model.get("orig_width");
        var height_adjust = ($(".vector_canvas_wrapper").height()) / this.data_model.get("orig_height");


        //IF REWINDED
        if (curr_time < this.latest_time) {
            this.clear_canvas();
        }

        else {
            this.latest_time = curr_time;


            //UPDATE CURSOR
            var cursor_index = parseInt((this.latest_time / parseFloat(this.json_data.total_time)) * this.json_data.cursor.length);
            var cursor_x = (parseInt(this.json_data.cursor[cursor_index][0])) * width_adjust;
            var cursor_y = (parseInt(this.json_data.cursor[cursor_index][1])) * height_adjust;

            if (!this.cursor) {
                this.cursor = new this.paper_scope.Path.Circle({
                    center: new this.paper_scope.Point(cursor_x, cursor_y),
                    radius: 1,
                    fillColor: 'white'
                });
            } else {
                this.cursor.position = new this.paper_scope.Point(cursor_x, cursor_y);
                if (this.zoom_enabled) {
                    this.paper_scope.view.center = new this.paper_scope.Point(this.adjust_center_x(cursor_x), this.adjust_center_y(cursor_y));
                }
            }


            //UPDATE STROKES
            //LOOP THROUGH OBJECTS
            for (var obj = this.latest_obj; obj < this.json_data.operations.length; obj++) {

                if ((parseFloat(this.json_data.operations[obj].start)) <= this.latest_time) {
                    this.latest_obj = obj;

                    var red = parseInt(this.json_data.operations[obj].color[0]) / 255;
                    var green = parseInt(this.json_data.operations[obj].color[1]) / 255;
                    var blue = parseInt(this.json_data.operations[obj].color[2]) / 255;

                    //LOOP THROUGH STROKES
                    for (var stroke = this.latest_stroke; stroke < this.json_data.operations[obj].strokes.length; stroke++) {

                        if (((parseFloat(this.json_data.operations[obj].strokes[stroke].stroke_start_time)) <= this.latest_time)) {
                            this.latest_stroke = stroke;

                            //LOOP THROUGH SUB STROKES
                            for (var sub_stroke = this.latest_sub_stroke; sub_stroke < this.json_data.operations[obj].strokes[stroke].length - 1; sub_stroke++) {

                                if (((parseFloat(this.json_data.operations[obj].strokes[stroke][sub_stroke].sub_stroke_start_time)) <= this.latest_time)) {

                                    var curr_sub_stroke = this.json_data.operations[obj].strokes[stroke][sub_stroke];
                                    var nxt_sub_stroke = this.json_data.operations[obj].strokes[stroke][sub_stroke + 1];
                                    var curr_sub_stroke_x = parseFloat(curr_sub_stroke.x) * width_adjust;
                                    var curr_sub_stroke_y = parseFloat(curr_sub_stroke.y) * height_adjust;
                                    var nxt_sub_stroke_x = parseFloat(nxt_sub_stroke.x) * width_adjust;
                                    var nxt_sub_stroke_y = parseFloat(nxt_sub_stroke.y) * height_adjust;

                                    //DRAW
                                    var sub_stroke_path = new this.paper_scope.Path.Line((new this.paper_scope.Point(curr_sub_stroke_x, curr_sub_stroke_y)), (new this.paper_scope.Point(nxt_sub_stroke_x, nxt_sub_stroke_y)));
                                    sub_stroke_path.strokeColor = new this.paper_scope.Color(red, green, blue);
                                    sub_stroke_path.strokeCap = 'round';
                                    sub_stroke_path.strokeJoin = 'round';

                                    //IF LAST SUBSTROKE AND LAST STROKE
                                    if ((sub_stroke == this.json_data.operations[obj].strokes[stroke].length - 2) && (stroke == this.json_data.operations[obj].strokes.length - 1)) {
                                        this.latest_sub_stroke = 0;
                                        this.latest_stroke = 0;
                                        this.latest_obj++;
                                    }
                                    //IF JUST LAST SUBSTROKE
                                    else if (sub_stroke == this.json_data.operations[obj].strokes[stroke].length - 2) {
                                        this.latest_sub_stroke = 0;
                                        this.latest_stroke++;
                                    }
                                    else {
                                        this.latest_sub_stroke = sub_stroke + 1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },


    adjust_center_x: function (cursor_x) {
        var new_center_x = cursor_x;
        if (new_center_x < (this.paper_scope.view.viewSize.width * 0.25)) {//depend on zoom level
            new_center_x = (this.paper_scope.view.viewSize.width * 0.25);//depend on zoom level
        } else if (new_center_x > (this.paper_scope.view.viewSize.width * 0.75)) {//depend on zoom level
            new_center_x = (this.paper_scope.view.viewSize.width * 0.75);//depend on zoom level
        }
        var current_center_x = this.paper_scope.view.center.x;
        var dist = Math.abs(new_center_x - current_center_x);//remove abs
        var zoomed_view_width = this.paper_scope.view.viewSize.width / 2;//depend on zoom level
        var ratio = dist / zoomed_view_width;//abs on dist
        var eased_ratio = this.ease_num(ratio);
        var dist_change = dist * eased_ratio;
        var adjusted_new_center_x;
        if (new_center_x - current_center_x >= 0) {
            adjusted_new_center_x = current_center_x + dist_change;//only keep this
        } else {
            adjusted_new_center_x = current_center_x - dist_change;
        }
        return adjusted_new_center_x;//-.5width < 0 -> -0.5
    },


    adjust_center_y: function (cursor_y) {
        var new_center_y = cursor_y;
        if (new_center_y < (this.paper_scope.view.viewSize.height * 0.25)) {//depend on zoom level
            new_center_y = (this.paper_scope.view.viewSize.height * 0.25);//depend on zoom level
        } else if (new_center_y > (this.paper_scope.view.viewSize.height * 0.75)) {//depend on zoom level
            new_center_y = (this.paper_scope.view.viewSize.height * 0.75);//depend on zoom level
        }
        var current_center_y = this.paper_scope.view.center.y;
        var dist = Math.abs(new_center_y - current_center_y);
        var zoomed_view_height = this.paper_scope.view.viewSize.height / 2;//depend on zoom level
        var ratio = dist / zoomed_view_height;
        var eased_ratio = this.ease_num(ratio);
        var dist_change = dist * eased_ratio;
        var adjusted_new_center_y;
        if (new_center_y - current_center_y >= 0) {
            adjusted_new_center_y = current_center_y + dist_change;
        } else {
            adjusted_new_center_y = current_center_y - dist_change;
        }
        return adjusted_new_center_y;
    },


    ease_num: function (t) {
        //below zero return 0
        return t * t * t;
    }
});


module.exports = {
    VectorVideoView: VectorVideoView
};

