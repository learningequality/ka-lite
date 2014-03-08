function assert(val, msg) {
    if (!val) {
        show_message("error", msg, "id_assert");
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

function doRequest(url, data) {
    console.log(url);
    url = setGetParam(url, "lang", CURRENT_LANGUAGE);
    console.log(url);
    return $.ajax({
        url: url,
        type: data ? "POST" : "GET",
        data: data ? JSON.stringify(data) : "",
        contentType: "application/json",
        dataType: "json"
    })
    .fail(function(resp) {
        communicate_api_failure(resp, "id_do_request");
    });
}

// Generic functions for client-side message passing
//   through our Django-based server-side API

function show_message(msg_class, msg_text, msg_id) {
    // This function is generic--can be called with server-side messages,
    //    or to display purely client-side messages.
    // msg_class includes error, warning, and success

    // remove any existing message with the same id
    if (msg_id) {
        clear_message(msg_id);
    }

    x_button = '<a class="close" data-dismiss="alert" href="#">&times;</a>';

    msg_html = "<div class='alert alert-" + msg_class + "'";
    if (msg_id) {
        clear_message(msg_id);
        msg_html += " id='" + msg_id + "'";
    }
    msg_html += ">" + x_button + msg_text + "</div>"
    $("#message_container").append(msg_html);
    return $("#message_container");
}

function clear_message(msg_id) {
    // Clear a single message, by ID
    $("#" + msg_id).remove();
    return $("#message_container");
}

function clear_messages() {
    // Clear all messages
    $("#message_container .message").remove();
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
