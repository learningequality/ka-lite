var Backbone = require("../base/backbone");

var RatingModel = Backbone.Model.extend({
    urlRoot: "/api/content_rating",

    initialize: function(){
        _.bindAll(this, "debounced_save");
    },

    debounced_save: _.debounce(function(){
        this.save();
    }, 2000)
});

var ContentRatingCollection = Backbone.Collection.extend({
    model: RatingModel
});

module.exports = {
    "RatingModel": RatingModel,
    "ContentRatingCollection": ContentRatingCollection
};
