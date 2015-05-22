//Models

window.SuggestedContentModel = Backbone.Model.extend({});


//Collections

window.SuggestedContentCollection = Backbone.Collection.extend({
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
