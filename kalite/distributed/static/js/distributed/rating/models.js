var Backbone = require("../base/backbone");

var RatingModel = Backbone.Model.extend({
    urlRoot: "/api/content_rating"
});

var ContentRatingCollection = Backbone.Collection.extend({
    parse: function(response) {
        console.log("in parse");
        return response.objects;
    },

    model: RatingModel
});

module.exports = {
    "RatingModel": RatingModel,
    "ContentRatingCollection": ContentRatingCollection
}
