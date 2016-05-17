var ContentBaseView = require("content/baseview");
//var soundManager = require("soundmanager2").soundManager;
var soundManager = require("../../../js/distributed/vectorvideo/soundmanager2_dev.js").soundManager;
var Paper = require("../../../../../../node_modules/paper/dist/paper-full.min.js");
require("../../../js/distributed/vectorvideo/material.min.css");
require("../../../js/distributed/vectorvideo/material.min.js");
require("../../../css/distributed/vectorvideo.less");
var sample_json = require("../../../js/distributed/vectorvideo/sample_json.json");
var vtt = require("../../../js/distributed/vectorvideo/vtt.min");


var VectorVideoView = ContentBaseView.extend({
    template: require("./hbtemplates/video-vectorization.handlebars"),
    events: {
        "click .vector_play_pause_btn": "clicked_play_pause_btn",
        "click .vector_replay_btn": "clicked_replay_btn",
        "input .vector_seeker": "adjusted_seeker",
        "click .vector_settings_btn": "clicked_settings_btn",
        "click .vector_playback_rate_item": "clicked_playback_rate_item",
        "click .vector_zoom_level_item": "clicked_zoom_level_item",
        "click .vector_cc_menu_item": "clicked_cc_menu_item",
        "click .vector_voice_menu_item": "clicked_voice_menu_item",
        "click .vector_volume_btn": "clicked_volume_btn",
        "click .vector_full_screen_btn": "clicked_full_screen_btn"
    },

    //TODO: REMOVE USE OF JQUERY IS POSSIBLE, REMOVE UNECESSARY CALLS IN THE RENDER CANVAS FUNCTION> SIMPLIFY THAT FUNCTION

    /********************EVENT HANDLERS********************/

    /**
     * Handles clicking the play/pause button .
     */
    clicked_play_pause_btn: function () {
        this.toggle_audio_pause();
        this.cancel_voice();
        this.reset_voice_time_index();
    },


    /**
     * Handles clicking the replay button.
     */
    clicked_replay_btn: function () {
        var new_time = this.get_audio_position_in_sec() - 10;
        if (new_time < 0) {
            this.set_audio_position(0);
        } else {
            this.set_audio_position(new_time * 1000);
        }
    },


    /**
     * Handles adjusting the seeker.
     */
    adjusted_seeker: function () {
        this.set_audio_position_percent(document.querySelector('.vector_seeker').value / document.querySelector('.vector_seeker').max);
        this.reset_voice();
    },

    /**
     *
     */
    clicked_settings_btn: function () {
        $(".vector_settings").toggle();
        $(".vector_settings_btn").toggleClass("vector_settings_btn_exit");
    },

    /**
     * Handles clicking on playback rate item.
     * @param e - The playback rate selected.
     */
    clicked_playback_rate_item: function (e) {
        this.set_audio_playback_rate(parseFloat(e.target.dataset.rate));
    },


    /**
     * Handles clicking on the zoom button.
     */
    clicked_zoom_level_item: function (e) {
        var zoom_level = parseFloat(e.target.dataset.zoom);
        this.zoom_level = zoom_level;
        this.paper_scope.view.zoom = this.zoom_level;
        this.reset_canvas_center();
        this.resize_canvas();
        if (zoom_level == 1.0) {
            this.zoom_enabled = false;
            $('.vector_zoom_level_btn').removeClass('vector_zoom_level_btn_on');
        } else {
            this.zoom_enabled = true;
            $('.vector_zoom_level_btn').addClass('vector_zoom_level_btn_on');
        }
    },


    /**
     * Handles clicking on a cc language item.
     * @param e - The cc language element selected.
     */
    clicked_cc_menu_item: function (e) {
        var that = this;
        this.cc_lang = e.target.dataset.cc;
        document.querySelector('.vector_captions').innerHTML = "";
        if (this.cc_lang == "off") {
            this.cc_on = false;
            $('.vector_cc_btn').removeClass('vector_cc_btn_on');
        } else {
            this.cc_on = true;
            $('.vector_cc_btn').addClass('vector_cc_btn_on');

            var cc_vtt_file = "../static/" + this.cc_lang + ".vtt";
            $.get(cc_vtt_file, function (vtt_file) {
                that.parse_captions(vtt_file, "cc");
            });
        }
    },


    /**
     * Handles clicking on a voice language item.
     * @param e - The voice language element selected.
     */
    clicked_voice_menu_item: function (e) {
        var that = this;
        var voice_lang = e.target.dataset.cc;

        if (voice_lang != this.voice_lang) {
            this.voice_lang = voice_lang;
            this.cancel_voice();
            this.voice_queue = [];

            if (this.voice_lang == "original") {
                this.voice_on = false;
                this.set_audio_volume(100);

                $('.vector_voice_btn').removeClass('vector_voice_btn_on');
            } else {
                this.voice_on = true;
                this.set_audio_volume(0);

                $('.vector_voice_btn').addClass('vector_voice_btn_on');

                var voice_vtt_file = "../static/" + this.voice_lang + ".vtt";
                $.get(voice_vtt_file, function (vtt_file) {
                    that.parse_captions(vtt_file, "voice");
                });
            }
        }
    },


    /**
     * Handles clicking on the volume button.
     */
    clicked_volume_btn: function () {
        if ($(document.querySelector('.vector_volume_label')).hasClass('is-checked')) {
            this.voice_volume = 1;

            if (this.voice_on) {
                this.reset_voice();
            } else {
                this.set_audio_volume(100);
            }

            $('.vector_volume_btn').removeClass('vector_volume_btn_mute');
        }
        else {
            this.voice_volume = 0;
            this.reset_voice();
            this.set_audio_volume(0);

            $('.vector_volume_btn').addClass('vector_volume_btn_mute');
        }
    },


    /**
     * Handles clicking on the full screen button.
     */
    clicked_full_screen_btn: function () {
        if (!document.fullscreenElement && !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {

            this.full_screen_enabled = true;
            $('.vector_full_screen_btn').addClass('vector_full_screen_btn_on');

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
            $('.vector_full_screen_btn').removeClass('vector_full_screen_btn_on');

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


    /********************INITIALIZATION********************/

    /**
     * Initializes.
     * @param options - Options.
     */
    initialize: function (options) {
        ContentBaseView.prototype.initialize.call(this, options);
        _.bindAll(this, "init_audio_object", "check_if_playing", "resize_canvas");
        this.$el.html(this.template(this.data_model.attributes));
        this.init_vars();
        this.init_sound_manager();
        this.paper_scope = new Paper.paper.PaperScope();
    },


    init_vars: function () {
        this.latest_time = 0;
        this.latest_obj = 0;
        this.latest_stroke = 0;
        this.latest_sub_stroke = 0;

        this.zoom_enabled = false;
        this.zoom_level = 1;

        this.full_screen_enabled = false;

        this.cc_on = false;
        this.cc_cues = [];
        this.cc_current_cue_index = 0;
        this.cc_current_cue_end_time = 0;

        this.voice_on = false;
        this.voice_cues = [];
        this.voice_current_cue_index = 0;
        this.voice_current_cue_end_time = 0;
        this.voice_volume = 1;
        this.voice_queue = [];
    },


    /********************UI********************/



    /**
     * Formats milliseconds into a h:m:s format.
     * @param ms Milliseconds
     * @return {string} - Time in a h:m:s format.
     */
    format_time: function (ms) {
        var ns = Math.floor(ms / 1000);
        var hr = Math.floor(ns / 3600);
        var min = Math.floor(ns / 60) - Math.floor(hr * 60);
        var sec = Math.floor(ns - (hr * 3600) - (min * 60));
        return (hr ? hr + ':' : '') + (hr && min < 10 ? '0' + min : min) + ':' + (sec < 10 ? '0' + sec : sec);
    },


    /********************AUDIO********************/

    /**
     * Initializes sound manager.
     */
    init_sound_manager: function () {
        window.soundManager.setup({
            url: window.sessionModel.get("STATIC_URL") + "soundmanager/",
            preferFlash: false,
            debugMode: false,
            html5PollingInterval: 15,
            onready: this.init_audio_object
        });
    },


    /**
     * Initializes audio.
     */
    init_audio_object: function () {
        window.audio_object = this.audio_object = soundManager.createSound({
            url: this.data_model.get("content_urls").stream,
            onload: this.audio_loaded.bind(this),
            onplay: this.audio_played.bind(this),
            onpause: this.audio_paused.bind(this),
            onresume: this.audio_played.bind(this),
            whileplaying: this.audio_playing.bind(this),
            onfinish: this.audio_finished.bind(this)
        });
    },


    /**
     * When the audio loads.
     */
    audio_loaded: function () {
        $(".vector_total_time").text(" / " + this.format_time(this.get_audio_duration()));
    },


    /**
     * When the audio is played.
     */
    audio_played: function () {
        this.data_model.set("is_playing", true);
        $('.vector_play_pause_btn').addClass('vector_play_pause_btn_pause');
        $('.vector_play_pause_btn_overlay').toggleClass('vector_hidden');
    },

    /**
     * Hides the controls.
     */
    hide_controls: function () {

    },


    /**
     * When the audio is paused.
     */
    audio_paused: function () {
        this.data_model.set("is_playing", false);
        $('.vector_play_pause_btn').removeClass('vector_play_pause_btn_pause');
        $('.vector_play_pause_btn_overlay').toggleClass('vector_hidden');
    },


    /**
     * While the audio is playing.
     */
    audio_playing: function () {
        $(".vector_current_time").text(this.format_time(this.get_audio_position()));
        document.querySelector('.vector_seeker').MaterialSlider.change(this.get_audio_position_percent() * document.querySelector('.vector_seeker').max);
    },


    /**
     * When the audio finishes.
     */
    audio_finished: function () {
        this.set_audio_position(0);
        this.audio_paused();
        this.reset_canvas_center();
    },


    /**
     * Gets the total duration of the audio.
     * @returns {number} - The total duration of the audio.
     */
    get_audio_duration: function () {
        return parseInt(this.audio_object.duration);
    },


    /**
     * Gets the current position of the audio.
     * @returns {number} - Current position of the audio.
     */
    get_audio_position: function () {
        return parseInt(this.audio_object.position);
    },


    /**
     * Gets the current position of the audio in seconds.
     * @returns {number} - The position of the audio in seconds.
     */
    get_audio_position_in_sec: function () {
        return (this.get_audio_position()) / 1000;
    },


    /**
     * Sets the position of the audio.
     * @param val - The new desired position of the audio.
     */
    set_audio_position: function (val) {
        this.audio_object.setPosition(val);
    },


    /**
     * Gets the position of the audio in terms of percentage played.
     * @returns {number} - The percentage of the audio played.
     */
    get_audio_position_percent: function () {
        return this.get_audio_position() / this.get_audio_duration();
    },


    /**
     * Sets the position of the audio in terms of percentage played.
     * @param percent - The new desired position on therms of percentage.
     */
    set_audio_position_percent: function (percent) {
        this.set_audio_position(percent * this.get_audio_duration());
    },


    /**
     * Plays or paused the audio.
     */
    toggle_audio_pause: function () {
        this.audio_object.togglePause();
    },


    /**
     * Sets the playback rate of the audio.
     * @param val - The new desired playback rate.
     */
    set_audio_playback_rate: function (val) {
        this.audio_object.setPlaybackRate(val);
        if (val == 1.0) {
            $('.vector_playback_rate_btn').removeClass('vector_playback_rate_btn_on');
        } else {
            $('.vector_playback_rate_btn').addClass('vector_playback_rate_btn_on');
        }
    },


    /**
     * Sets the volume of the audio.
     * @param val - The new desired volume.
     */
    set_audio_volume: function (val) {
        this.audio_object.setVolume(val);
    },


    /********************CANVAS********************/

    /**
     * Initializes the canvas.
     */
    init_canvas: function () {
        this.json_data = sample_json;
        this.modify_json();

        this.paper_scope.setup($(".vector_canvas")[0]);
        this.paper_scope.view.onFrame = this.check_if_playing;
        this.paper_scope.view.onResize = this.resize_canvas;
        this.resize_canvas();
    },


    /**
     * Checks if the audio is playing.
     */
    check_if_playing: function () {
        if (this.data_model.get("is_playing") === true) {
            this.render_canvas();
            if (this.cc_on) {
                this.update_cc();
            }
            if (this.voice_on) {
                this.update_voice();
            }
        }
    },


    /**
     * When the audio is rewinded.
     */
    audio_rewinded: function () {
        this.reset_canvas();
        this.reset_cc();
        this.reset_voice();
    },


    /**
     * Resize the canvas.
     */
    resize_canvas: function () {
        this.reset_canvas();
        var vector_canvas_wrapper = $(".vector_canvas_wrapper");
        this.vector_canvas_wrapper_width = vector_canvas_wrapper.width();
        this.vector_canvas_wrapper_height = vector_canvas_wrapper.height();
        this.paper_scope.view.viewSize = new Paper.Size(this.vector_canvas_wrapper_width, this.vector_canvas_wrapper_height);
    },


    /**
     * Resets the canvas.
     */
    reset_canvas: function () {
        this.latest_time = 0;
        this.latest_obj = 0;
        this.latest_stroke = 0;
        this.latest_sub_stroke = 0;
        this.cursor = null;
        this.paper_scope.project.clear();
        this.add_bg();
    },


    /**
     * Resets the canvas center.
     */
    reset_canvas_center: function () {
        this.paper_scope.view.center = new this.paper_scope.Point(this.paper_scope.view.viewSize.width / 2, this.paper_scope.view.viewSize.height / 2);
    },


    /**
     * Adds the background.
     */
    add_bg: function () {
        var that = this;
        var bg_img = new this.paper_scope.Raster({
            source: '../static/js/distributed/vectorvideo/samp_bg.png'
        });

        bg_img.onLoad = function () {
            bg_img.size = that.paper_scope.view.viewSize;
            bg_img.position = that.paper_scope.view.center;
        };
    },


    /**
     * Adds fps, cursor update rate, exact x and y values of every sub stroke, stroke time start and end times, and sub stroke start times.
     */
    modify_json: function () {
        var data = this.json_data;

        //TODO: ORIGINAL DIMENSIONS SHOULD BE IN THE JSON. HERE I AM ASSUMING 1280 x 720
        this.orig_width = 1280;
        this.orig_height = 720;


        //CALCULATE FPS AND HOW OFTEN, IN TERMS OF TIME, THE CURSOR SHOULD BE UPDATES
        data.actual_fps = data.cursor.length / parseFloat(data.total_time);
        data.cursor_update_rate = parseFloat(data.total_time) / data.cursor.length;


        //LOOP THROUGH ALL OBJECTS
        for (var obj = 0; obj < data.operations.length; obj++) {
            var obj_offset_x = parseInt(data.operations[obj].offset_x);
            var obj_offset_y = parseInt(data.operations[obj].offset_y);
            var obj_start_time = parseFloat(data.operations[obj].start);
            var obj_end_time = parseFloat(data.operations[obj].end);
            //TODO: ADJUST THE OBJECT DURATION BY DIVIDING OR SUBTRACTING BY SOMETHING 0.5 IS JUST A GUESS
            var obj_dur = (obj_end_time - obj_start_time) * 0.5;
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
                    stroke_dist += sub_stroke_dist;

                    //ADD EXACT X AND Y COORDINATES TO EVERY SUB STROKE
                    data.operations[obj].strokes[stroke][sub_stroke].x = obj_offset_x + x_cord;
                    data.operations[obj].strokes[stroke][sub_stroke].y = obj_offset_y + y_cord;

                }

                stroke_distances.push(stroke_dist);
                obj_dist += stroke_dist;
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


    /**
     * Draws the appropriate strokes on the canvas.
     */
    render_canvas: function () {
        var curr_time = this.get_audio_position_in_sec();


        //GET CURRENT WIDTH AND HEIGHT
        var width_adjust = this.vector_canvas_wrapper_width / this.orig_width;
        var height_adjust = this.vector_canvas_wrapper_height / this.orig_height;


        //IF REWINDED
        if (curr_time < this.latest_time) {
            this.audio_rewinded();
        }

        else {
            this.latest_time = curr_time;

            this.render_cursor(width_adjust, height_adjust);

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
                                    sub_stroke_path.strokeWidth = 2;

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


    /**
     * Renders the cursor on the canvas.
     * @param width_adjust - The adjusted width of the canvas.
     * @param height_adjust - The adjusted height of the canvas.
     */
    render_cursor: function (width_adjust, height_adjust) {
        var cursor_index = parseInt((this.latest_time / parseFloat(this.json_data.total_time)) * this.json_data.cursor.length);
        var cursor_x = (parseInt(this.json_data.cursor[cursor_index][0])) * width_adjust;
        var cursor_y = (parseInt(this.json_data.cursor[cursor_index][1])) * height_adjust;

        if (this.cursor) {
            this.cursor.position = new this.paper_scope.Point(cursor_x, cursor_y);
            if (this.zoom_enabled) {
                this.paper_scope.view.center = new this.paper_scope.Point(this.adjust_center_point("x", cursor_x), this.adjust_center_point("y", cursor_y));
            }
        } else {
            this.cursor = new this.paper_scope.Path.Circle(
                {
                    center: new this.paper_scope.Point(cursor_x, cursor_y),
                    radius: 2,
                    fillColor: 'white'
                }
            );
        }
    },


    /**
     * Attempts to find the new best center values for x and y in order to smooth panning.
     * @param x_or_y - Whether this is for x or y.
     * @param next_center_val - The new center value that needs to be adjusted.
     * @returns {number} - The new adjusted center value.
     */
    adjust_center_point: function (x_or_y, next_center_val) {

        //APPROPRIATE VALUES DEPENDING IF X OR Y
        var curr_center_val, total_length, view_port_length;
        if (x_or_y == "x") {
            curr_center_val = this.paper_scope.view.center.x;
            total_length = this.paper_scope.view.viewSize.width;
            view_port_length = this.paper_scope.view.bounds.width;
        } else {
            curr_center_val = this.paper_scope.view.center.y;
            total_length = this.paper_scope.view.viewSize.height;
            view_port_length = this.paper_scope.view.bounds.height;
        }

        // CALCULATES WHAT THE NEW CENTER VALUE SHOULD BE.
        // THE CLOSER THE NEXT CENTER VAL IS TO THE CURRENT CENTER VAL,
        // THE CLOSER THE NEW CENTER SHOULD BE TO THE CURRENT CENTER.
        var diff = next_center_val - curr_center_val;
        var abs_diff = Math.abs(diff);
        var ratio = abs_diff / view_port_length;
        var eased_ratio = this.ease_num(ratio);
        var eased_diff = diff * eased_ratio;
        var new_center_val = curr_center_val + eased_diff;

        //CALCULATE THE END POINTS AND MAKE SURE THEY FALL WITHIN THE BOUNDS.
        var new_view_port_start = new_center_val - (view_port_length / 2);
        var new_view_port_end = new_center_val + (view_port_length / 2);

        if (new_view_port_start < 0) {
            new_view_port_start = 0;
            new_view_port_end = new_view_port_start + view_port_length;
        } else if (new_view_port_end > total_length) {
            new_view_port_end = total_length;
            new_view_port_start = new_view_port_end - view_port_length;
        }

        return (new_view_port_start + new_view_port_end) / 2;
    },


    /**
     * Eases a number using the easeInCubic function.
     * @param t - The number to be eased.
     * @returns {number} The new eased number.
     */
    ease_num: function (t) {
        return t * t * t;
    },


    /********************CLOSED CAPTIONS********************/

    /**
     * Parses the vtt file.
     * @param captions The vtt file that contains the captions.
     * @param cc_or_voice - Whether the captions are for cc or voice.
     */
    parse_captions: function (captions, cc_or_voice) {
        var cues = [];
        var parser = new vtt.WebVTT.Parser(window, vtt.WebVTT.StringDecoder());
        parser.oncue = function (cue) {
            cues.push(cue);
        };
        parser.parse(captions);
        if (cc_or_voice == "cc") {
            this.cc_cues = cues;
            this.cc_current_cue_end_time = 0;
        } else {
            this.voice_cues = cues;
            this.reset_voice_time_index();
        }
    },


    /**
     * Renders the cc.
     */
    update_cc: function () {
        var curr_time = this.get_audio_position_in_sec();
        if (curr_time > this.cc_current_cue_end_time) {
            for (var i = this.cc_current_cue_index; i < this.cc_cues.length; i++) {
                if (this.cc_cues[i].startTime < curr_time &&
                    this.cc_cues[i].endTime > curr_time) {
                    document.querySelector('.vector_captions').innerHTML = this.cc_cues[i].text;
                    this.cc_current_cue_end_time = this.cc_cues[i].endTime;
                    this.cc_current_cue_index = i;
                    return;
                }
            }
        }
    },


    /**
     * Resets the cc.
     */
    reset_cc: function () {
        this.cc_current_cue_index = 0;
        this.cc_current_cue_end_time = 0;
    },


    /********************VOICE********************/

    reset_voice_time_index: function () {
        this.voice_current_cue_end_time = 0;
        this.voice_current_cue_index = 0;
    },


    /**
     * Plays the voice.
     */
    update_voice: function () {
        var curr_time = this.get_audio_position_in_sec();

        if (curr_time > this.voice_current_cue_end_time) {
            for (var i = this.voice_current_cue_index; i < this.voice_cues.length; i++) {
                if ((this.voice_cues[i].startTime < curr_time) &&
                    (this.voice_cues[i].endTime > curr_time)) {
                    var person;
                    switch (this.voice_lang) {
                        case "en":
                            person = "US English Female";
                            break;
                        case "es":
                            person = "Spanish Female";
                            break;
                        default:
                            person = "US English Female";
                            break;
                    }
                    this.voice_queue.push({
                        text: this.voice_cues[i].text,
                        person: person
                    });
                    this.voice_current_cue_end_time = this.voice_cues[i].endTime;
                    this.voice_current_cue_index = i;
                    return;
                }
            }
        }

        //IF QUEUE IS NOT EMPTY AND NOTHING IS PLAY, THEN DEQUEUE AND PLAY
        if ((this.voice_queue.length > 0) && !this.is_voice_playing()) {
            var new_cue = this.voice_queue.shift();
            this.speak(new_cue['text'], new_cue['person'], {rate: 1.3, volume: this.voice_volume}); //SPEED IS JUST AN ESTIMATE
        }
    },


    /**
     * Resets the voice.
     */
    reset_voice: function () {
        this.cancel_voice();
        this.voice_queue = [];
        this.reset_voice_time_index();
    },


    /**
     * Stops the voice.
     */
    cancel_voice: function () {
        responsiveVoice.cancel();
    },


    /**
     * Checks whether the voice is playing.
     * @returns {boolean} Whether the voice is playing or not.
     */
    is_voice_playing: function () {
        return responsiveVoice.isPlaying();
    },


    /**
     *
     * @param text - The text to be spoken.
     * @param person - The person to be used to speak
     * @param settings - Object of other settings such as rate and volume.
     */
    speak: function (text, person, settings) {
        responsiveVoice.speak(text, person, settings);
    }
});

/**
 *
 * @type {{VectorVideoView: *}}
 */
module.exports = {
    VectorVideoView: VectorVideoView
};

