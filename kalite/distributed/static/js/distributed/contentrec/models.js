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

window.ContentNextStepsModel = Backbone.Model.extend({
	defaults: {
		lesson_title: "",
		lesson_description: "blahblah"
	},

	initialize: function() {
        //this.channel = options.channel;
        console.log(this.get('lesson_description'));
    }
});

window.ContentNextStepsLessonModel = Backbone.Model.extend({
	defaults: {
		interest_topic: "geometry",
		lesson_title: "Meet the Professional",
		lesson_description: "blahblah"
	},

	initialize: function() {
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

window.ContentExploreTopicModel = Backbone.Model.extend({
	defaults: {
		interest_topic: "geometry",
		lesson_title: "",
		lesson_description: "blahblah"
	},

	initialize: function() {
		console.log(this.get('lesson_description'));
	}
});


//Collections

window.ContentNextStepsCollection = Backbone.Collection.extend({
	model: ContentNextStepsLessonModel
});

window.ContentExploreCollection = Backbone.Collection.extend({
	model: ContentExploreTopicModel
});