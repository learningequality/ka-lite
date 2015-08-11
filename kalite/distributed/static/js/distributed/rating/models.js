var Backbone = require("../base/backbone");

var RatingModel = Backbone.Model.extend({
    urlRoot: "/api/content_rating"
});

var ContentRatingCollection = Backbone.Collection.extend({
    model: RatingModel
});

module.exports = {
    "RatingModel": RatingModel,
    "ContentRatingCollection": ContentRatingCollection
}
