//Models

window.ContentResumeModel = Backbone.Model.extend({
	defaults: {
		lesson_title: "",
		lesson_description: "blahblah"
	},

	initialize: function() {
        //this.channel = options.channel;
        console.log(this.get('lesson_description'));
    }
});

window.ContentExploreModel = Backbone.Model.extend({
	defaults: {
		lesson_title: "",
		lesson_description: "blahblah"
	},

	initialize: function() {
        //this.channel = options.channel;
        console.log(this.get('lesson_description'));
    }
});

window.ContentExploreLessonModel = Backbone.Model.extend({
	defaults: {
		interest_topic: "geometry",
		lesson_title: "",
		lesson_description: "blahblah"
	},

	initialize: function() {
		console.log(this.get('lesson_description'));
	}
});