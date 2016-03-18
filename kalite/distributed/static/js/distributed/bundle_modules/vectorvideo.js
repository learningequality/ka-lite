var $ = require("base/jQuery");
var file = require("vectorvideo/views");
var Paper = require("../../../../../../node_modules/paper/dist/paper-full.js");
var Models = require("content/models");


var data_model = new Models.ContentDataModel({
    content_urls: {stream: "https://raw.githubusercontent.com/christianmemije/audio_file/master/audio.mp3"},
    is_playing: false
});

var log_model = new Models.ContentLogModel();

window.vectorVideoView = new file.VectorVideoView({data_model: data_model, log_model: log_model});

//vectorVideoView.render();
//console.log(vectorVideoView);

$(function () {
    $("#content-area").append(vectorVideoView.el);
    console.log($(".papCanvas").length);
    vectorVideoView.initialize_canvas();
});

