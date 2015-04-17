// Views

/**
 * View that wraps the content resume card on the learn page
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
 * View that wraps a lesson on the content explore card on the learn page
 */
window.ContentExploreLessonView = BaseView.extend({

	template: HB.template("contentrec/content-explore-lesson"),

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
		this.render();
	},

	render: function() {


		this.contentExploreLessonModel = new ContentExploreLessonModel();

		this.content_explore_lesson_1 = this.add_subview(ContentExploreLessonView, {
			model: this.contentExploreLessonModel
		});
		this.content_explore_lesson_2 = this.add_subview(ContentExploreLessonView, {
			model: this.contentExploreLessonModel
		});
		this.content_explore_lesson_3 = this.add_subview(ContentExploreLessonView, {
			model: this.contentExploreLessonModel
		});
		this.content_explore_lesson_4 = this.add_subview(ContentExploreLessonView, {
			model: this.contentExploreLessonModel
		});

		this.$el.html(this.template(this.model.attributes));

		this.$("#content-explore-lessons").append(this.content_explore_lesson_1.el.childNodes);
		this.$("#content-explore-lessons").append(this.content_explore_lesson_2.el.childNodes);
		this.$("#content-explore-lessons").append(this.content_explore_lesson_3.el.childNodes);
		this.$("#content-explore-lessons").append(this.content_explore_lesson_4.el.childNodes);
	}

});



$(function(){
	window.contentResumeModel = new window.ContentResumeModel();
	window.contentExploreModel = new window.ContentExploreModel();

	//contentResumeModel.fetch().then(function(){
		window.content_resume = new ContentResumeView({
			model: contentResumeModel
		});

		$("#content-area").append(window.content_resume.el.childNodes);

		window.content_explore = new ContentExploreView({
			model: contentExploreModel
		});

		$("#content-area").append(window.content_explore.el.childNodes);

	//});
});
