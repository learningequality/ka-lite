// Views

/**
 * View that wraps the resume card on the learn page
 */
window.ContentResumeView = BaseView.extend({

    template: HB.template("contentrec/content-resume"),
    
    initialize: function() {
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
    }

});

/**
 * View that wraps a lesson on the next steps card on the learn page
 */
window.ContentNextStepsLessonView = BaseView.extend({

	template: HB.template("contentrec/content-nextsteps-lesson"),

	initialize: function() {
		this.render();
	},

	render: function() {
		this.$el.html(this.template(this.model.attributes));
	}

});

/**
 * View that wraps the next steps card on the learn page
 */
window.ContentNextStepsView = BaseView.extend({

    template: HB.template("contentrec/content-nextsteps"),
    
    initialize: function() {
    	if (typeof this.collection === "undefined") {
    		this.collection = new SuggestedContentCollection([
    			{interest_topic: "Test Topic 1", lesson_title: "Test Lesson Title"},
    			{interest_topic: "Test Topic 2", lesson_title: "Test Lesson Title 2"},
    			{interest_topic: "Test Topic 3", lesson_title: "Test Lesson Title 3"},
    			{interest_topic: "Test Topic 4", lesson_title: "Test Lesson Title 4"},
    			]);
    	}
        this.render();
    },

    render: function() {

        this.$el.html(this.template(this.model.attributes));
        var container = document.createDocumentFragment();

        for(i = 0; i < this.collection.length; i++) {
			var name = new String('content_nextsteps_lesson_'+i);
			this[name] = this.add_subview(ContentNextStepsLessonView, {
				model: this.collection.models[i]
			});
			container.appendChild(this[name].el);
		}

		this.$("#content-nextsteps-lessons").append(container);
    }

});

/**
 * View that wraps a topic on the content explore card on the learn page
 */
window.ContentExploreTopicView = BaseView.extend({

	template: HB.template("contentrec/content-explore-topic"),

	initialize: function() {
		this.render();
	},

	render: function() {
		this.$el.html(this.template(this.model.attributes));
	}

});

/**
 * View that wraps the content explore card on the learn page
 */
window.ContentExploreView = BaseView.extend({

	template: HB.template("contentrec/content-explore"),

	initialize: function() {
		if (typeof this.collection === "undefined") {
    		this.collection = new SuggestedContentCollection([
    			{interest_topic: "Chemistry", suggested_topic: "Physics"},
    			{interest_topic: "Physiology", suggested_topic: "Biology"},
    			{interest_topic: "Algebra", suggested_topic: "Precalculus"},
    			{interest_topic: "Modern Art", suggested_topic: "Art History"}
    			]);
    	}
        this.render();
	},

	render: function() {

		this.$el.html(this.template(this.model.attributes));
        var container = document.createDocumentFragment();

		for(i = 0; i < this.collection.length; i++) {
			var name = new String('content_explore_topic_'+i);
			this[name] = this.add_subview(ContentExploreTopicView, {
				model: this.collection.models[i]
			});
			container.appendChild(this[name].el);
		}

		this.$("#content-explore-topics").append(container);
	}

});


$(function(){
	window.contentResumeModel = new window.ContentResumeModel();
	window.suggestedContentCollection = new window.SuggestedContentCollection();

	//contentResumeModel.fetch().then(function(){
		window.content_resume = new ContentResumeView({
			model: contentResumeModel
		});

		window.content_nextsteps = new ContentNextStepsView({
			model: suggestedContentCollection
		});

		window.content_explore = new ContentExploreView({
			model: suggestedContentCollection
		});

		//$("#content-area").append(window.content_resume.el.childNodes);
		$("#content-area").append(window.content_nextsteps.el.childNodes);
		$("#content-area").append(window.content_explore.el.childNodes);

	//});

	//resize_to_fit();
});

function resize_to_fit(){
	var fontsize = $('span#left-col span').css('font-size');
	$('span#left-col span').css('fontSize', parseFloat(fontsize) - 1);

	if($('span#left-col span').height() >= $('span#left-col').height()){
		//console.log("resizing");
		resize_to_fit();
	}
}
