var $ = require("../base/jQuery");
var Backbone = require("../base/backbone");


//Models

var SuggestedContentModel = Backbone.Model.extend({});


//Collections

var SuggestedContentCollection = Backbone.Collection.extend({
	initialize: function(models, options) {
		this.filters = $.extend({
			"user": window.statusModel.get("user_id")
		}, options);
	},

	url: function() {
		return window.Urls.content_recommender()+ "?" + $.param(this.filters, true);
	},

	model: SuggestedContentModel
});

module.exports = {
	SuggestedContentModel: SuggestedContentModel,
	SuggestedContentCollection: SuggestedContentCollection
};