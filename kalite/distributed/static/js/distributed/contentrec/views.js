// Views

/*The wrapper where everything goes, makes for a dynamic page*/
window.HomepageWrapper = BaseView.extend({

    template: HB.template("contentrec/content-rec-wrapper"),
    
    initialize: function() {
        
        var resumeCollection = new window.SuggestedContentCollection(this.collection.where({resume:true}));
        
        var nextStepsCollection = new window.SuggestedContentCollection(this.collection.where({nextSteps:true}));
        
        var exploreCollection = new window.SuggestedContentCollection(this.collection.where({explore:true}));
        
        this.content_resume = new ContentResumeView({
            collection:resumeCollection
		});

		this.content_nextsteps = new ContentNextStepsView({
            collection:nextStepsCollection
		});

		this.content_explore = new ContentExploreView({
            collection:exploreCollection
		});
                
        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        this.$("#resume").append(this.content_resume.el);
        this.$("#nextsteps").append(this.content_nextsteps.el);
        this.$("#explore").append(this.content_explore.el);
    }

});

/**
 * View that wraps the resume card on the home page
 */
window.ContentResumeView = BaseView.extend({

    template: HB.template("contentrec/content-resume"),
    
    initialize: function() {
        this.render();
    },

    render: function() {
        this.$el.html(this.template());
    }

});

/**
 * View that wraps a lesson on the next steps card on the home page
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
 * View that wraps the next steps card on the home page
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

        this.$el.html(this.template());
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
 * View that wraps a topic on the content explore card on the home page
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
 * View that wraps the content explore card on the home page
 */
window.ContentExploreView = BaseView.extend({

	template: HB.template("contentrec/content-explore"),

	initialize: function() {
		_.bindAll(this);
		if (typeof this.collection === "undefined") {
    		this.collection = new SuggestedContentCollection();
    		this.collection.fetch({
    			data: {explore: true},
    			success: this.render
    		});
    	} else {
        	this.render();
    	}
	},

	render: function() {

		this.$el.html(this.template());
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
        
    window.suggestedContentCollection = new window.SuggestedContentCollection([
		{interest_topic: "Chemistry", suggested_topic: "Physics", resume: true},
		{interest_topic: "Physiology", suggested_topic: "Biology", nextSteps: true},
		{interest_topic: "Algebra", suggested_topic: "Precalculus", explore: true, nextSteps: true},
		{interest_topic: "Modern Art", suggested_topic: "Art History", explore: true}
	]);
    
    window.hpwrapper = new HomepageWrapper({
        collection:suggestedContentCollection,
        el:"#content-area"
		});    
});

