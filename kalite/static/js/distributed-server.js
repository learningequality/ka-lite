/**
* This file depends on global js constants defined at the top of base_distributed.html
* and should only be included on pages that inherit from that template.
*/

// Functions related to loading the page

function toggle_state(state, status){
    $("." + (status ? "not-" : "") + state + "-only").hide();
    $("." + (!status ? "not-" : "") + state + "-only").show();
}

function show_django_messages(messages) {
    // This function knows to loop through the server-side messages,
    //   received in the format from the status object
    for (var mi in messages) {
        show_message(messages[mi]["tags"], messages[mi]["text"]);
    }
}

function show_api_messages(messages, msg_id) {
    // When receiving an error response object,
    //   show errors reported in that object
    if (msg_id) {
        clear_message(msg_id)
    }
    if (!messages) {
        return
    }
    switch (typeof messages) {
        case "object":
            for (msg_type in messages) {
                show_message(msg_type, messages[msg_type], msg_id);
            }
            break;
        case "string":
            // Should throw an exception, but try to handle gracefully
            show_message("info", messages, msg_id);
            break;
        default:
            // Programming error; this should not happen
            throw "do not call show_api_messages object of type " + (typeof messages)
    }
}

function communicate_api_failure(resp, msg_id) {
    // When receiving an error response object,
    //   show errors reported in that object
    var messages = $.parseJSON(resp.responseText);
    show_api_messages(messages, msg_id)
}

$(function(){
    // Do the AJAX request to async-load user and message data
    $("[class$=-only]").hide();
    doRequest("/securesync/api/status")
        .success(function(data){
            toggle_state("logged-in", data.is_logged_in);
            toggle_state("registered", data.registered);
            toggle_state("django-user", data.is_django_user);
            toggle_state("admin", data.is_admin);
            if (data.is_logged_in){
                if (data.is_admin) {
                    $('#logout').text(data.username + " (Logout)");
                }
                else {
                    $('#logged-in-name').text(data.username);
                    if (data.points!=0) {
                        $('#sitepoints').text("Points: " + data.points);
                    }
                }
            }
            show_django_messages(data.messages);
        })
        .fail(function(resp) {
            communicate_api_failure(resp, "id_status")
        });

    // load progress data for all videos linked on page, and render progress circles
    var youtube_ids = $.map($(".progress-circle[data-youtube-id]"), function(el) { return $(el).data("youtube-id") });
    if (youtube_ids.length > 0) {
        doRequest("/api/get_video_logs", youtube_ids)
            .success(function(data) {
                $.each(data, function(ind, video) {
                    var newClass = video.complete ? "complete" : "partial";
                    $("[data-youtube-id='" + video.youtube_id + "']").addClass(newClass);
                });
            })
            .fail(function(resp) {
                communicate_api_failure(resp, "id_student_logs")
            });
    }

    // load progress data for all exercises linked on page, and render progress circles
    var exercise_ids = $.map($(".progress-circle[data-exercise-id]"), function(el) { return $(el).data("exercise-id") });
    if (exercise_ids.length > 0) {
        doRequest("/api/get_exercise_logs", exercise_ids)
            .success(function(data) {
                $.each(data, function(ind, exercise) {
                    var newClass = exercise.complete ? "complete" : "partial";
                    $("[data-exercise-id='" + exercise.exercise_id + "']").addClass(newClass);
                });
            })
            .fail(function(resp) {
                communicate_api_failure(resp, "id_student_logs");
            });
    }

});


// Code related to checking internet connectivity status

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

    var args = $.extend(defaults, options);

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
 * This function immediately checks whether the local distributed server has access to the internet.
 *
 * @param {function} A function to handle the callback operation.
 *
 * @return {boolean} The callback function will be passed true if the server is online, and false otherwise.
 */
function check_now_whether_server_is_online(callback) {
    get_server_status({}, ["online"], function(data) {
        callback(data["online"] === true);
    });
}

/**
 * This function immediately checks whether the client (the user's browser) has direct access to the internet.
 *
 * @param {function} A function to handle the callback operation.
 *
 * @return {boolean} The callback function will be passed true if the client is online, and false otherwise.
 */
function check_now_whether_client_is_online(callback) {
    var hostname = CENTRAL_SERVER_HOST.split(":")[0];
    var port = CENTRAL_SERVER_HOST.split(":")[1] || null;
    get_server_status({protocol: SECURESYNC_PROTOCOL, hostname: hostname, port: port}, [], function(data) {
        callback(data["status"] === "OK");
    });
}

// container for the Deferred objects that will track the progress of the internet connectivity checks
window._online_deferreds = {
    server: null,
    client: null
};

/**
 * This function checks the online status of either the client or the server, or uses the cached value if it
 * had already checked previously, in which case it calls back immediately.
 *
 * @param {string} Either "server" or "client", to indicate whether to check for the local server or the browser client.
 * @param {function} A function to handle the callback operation.
 *
 * @return {boolean} The callback function will be passed true if the client/server is online, and false otherwise.
 */
function with_online_status(server_or_client, callback) {

    var deferred = _online_deferreds[server_or_client];

    // if we have not yet checked, do the actual check now
    if (!deferred) {

        deferred = _online_deferreds[server_or_client] = $.Deferred();

        window["check_now_whether_" + server_or_client + "_is_online"](function(is_online) {
            if (is_online) {
                deferred.resolve();
            } else {
                deferred.reject();
            }
        });
    }

    // when the deferred is resolved (or now, if it's already resolved), call back to indicate we're online
    deferred.done(function() {
        callback(true);
    });

    // when the deferred is rejected (or now, if it's already rejected), call back to indicate we're offline
    deferred.fail(function() {
        callback(false);
    });
}

// automatically detect whether we need to do checks for online status of the server/client, based on whether
// there are any elements on the page with classes that are conditionally displayed depending on online status,
// for example with the "server-online-only" or "not-client-online-only" classes
$(function() {

    _.each(["server", "client"], function(server_or_client) {

        // check for the existence of elements to selectively show based on connectivity
        if ($("." + server_or_client + "-online-only, .not-" + server_or_client + "-online-only").length) {

            // perform the actual check (it will use a cached value if the check has already been done elsewhere)
            with_online_status(server_or_client, function(is_online) {

                // hide and show the elements on the page as needed, based on the online status
                toggle_state(server_or_client + "-online", is_online);

            });
        }
    });

});
