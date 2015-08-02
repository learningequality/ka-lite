// This file provides a thin wrapper around Backbone to customize it for our purposes.

var Backbone = require("backbone");
var _ = require("underscore");
require("./backbone-tastypie.js");

var api = require("../utils/api");

Backbone.$ = require("./jQuery")

// Customize the Backbone.js ajax method to call our success and fail handlers for error display
Backbone.ajax = function() {
    return Backbone.$.ajax.apply(Backbone.$, arguments)
        .success(function(resp) {
            api.handleSuccessAPI(resp);
        })
        .fail(function(resp) {
            api.handleFailedAPI(resp);
        });
};

module.exports = Backbone;