var user = require("../user/views");
var $ = require("../base/jQuery");
var _ = require("underscore");
var messages = require("../utils/messages");
var api = require("../utils/api");
var SessionModel = require("../session/models");
var StatusModel = require("../user/models").StatusModel

global.$ = $;
global._ = _;
global.sessionModel = new SessionModel();

// Related to showing elements on screen
$(function(){

    global.statusModel = new StatusModel();
    global.statusModel.fetch_data();
    global.toggleNavbarView = new user.ToggleNavbarView({model: statusModel, el: "#topnav"});

    // Process any direct messages, from the url querystring
    if ($.url().param('message')) {

        var message_type = sanitize_string($.url().param('message_type') || "info");
        var message = sanitize_string($.url().param('message'));
        var message_id = sanitize_string($.url().param('message_id') || "");

        messages.show_message(message_type, message, message_id);

    }

    // If new language is selected, redirect after adding django_language session key
    $("#language_selector").change(function() {
        var lang_code = $("#language_selector").val();
        if (lang_code != "") {
            api.doRequest(global.Urls.set_default_language(),
                      {lang: lang_code}
                     ).success(function() {
                         global.location.reload();
                     });
        }
    });
});
