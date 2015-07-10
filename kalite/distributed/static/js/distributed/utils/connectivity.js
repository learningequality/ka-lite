// Code related to checking internet connectivity status

var $ = require("../base/jQuery");
var _ = require("underscore");
var toggle_state = require("./toggle_state");

function get_server_status(options, fields, callback) {

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

    var defaults = {
        protocol: "http",
        hostname: "",
        port: 8008,
        path: window.Urls.get_server_info()
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

function check_now_whether_server_is_online(callback) {
    /**
     * This function immediately checks whether the local distributed server has access to the internet.
     *
     * @param {function} A function to handle the callback operation.
     *
     * @return {boolean} The callback function will be passed true if the server is online, and false otherwise.
     */
    get_server_status({}, ["online"], function(data) {
        callback(data["online"] === true);
    });
}

function check_now_whether_client_is_online(callback) {
    /**
     * This function immediately checks whether the client (the user's browser) has direct access to the internet.
     *
     * @param {function} A function to handle the callback operation.
     *
     * @return {boolean} The callback function will be passed true if the client is online, and false otherwise.
     */
    var hostname = window.sessionModel.get("CENTRAL_SERVER_HOST").split(":")[0];
    var port = window.sessionModel.get("CENTRAL_SERVER_HOST").split(":")[1] || null;
    get_server_status({protocol: window.sessionModel.get("SECURESYNC_PROTOCOL"), hostname: hostname, port: port}, [], function(data) {
        callback(data["status"] === "OK");
    });
}

// container for the Deferred objects that will track the progress of the internet connectivity checks
var _online_deferreds = {
    server: null,
    client: null
};

function with_online_status(server_or_client, callback) {
    /**
     * This function checks the online status of either the client or the server, or uses the cached value if it
     * had already checked previously, in which case it calls back immediately.
     *
     * @param {string} Either "server" or "client", to indicate whether to check for the local server or the browser client.
     * @param {function} A function to handle the callback operation.
     *
     * @return {boolean} The callback function will be passed true if the client/server is online, and false otherwise.
     */
    var deferred = _online_deferreds[server_or_client];

    // if we have not yet checked, do the actual check now
    if (!deferred) {

        deferred = _online_deferreds[server_or_client] = $.Deferred();

        var check_function;

        if (server_or_client==="server") {
            check_function = check_now_whether_server_is_online;
        } else if (server_or_client==="client") {
            check_function = check_now_whether_client_is_online;
        }

        check_function(function(is_online) {
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

module.exports = {
    get_server_status: get_server_status,
    check_now_whether_server_is_online: check_now_whether_server_is_online,
    check_now_whether_client_is_online: check_now_whether_client_is_online,
    with_online_status: with_online_status
};