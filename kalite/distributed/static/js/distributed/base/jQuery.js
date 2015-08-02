// This file provides a thin wrapper around jQuery to customize it for our purposes.

var jQuery = require("jquery");

var get_cookie = require("../utils/get_cookie");

var csrftoken = get_cookie("csrftoken") || "";

// add the CSRF token to all ajax requests
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

jQuery.ajaxSetup({
    cache: false,
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    },
    dataFilter: function(data, type) {
        if (type === "json" && data === "") {
            data = null;
        }
        return data;
    }
});

window.$ = window.jQuery = jQuery;

module.exports = jQuery;