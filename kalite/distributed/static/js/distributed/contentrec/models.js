//Models

window.SuggestedContentModel = Backbone.Model.extend({
	defaults: {
		interest_topic: "interest topic",
		lesson_title: "lesson title",
		lesson_description: "lesson description",
		suggested_topic_title: "suggested topic",
		suggested_topic_description: "topic description",
		video_thumbnail: "video thumnail"
	},

	initialize: function() {

	}
});


//Collections

window.SuggestedContentCollection = Backbone.Collection.extend({
	url: '/api/content_recommendation',
	model: SuggestedContentModel
});