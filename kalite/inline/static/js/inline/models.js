var Backbone = require("base/backbone");

// Model for the inline tutorial system that fetches from tastypie resource "NarrativeResource"

var NarrativeModel = Backbone.Model.extend({
    // urlRoot since we are using a model outside of a backbone collection,
    // enables the url function to generate URLs based on the model id.
    urlRoot: function() {
        return Urls.narrative("");
    }
});

module.exports = NarrativeModel;