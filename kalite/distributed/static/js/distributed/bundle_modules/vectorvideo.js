var $ = require("base/jQuery");
var file = require("vectorvideo/views");
var Paper = require("../../../../../../node_modules/paper/dist/paper-full.js");
var Models = require("content/models");

var data_model = new Models.ContentDataModel({
    content_urls: {stream: "https://raw.githubusercontent.com/anuvaradha/ka-lite/vectorization/kalite/distributed/static/js/distributed/vectorvideo/sample_audio.mp3"},
    is_playing: false
});

window.vectorVideoView = new file.VectorVideoView({data_model: data_model});

$(function () {
    $("#content-area").append(vectorVideoView.el);
    vectorVideoView.initialize_canvas();
});
