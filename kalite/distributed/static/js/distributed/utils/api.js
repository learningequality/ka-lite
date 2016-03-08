var get_params = require("./get_params");
var $ = require("../base/jQuery");
var messages_utils = require("./messages");
var sprintf = require("sprintf-js").sprintf;
var url_utils = require("url");

function handleSuccessAPI(obj) {

    var messages = null;
    var msg_types = ["success", "info", "warning", "error"];  // in case we need to dig for messages


    if (!obj) {
        return;

    } else if (obj.hasOwnProperty("responseText")) {
        // Got a HTTP response object; parse it.
        try {
            if (obj.responseText) {  // No point in trying to parse empty response (which is common)
                messages = $.parseJSON(obj.responseText);
            }
        } catch (e) {
            // Many reasons this could fail, some valid; others not.
            console.log(e);
        }
    } else if (obj.hasOwnProperty("messages")) {
        // Got messages embedded in the object
        messages = {};
        for (var idx in obj.messages) {
            messages = obj.messages[idx];
        }
    } else {
        // Got messages at the top level of the object; grab them.
        messages = {};
        for (var idy in msg_types) {
            var msg_type = msg_types[idy];
            if (msg_type in obj) {
                messages[msg_type] = obj[msg_type];
                console.log(messages[msg_type]);
            }
        }
    }

    if (messages) {
        messages_utils.show_api_messages(messages);
    }
}

function handleFailedAPI(resp, error_prefix) {
    // Two ways for this function to be called:
    // 1. With an API response (resp) containing a JSON error.
    // 2. With an explicit error_prefix

    // TODO(jamalex): simplify this crud; "error_prefix" doesn't even seem to get used at all?

    // Parse the messages.
    var messages = {};
    switch (resp.status) {
        case 0:
            messages = {error: gettext("Connecting to the server.") + " " + gettext("Please wait...")};
            break;
        
        case 401:

        case 403:
            messages = {error: gettext("You are not authorized to complete the request.  Please login as an authorized user, then retry the request.")};
            if (window.statusModel) {
                window.toggleNavbarView.userView.login_start_open = true;
                window.statusModel.fetch();
            }
            break;

        default:

            try {
                messages = $.parseJSON(resp.responseText || "{}").messages || $.parseJSON(resp.responseText || "{}");
            } catch (e) {
                // Replacing resp.responseText with "There was an unexpected error!" is just a workaround... this should be fixed.
                // See https://github.com/learningequality/ka-lite/issues/4203
                var error_msg = sprintf("%s<br/>%s<br/>%s", resp.status, "There was an unexpected error!", resp);
                messages = {error: sprintf(gettext("Unexpected error; contact the FLE with the following information: %(error_msg)s"), {error_msg: error_msg})};
                console.log("Response text: " + resp.responseText);
                console.log(e);
            }
            break;
    }

    messages_utils.clear_messages();  // Clear all messages before showing the new (error) message.
    messages_utils.show_api_messages(messages);
}

function doRequest(url, data, opts) {
    // If locale is not already set, set it to the current language.
    var query;

    if ((query = url_utils.parse(url).query) === null) {
      query = {};
    }

    if (query.lang === undefined && data !== null && data !== undefined) {
        if (!data.hasOwnProperty('lang')) {
            url = get_params.setGetParam(url, "lang", window.sessionModel.get("CURRENT_LANGUAGE"));
        }
    }

    var request_options = {
        url: url,
        type: data ? "POST" : "GET",
        data: data ? JSON.stringify(data) : "",
        contentType: "application/json",
        dataType: "json"
    };
    var error_prefix = "";

    for (var opt_key in opts) {
        switch (opt_key) {
            case "error_prefix":  // Set the error prefix on a failure.
                error_prefix = opts[opt_key];
                break;
            default:  // Tweak the default options
                request_options[opt_key] = opts[opt_key];
                break;
        }
    }
    // TODO-BLOCKER (rtibbles): Make setting of the success and fail callbacks more flexible.
    return $.ajax(request_options)
        .success(function(resp) {
            handleSuccessAPI(resp);
        })
        .fail(function(resp) {
            handleFailedAPI(resp, error_prefix);
        });
}

module.exports = {
    handleSuccessAPI: handleSuccessAPI,
    handleFailedAPI: handleFailedAPI,
    doRequest: doRequest
};