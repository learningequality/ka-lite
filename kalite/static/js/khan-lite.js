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
 * @param {fields} An array of strings. They refer to the extra data that we want from the server. Example ["name", "version"] .
 * @param {function} A function to handle the callback operation.
 *
 * @return {object} Returns a jsonp object containing data from the server. For testing, you can use alert(JSON.stringify(eval(result))).
 *                  The "status" attribute on the returned object will be set to "error" if the connection to the server failed, else "OK".
 */
function get_server_status(options, fields, callback) {

    var defaults = {
        protocol: "http",
        hostname: "",
        port: 8008,
        path: SERVER_INFO_PATH
    };

    var args = $.extend(defaults, options || {});

    // build the prefix only when a hostname was specified
    var prefix = "";
    if (args.hostname) {
        prefix = (args.protocol ? args.protocol + ":" : "") + "//" + args.hostname + (args.port ? ":" + args.port : "");
    }

    // if prefix is empty, gives an absolute (local) url. If prefix, then fully qualified url.
    var request = $.ajax({
        url:  prefix + args.path,
        dataType: args.hostname ? "jsonp" : "json",
        jsonpCallback: "temp_callback", // TODO(jamalex): remove this line once the central server has this endpoint properly running
        data: {fields: (fields || []).join(",")}
    }).success(function(data) {
        callback(data);
    }).error(function() {
        callback({status: "error"});
    });
}

/**
 * This function checks whether the local distributed server has access to the internet.
 *
 * @param {function} A function to handle the callback operation.
 *
 * @return {boolean} The callback function will be passed true if the server is online, and false otherwise.
 */
function check_if_server_is_online(callback) {
    get_server_status({}, ["online"], function(data) {
        callback(data["online"] === true);
    });
}

/**
 * This function checks whether the client (the user's browser) has direct access to the internet.
 *
 * @param {function} A function to handle the callback operation.
 *
 * @return {boolean} The callback function will be passed true if the client is online, and false otherwise.
 */
function check_if_client_is_online(callback) {
    get_server_status({protocol: "https", hostname: CENTRAL_SERVER_HOST, port: null}, [], function(data) {
        callback(data["status"] === "OK");
    });
}


// automatically detect whether we need to do checks for online status of the server/client, and if so, do them
$(function() {

    // if needed on the page, check to see if the local, distributed server is online, and then show/hide elements appropriately
    var $server_online_only = $(".server-online-only");
    if ($server_online_only.length || _.isFunction(window.server_online_status_callback)) {
        check_if_server_is_online(function(server_is_online) {
            $server_online_only.toggle(server_is_online);
            // call a global callback function if it exists, to do custom actions based on whether the server is online or not
            if (_.isFunction(window.server_online_status_callback)) {
                window.server_online_status_callback(server_is_online);
            }
        });
    }

    // if needed on the page, check to see if the client (the user's browser) is online, and then show/hide elements appropriately
    var $client_online_only = $(".client-online-only");
    if ($client_online_only.length || _.isFunction(window.client_online_status_callback)) {
        check_if_client_is_online(function(client_is_online) {
            $client_online_only.toggle(client_is_online);
            // call a global callback function if it exists, to do custom actions based on whether the client is online or not
            if (_.isFunction(window.client_online_status_callback)) {
                window.client_online_status_callback(client_is_online);
            }
        });
    }
});