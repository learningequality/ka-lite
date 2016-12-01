var user = require("../user/views");
var $ = require("../base/jQuery");
require('jquery-ui/tooltip');
require('jquery-ui-touch-punch');

var _ = require("underscore");
var messages = require("../utils/messages");
var api = require("../utils/api");
var SessionModel = require("../session/models");
var StatusModel = require("../user/models").StatusModel;
var attachfastclick = require("fastclick");
var $script = require("scriptjs");
require("browsernizr/test/canvas");
require("browsernizr/test/touchevents");
var Modernizr = require("browsernizr");

global.$ = $;
global._ = _;
global.sessionModel = new SessionModel();

$(document).ajaxError(
  function(e, xhr, options) {
    $("#ajax_user_error").show();
  }
);

var url = require("url");

// An object we can use for checking the state of our models and views.
// Be sure to clean up after yourself if you use it, so there's no memory bloat!
window._kalite_debug = {};

window.onerror=function(msg){
    window.js_errors = window.js_errors || [];
    window.js_errors.push(msg);
};

require("jquery-ui/themes/base/jquery-ui.css");

require("bootstrap/dist/js/npm.js");

require("../../../css/distributed/khan-site.css");

// We override introjs.css in khan-lite.less, so load before.
require("intro.js/introjs.css");

require("../../../css/distributed/khan-lite.less");

// Related to showing elements on screen
$(function(){

    if (!Modernizr.canvas) {
        $script(window.sessionModel.get("STATIC_URL") + "js/distributed/bundles/bundle_compatibility.js");
    }

    attachfastclick(document.body);

    // Trigger tooltips for help icons
    $('.help-tooltip').tooltip({
        trigger: "hover click"
    });

    global.statusModel = new StatusModel();
    global.statusModel.fetch_data();
    global.toggleNavbarView = new user.ToggleNavbarView({model: statusModel, el: "#topnav"});

    // Process any direct messages, from the url querystring
    if (url.parse(window.location.href).query) {

        if (url.parse(window.location.href).query.message){

            var message_type = sanitize_string(url.parse(window.location.href).query.message_type || "info");
            var message = sanitize_string(url.parse(window.location.href).query.message);
            var message_id = sanitize_string(url.parse(window.location.href).query.message_id || "");

            messages.show_message(message_type, message, message_id);

        }

    }

    // If new language is selected, redirect after adding django_language session key
    $("#language_selector").change(function() {
        var lang_code = $("#language_selector").val();
        if (lang_code !== "") {
            api.doRequest(global.Urls.set_default_language(),
                      {lang: lang_code}
                     ).success(function() {
                         global.location.reload();
                     });
        }
    });
});
