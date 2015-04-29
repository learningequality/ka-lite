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
    		this.collection = new ContentNextStepsCollection([
    			{interest_topic: "Test Topic 1", lesson_title: "Test Lesson Title"},
    			{interest_topic: "Test Topic 2", lesson_title: "Test Lesson Title 2"}
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
    		this.collection = new ContentExploreCollection([
    			{interest_topic: "Test Topic 1", suggested_topic: "Physics"},
    			{interest_topic: "Test Topic 2", suggested_topic: "Geometry"}
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
	window.contentNextStepsCollection = new window.ContentNextStepsCollection();
	window.contentExploreCollection = new window.ContentExploreCollection();

	//contentResumeModel.fetch().then(function(){
		window.content_resume = new ContentResumeView({
			model: contentResumeModel
		});

		window.content_nextsteps = new ContentNextStepsView({
			model: contentNextStepsCollection
		});

		window.content_explore = new ContentExploreView({
			model: contentExploreCollection
		});

		$("#content-area").append(window.content_resume.el.childNodes);
		$("#content-area").append(window.content_nextsteps.el.childNodes);
		$("#content-area").append(window.content_explore.el.childNodes);

	//});
});
