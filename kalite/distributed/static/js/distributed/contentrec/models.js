//Models

window.SuggestedContentModel = Backbone.Model.extend({});


//Collections

window.SuggestedContentCollection = Backbone.Collection.extend({
	url: '/api/contentrecommender',
	model: SuggestedContentModel
});
