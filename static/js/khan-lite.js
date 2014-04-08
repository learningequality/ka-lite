function assert(val, msg) {
    if (!val) {
        show_message("error", msg);
    }
}

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// add the CSRF token to all ajax requests
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function doRequest(url, data, opts) {
    // If locale is not already set, set it to the current language.
    if ($.url().param("lang") === undefined) {
        url = setGetParam(url, "lang", CURRENT_LANGUAGE);
    }

    var request_options = {
        url: url,
        type: data ? "POST" : "GET",
        data: data ? JSON.stringify(data) : "",
        contentType: "application/json",
        dataType: "json"
    };
    var error_prefix = "";

    for (opt_key in opts) {
        switch (opt_key) {
            case "error_prefix":  // Set the error prefix on a failure.
                error_prefix = opts[opt_key];
                break;
            default:  // Tweak the default options
                request_options[opt_key] = opts[opt_key];
                break;
        }
    }

    return $.ajax(request_options)
        .success(function(resp) {
            handleSuccessAPI(resp);
        })
        .fail(function(resp) {
            handleFailedAPI(resp, error_prefix);
        });
}

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
        messages = {}
        for (idx in obj.messages) {
            messages = obj.messages[idx];
        }
    } else {
        // Got messages at the top level of the object; grab them.
        messages = {};
        for (idx in msg_types) {
            var msg_type = msg_types[idx];
            if (msg_type in obj) {
                messages[msg_type] = obj[msg_type];
                console.log(messages[msg_type]);
            }
        }
    }

    clear_messages("error");
    if (messages) {
        show_api_messages(messages);
    }
}

function handleFailedAPI(resp, error_prefix) {
    // Two ways for this function to be called:
    // 1. With an API response (resp) containing a JSON error.
    // 2. With an explicit error_prefix

    // Parse the messages.
    var messages = {};
    switch (resp.status) {
        case 0:
            messages = {error: gettext("Could not connect to the server.") + " " + gettext("Please try again later.")};
            break;

        case 200:  // return JSON messages
        case 500:  // also currently return JSON messages
            try {
                messages = $.parseJSON(resp.responseText);
            } catch (e) {
                var error_msg = sprintf("%s<br/>%s<br/>%s", resp.status, resp.responseText, response);
                messages = {error: sprintf(gettext("Unexpected error; contact the FLE with the following information: %(error_msg)"), {error_msg: error_msg})};
                console.log("Response text: " + resp.responseText);
                console.log(e);
            }
            break;
        case 403:
            messages = {error: gettext("You are not authorized to complete the request.  Please <a href='/securesync/login/' target='_blank'>login</a> as an administrator, then retry.")};
            break;

        default:
            console.log(resp);
            var error_msg = sprintf("%s<br/>%s<br/>%s", resp.status, resp.responseText, resp);
            messages = {error: sprintf(gettext("Unexpected error; contact the FLE with the following information: %(error_msg)"), {error_msg: error_msg})};
    }

    clear_messages();  // Clear all messages before showing the new (error) message.
    show_api_messages(messages);
}

function show_api_messages(messages) {
    // When receiving an error response object,
    //   show errors reported in that object
    if (!messages) {
        return;
    }
    switch (typeof messages) {
        case "object":
            for (msg_type in messages) {
                show_message(msg_type, messages[msg_type]);
            }
            break;
        case "string":
            // Should throw an exception, but try to handle gracefully
            show_message("info", messages);
            break;
        default:
            // Programming error; this should not happen
            // NOTE: DO NOT WRAP THIS STRING.
            throw "do not call show_api_messages object of type " + (typeof messages);
    }
}

// Generates a unique ID for each message - No duplicates.
String.prototype.hashCode = function(){
    var hash = 0, i, char;
    if (this.length == 0) return hash;
    for (i = 0, l = this.length; i < l; i++) {
        char  = this.charCodeAt(i);
        hash  = ((hash<<5)-hash)+char;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

// Generic functions for client-side message passing
//   through our Django-based server-side API
function show_message(msg_class, msg_text) {
    // This function is generic--can be called with server-side messages,
    //    or to display purely client-side messages.
    // msg_class includes error, warning, and success

    // remove any existing message with the same id

    var msg_id = msg_text.hashCode();

    // Avoid duplicating the same message by removing
    if (msg_id) {
        $("#" + msg_id).remove();
    }

    x_button = '<a class="close" data-dismiss="alert" href="#">&times;</a>';

    msg_html = "<div class='alert alert-" + msg_class + "'";
    if (msg_id) {
        $("#" + msg_id).remove();
        msg_html += " id='" + msg_id + "'";
    }
    msg_html += ">" + x_button + msg_text + "</div>";
    $("#message_container").append(msg_html);
    return $("#message_container");
}

function clear_messages(msg_type) {
    if (!msg_type) {
        // Clear all messages
        $("#message_container .alert").remove();
    } else {
        $("#message_container .alert-" + msg_type).remove();
    }
    return $("#message_container");
}

function get_message(msg_id) {
    return $("#" + msg_id).text();
}

function setGetParam(href, name, val) {
    // Generic function for changing a querystring parameter in a url
    var vars = {};
    var base = href.replace(/([?].*)$/gi, ""); // no querystring
    var parts = href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m, key, value) {
        vars[key] = value;
    });

    if (val == "" || val == "----" || val === undefined) {
        delete vars[name];
    } else {
        vars[name] = val;
    }

    var url = base;
    var idx = 0;
    for (key in vars) {
        url += (idx == 0) ? "?" : "&";
        url += key + "=" + vars[key];//         + $.param(vars);
        idx++;
    }
    return url;
}

function setGetParamDict(href, dict) {
    for (key in dict) {
         href = setGetParam(href, key, dict[key]);
    }
    return href;
}

var csrftoken = getCookie("csrftoken") || "";

$.ajaxSetup({
    cache: false,
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
