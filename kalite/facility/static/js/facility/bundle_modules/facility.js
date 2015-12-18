$ = require("base/jQuery");
var DatabaseStateModel = require("../models");
var ConfigSettingsView = require("../views").ConfigSettingsView;

$(function(){
   /** var downloadProgModel = new DownloadAssessmentProgressModel();
    var downloadProgView = new DownloadAssessmentProgressView({ 
                                model: downloadProgModel,
                                id: '1234'}); **/
    var configSettingsView = new ConfigSettingsView({ 
        "csrftoken": window.csrftoken,
        "default_hostname": window.default_hostname,
        "need_update": window.need_update
     });
});
