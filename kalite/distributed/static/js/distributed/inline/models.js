// Model for the inline tutorial system that fetches from tastypie resource "NarrativeResource"

var NarrativeModel = Backbone.Model.extend({
    // urlRoot since we are using a model outside of a backbone collection,
    // enables the url function to generate URLs based on the model id.
    urlRoot: function() {
        console.log("Inside NarrativeModel: urlRoot function");
        console.log("INLINE + THIS.ID");
        console.log('/inline' + this.id);

        return '/api/inline';
    }
});