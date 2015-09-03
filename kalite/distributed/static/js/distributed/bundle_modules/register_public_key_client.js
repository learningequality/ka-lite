var $ = require("../base/jQuery");
var messages = require("../utils/messages");
var api = require("../utils/api");

function reload() {
    window.location.reload();
}

function auto_register() {
    // Disable and show message
    $("#one-click-register").toggleClass("disabled", true);
    messages.show_message("info", gettext("Contacting central server to register; page will reload upon success."));

    // window.auto_registration_url is defined by a template context variable.
    api.doRequest(window.auto_registration_url, null, {dataType: "jsonp"})
        .success(function() {
            messages.show_message("success", "Auto-registered.");
            window.location.reload();
        })
        .fail(function(a, b) {
            // Re-enable
            $("#one-click-register").toggleClass("disabled", false);
        });
}

$(function() {
    $(".refresh-link").click(reload);
    $("#one-click-register").click(auto_register);
});
