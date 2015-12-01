// Model that fetches from tastypie resource "AssessmentDownloadProgress"

var Backbone = require("base/backbone");


var DownloadAssessmentProgressModel = Backbone.Model.extend({
    // urlRoot instead of url since we are using a model outside of a 
    // Backbone collection -- enables the url function to generate URLs 
    urlRoot: '/securesync/api/dl_progress'
    
});

var CreateDeviceAndUserModel = Backbone.Model.extend({
    username: "",
    password: "",
    device_desc: "",
    device_name: "",
});

//module.exports = DownloadAssessmentProgressModel;
module.exports = { 
    DownloadAssessmentProgressModel: DownloadAssessmentProgressModel,
    CreateDeviceAndUserModel: CreateDeviceAndUserModel
};
