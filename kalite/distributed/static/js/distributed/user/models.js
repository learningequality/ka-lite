var Backbone = require("../base/backbone");
var _ = require("underscore");
var $ = require("../base/jQuery");
var api = require("../utils/api");
var toggle_state = require("../utils/toggle_state");

/**
* Model that holds overall information about the server state or the current user.
*/
var StatusModel = Backbone.Model.extend({

    defaults: {
        points: 0,
        client_server_time_diff: 0
    },

    is_student: function() {
        return this.get("is_logged_in") && !this.get("is_admin");
    },

    urlRoot: function() {
        return window.sessionModel.get("USER_URL");
    },

    url: function () {
        return this.urlRoot() + "status/";
    },

    initialize: function() {

        _.bindAll.apply(_, [this].concat(_.functions(this)));

    },

    fetch_data: function() {
        // save the deferred object from the fetch, so we can run stuff after this model has loaded
        this.loaded = this.fetch();

        this.loaded.then(this.after_loading);
    },

    get_server_time: function () {
        var regex = /(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s[0-9]{2}\s[0-9]{4}\s[0-9]{2}:[0-9]{2}:[0-9]{2}/;
        // Function to return time corrected to server clock based on status update.
        return (new Date(new Date().getTime() - this.get("client_server_time_diff"))).toString().match(regex)[0];
    },

    login: function(username, password, facility, callback) {
        /**
        * login method for StatusModel
        *
        * @method login
        * @param {String} username Username to login with
        * @param {String} password Password with with to login
        * @param {String} facility The id of the facility object to which the facility user belongs
        * @param {Function} callback A callback function
        * Add a callback to allow functions calling this method to
        * the login - failure, success, and particular errors that can be noted on the UI (such as incorrect username)
        */

        var self = this;

        data = {
            username: username || "",
            password: password || "",
            facility: facility || ""
        };

        $.ajax({
            url: self.urlRoot() + "login/",
            contentType: 'application/json',
            dataType: 'json',
            type: 'POST',
            data: JSON.stringify(data),
            // Pass callback to wrapper function to pass the callback argument to the success and fail functions.
            success: self.handle_login_logout_success_with_callback(callback),
            error: self.handle_login_logout_error_with_callback(callback)
        });
    },

    logout: function(callback) {
        var self = this;

        $.ajax({
            url: self.urlRoot() + "logout/",
            contentType: 'application/json',
            dataType: 'json',
            type: 'GET',
            // Pass callback to wrapper function to pass the callback argument to the success and fail functions.
            success: self.handle_login_logout_success_with_callback(callback),
            error: self.handle_login_logout_error_with_callback(callback)
        });
    },

    handle_login_logout_success_with_callback: function(callback) {
        var self = this;
        return function(data, status, response) {
            self.handle_login_logout_success(data, status, response, callback);
        };
    },

    handle_login_logout_success: function(data, status, response, callback) {
        if (data.redirect) {
            response.redirect = data.redirect;
        }
        this.fetch_data();
        if (callback) {
            callback(response);
        } else {
            if (data.redirect) {
                window.location = data.redirect;
            }
        }
    },

    handle_login_logout_error_with_callback: function(callback) {
        var self = this;
        return function(response, status, error) {
            self.handle_login_logout_error(response, status, error, callback);
        };
    },

    handle_login_logout_error: function(response, status, error, callback) {
        if (callback) {
            callback(response);
        } else {
            api.handleFailedAPI(response);
        }
    },

    after_loading: function() {

        var self = this;

        // Add field that quantifies the time differential between client and server.
        // This is the amount that needs to be taken away from client time to give server time.
        // As the server sends its timestamp without a timezone (and we can't rely on timezones
        // being set correctly, we need to do some finagling with the offset to get it to work out.
        var time_stamp = new Date(this.get("status_timestamp"));

        this.set("client_server_time_diff", (new Date()).getTime() - time_stamp.getTime());

        $(function() {
            toggle_state("logged-in", self.get("is_logged_in"));
            toggle_state("registered", self.get("registered"));
            toggle_state("super-user", self.get("is_django_user"));
            toggle_state("teacher", self.get("is_admin") && !self.get("is_django_user"));
            toggle_state("student", !self.get("is_admin") && !self.get("is_django_user") && self.get("is_logged_in"));
            toggle_state("admin", self.get("is_admin")); // combination of teachers & super-users
            $('.navbar-right').show();
        });
    },

    update_total_points: function(points) {
        points = points || 0;
        // add the points that existed at page load and the points earned since page load, to get the total current points
        this.set("points", this.get("points") + points);
    },

    pageType: function() {

        if ( window.location.pathname.search(Urls.coach_reports(window.statusModel.get("zone_id"))) > -1 ) {
            return "teachPage";
        }
        if ( window.location.pathname.search(Urls.learn()) > -1 ) {
            return "learnPage";
        } 
        if ( window.location.pathname.search(Urls.zone_redirect()) > -1 || window.location.pathname.search("/update/") > -1 ) {
            return "managePage";
        }
        
    }

});

module.exports = {
    StatusModel: StatusModel
};