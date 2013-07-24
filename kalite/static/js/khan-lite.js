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
$.ajaxSetup({
    cache: false,
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function doRequest(url, data) {
    return $.ajax({
        url: url,
        type: data ? "POST" : "GET",
        data: data ? JSON.stringify(data) : "",
        contentType: "application/json",
        dataType: "json"
    });
}


// Generic functions for client-side message passing
//   through our Django-based server-side API

function show_message(msg_class, msg_text, msg_id) {
    // This function is generic--can be called with server-side messages,
    //    or to display purely client-side messages.
    // msg_class includes error, warning, and success
    
    msg_html = "<div class='message " + msg_class + "'";
    if (msg_id) {
        msg_html += " id='" + msg_id + "'"
    }
    msg_html += ">" + msg_text + "</div>"
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

    var url = base + "?";
    for (key in vars) {
        url += "&" + key + "=" + vars[key];//         + $.param(vars);
    }
    return url
}

function setGetParamDict(href, dict) {
    for (key in dict) {
         href = setGetParam(href, key, dict[key]);
    }
    return href;
}

/**
 * This function gets the status of any KA Lite server. By default it will call the central server.
 *
 * @param {options} An object containing the parameterized options. If omitted, it will use the default options.
 * @param {requested_data} An array of strings. They refer to the extra data that we want from the server. Example ["name", "version"] .
 * @param {function} A function to handle the callback operation.
 *
 * @return {object} Returns a jsonp object containing data from the server or status OK. For testing, you can use alert(JSON.stringify(eval(result))).
 * @return {boolean} If it fails, it will return false.
 */
function get_server_status(options, requested_data, callback) {

    var defaults = {
        protocol : "http",
        hostname : "",
        port: 8008,
        path : "/securesync/api/info"
    };

    var args = $.extend(defaults, options || {});
    // Build the prefix only for absolute urls
    var prefix = "";
    if (args.hostname) {
        prefix = (args.protocol ? args.protocol + ":" : "") + "//" + args.hostname + (args.port ? ":" + args.port : "");
    }

    // If prefix is empty, gives an absolute url.  If prefix, then FQ url
    var request = $.ajax({
            url :  prefix + args.path,
            traditional : true,
            type : "POST",
            dataType : "jsonp",
            data : (requested_data ? {requested_data:JSON.stringify(requested_data)} : ""),
        }).success(function(data) {
            callback(data);
        }).error(function() {
            callback(false);
        });
    window.request = request
}