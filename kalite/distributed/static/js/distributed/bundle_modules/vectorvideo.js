var $ = require("base/jquery");
var file = require("vectorvideo/views");
var Models = require("content/models");
var data_model = new Models.ContentDataModel({content_urls: {stream: ""}});
var log_model = new Models.ContentLogModel();
var vectorVideoView = new file.VectorVideoView({data_model: data_model, log_model: log_model});
vectorVideoView.render();
console.log(vectorVideoView);
$(function(){
$("#content-area").append(vectorVideoView.el);
});
