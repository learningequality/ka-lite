/**
* This file depends on global js constants defined at the top of base_distributed.html
* and should only be included on pages that inherit from that template.
*/

// Functions related to loading the page

function toggle_state(state, status){
    $("." + (status ? "not-" : "") + state + "-only").hide();
    $("." + (!status ? "not-" : "") + state + "-only").show();
    // Use display block setting instead of inline to prevent misalignment of navbar items.
    $(".nav ." + (!status ? "not-" : "") + state + "-only").css("display", "block");
}

function show_api_messages(messages) {
    // When receiving an error response object,
    //   show errors reported in that object
    if (!messages) {
        return;
    }
    switch (typeof messages) {
        case "object":
            for (var msg_type in messages) {
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


function force_sync() {
    // Simple function that calls the API endpoint to force a data sync,
    //   then shows a message for success/failure
    doRequest(FORCE_SYNC_URL)
        .success(function() {
            var msg = gettext("Successfully launched data syncing job.") + " ";
            msg += sprintf(gettext("After syncing completes, visit the <a href='%(devman_url)s'>device management page</a> to view results."), {
                devman_url: LOCAL_DEVICE_MANAGEMENT_URL
            });
            show_message("success", msg);
        });
}


/**
* Model that holds overall information about the server state or the current user.
*/
var StatusModel = Backbone.Model.extend({

    defaults: {
        points: 0,
        newpoints: 0,
        client_server_time_diff: 0
    },

    url: STATUS_URL,

    initialize: function() {

        _.bindAll(this);

        // save the deferred object from the fetch, so we can run stuff after this model has loaded
        this.loaded = this.fetch();

        this.loaded.then(this.after_loading);

        this.listenTo(this, "change:points", this.update_total_points);
        this.listenTo(this, "change:newpoints", this.update_total_points);

    },

    get_server_time: function () {
        // Function to return time corrected to server clock based on status update.
        return (new Date(new Date() - this.get("client_server_time_diff"))).toISOString().slice(0, -1);
    },

    after_loading: function() {

        var self = this;

        // Add field that quantifies the time differential between client and server.
        // This is the amount that needs to be taken away from client time to give server time.
        // As the server sends its timestamp without a timezone (and we can't rely on timezones
        // being set correctly, we need to do some finagling with the offset to get it to work out.
        var time_stamp = new Date(this.get("status_timestamp"));
        this.set("client_server_time_diff", new Date() - time_stamp.getTime());

        $(function() {
            toggle_state("logged-in", self.get("is_logged_in"));
            toggle_state("registered", self.get("registered"));
            toggle_state("super-user", self.get("is_django_user"));
            toggle_state("teacher", self.get("is_admin") && !self.get("is_django_user"));
            toggle_state("student", !self.get("is_admin") && !self.get("is_django_user") && self.get("is_logged_in"));
            toggle_state("admin", self.get("is_admin")); // combination of teachers & super-users
            $('.navbar-right').show();
        });

        this.update_total_points();

    },

    update_total_points: function() {
        // add the points that existed at page load and the points earned since page load, to get the total current points
        this.set("totalpoints", this.get("points") + this.get("newpoints"));
    }

});

// create a global StatusModel instance to hold shared state, mostly as returned by the "status" api call
window.statusModel = new StatusModel();


/**
 * View that wraps the point display in the top-right corner of the screen, updating itself when points change.
 */
var TotalPointView = Backbone.View.extend({

    initialize: function() {
        _.bindAll(this);
        this.model.bind("change:totalpoints", this.render);
        this.render();
    },

    render: function() {

        var points = this.model.get("totalpoints");
        var message = null;

        // only display the points if they are greater than zero, and the user is logged in
        if (!this.model.get("is_logged_in")) {
            return;
        }

        message = sprintf(gettext("Points: %(points)d "), { points : points });
        if (ds.store.show_store_link_once_points_earned) {
            message += " | <a href='/store/'>Store!</a>";
        }

        this.$el.html(message);
        this.$el.show();
    }

});

var UsernameView = Backbone.View.extend({

    initialize: function() {
        _.bindAll(this);
        this.model.bind("change:username", this.render);
        this.render();
    },

    render: function() {

        var username_span = this.model.get("username");

        // only display the points if they are greater than zero, and the user is logged in
        if (!this.model.get("is_logged_in")) {
            return;
        }

        // TODO-BLOCKER(jamalex): only include the hex user ID when Nalanda package is enabled
        if (this.model.has("user_id")) {
            username_span += sprintf(" (%s)", this.model.get("user_id").slice(0, 8));
        }

        this.$el.html(username_span);
        this.$el.show();
    }

});

function sanitize_string(input_string) {
    return $('<div/>').text(input_string).html();
}

// Related to showing elements on screen
$(function(){

    // create an instance of the total point view, which encapsulates the point display in the top right of the screen
    var usernameView = new UsernameView({model: statusModel, el: "#username"});
    var totalPointView = new TotalPointView({model: statusModel, el: "#points"});

    // For mobile (Bootstrap xs) view
    var totalPointViewXs = new TotalPointView({model: statusModel, el: "#points-xs"});

    // Process any direct messages, from the url querystring
    if ($.url().param('message')) {

        var message_type = sanitize_string($.url().param('message_type') || "info");
        var message = sanitize_string($.url().param('message'));
        var message_id = sanitize_string($.url().param('message_id') || "");

        show_message(message_type, message, message_id);

    }

    // Hide stuff with "-only" classes by default
    //$("[class$=-only]").hide();
});


// Download needed user data and add classes to indicate progress, as appropriate
$(function() {

    // load progress data for all videos linked on page, and render progress circles
    var video_ids = $.map($(".progress-circle[data-video-id]"), function(el) { return $(el).data("video-id"); });
    if (video_ids.length > 0) {
        doRequest(GET_VIDEO_LOGS_URL, video_ids)
            .success(function(data) {
                $.each(data, function(ind, video) {
                    var newClass = video.complete ? "complete" : "partial";
                    $("[data-video-id='" + video.video_id + "']").addClass(newClass);
                });
            });
    }

    // load progress data for all exercises linked on page, and render progress circles
    var exercise_ids = $.map($(".progress-circle[data-exercise-id]"), function(el) { return $(el).data("exercise-id"); });
    if (exercise_ids.length > 0) {
        doRequest(GET_EXERCISE_LOGS_URL, exercise_ids)
            .success(function(data) {
                $.each(data, function(ind, exercise) {
                    var newClass = exercise.complete ? "complete" : "partial";
                    $("[data-exercise-id='" + exercise.exercise_id + "']").addClass(newClass);
                });
            });
    }

});

// Related to language bar function
$(function() {

    // If new language is selected, redirect after adding django_language session key
    $("#language_selector").change(function() {
        var lang_code = $("#language_selector").val();
        if (lang_code != "") {
            doRequest(SET_DEFAULT_LANGUAGE_URL,
                      {lang: lang_code}
                     ).success(function() {
                         window.location.reload();
                     });
        }
    });
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
        data: {fields: (fields || []).join(",")}
    }).success(function(data) {
        callback(data);
    }).fail(function() {
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


// Hides/shows nav bar search input field/button when user clicks on search glyphicon
$(function() {

    var glyphicon_search = $('#glyphicon-search-js'); // Search glyphicon
    var search = $('.search-js'); // Search input field/button

    search.hide(); // Search input field/button are hidden upon page load

    glyphicon_search.click(function() { // When user clicks on search glyphicon,
        if (search.is(':hidden')) { // if search input field/button are hidden,
            search.show(); // search input field/button are displayed;
        } else { // if user clicks on search glyphicon and search input field/button are displayed,
            search.hide(); // search input field/button are hidden.
        }
    });

});
