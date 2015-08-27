// Views

/*All 3 cards go into this wrapper, which makes the page responsive*/
window.HomepageWrapper = BaseView.extend({

    template: HB.template("contentrec/content-rec-wrapper"),
    
    initialize: function() {
        _.bindAll(this);
        this.set_collection();
        this.listenTo(window.statusModel, "change:user_id", this.set_collection);
    },

    set_collection: function() {
        this.collection = new window.SuggestedContentCollection([], {
            resume: true,
            next: true,
            explore: true
        });
        this.listenTo(this.collection, "sync", this.data_load);
        this.collection.fetch();
    },

    render: function() {
        if (this.collection.length > 0) {
            this.$el.html(this.template());

            if (this.content_resume) {
                this.$("#resume").append(this.content_resume.el);
            }

            if (this.content_nextsteps) {
                this.$("#nextsteps").append(this.content_nextsteps.el);
            }

            if (this.content_explore) {
                this.$("#explore").append(this.content_explore.el);
            }
        }
    },

    data_load: function() {
        var resumeCollection = new window.SuggestedContentCollection(this.collection.where({resume:true}));
        
        var nextStepsCollection = new window.SuggestedContentCollection(this.collection.where({next:true}));
        
        var exploreCollection = new window.SuggestedContentCollection(this.collection.where({explore:true}));
        
        if (resumeCollection.length > 0) {
            this.content_resume = new ContentResumeView({
                collection:resumeCollection
            });
        }

        if (nextStepsCollection.length > 0) {
            this.content_nextsteps = new ContentNextStepsView({
                collection:nextStepsCollection
            });
        }

        if (exploreCollection.length > 0) {
            this.content_explore = new ContentExploreView({
                collection:exploreCollection
            });
        }
                
        this.render();
    }
});

/**
 * View that wraps the resume card on the home page
 */
window.ContentResumeView = BaseView.extend({

    template: HB.template("contentrec/content-resume"),
    
    initialize: function() {
        if (typeof this.collection === "undefined") {
            this.collection = new SuggestedContentCollection([], {resume: true});
            this.listenTo(this.collection, "sync", this.render);
            this.collection.fetch();
        } else {
            this.render();
        }
    },

    render: function() {
        this.model = this.collection.at(0);
        this.$el.html(this.template(this.model.attributes));
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
 * View that wraps all the next steps cards on the home page
 */
window.ContentNextStepsView = BaseView.extend({

    template: HB.template("contentrec/content-nextsteps"),
    
    initialize: function() {
        if (typeof this.collection === "undefined") {
            this.collection = new SuggestedContentCollection([], {next: true});
            this.listenTo(this.collection, "sync", this.render);
            this.collection.fetch();
        } else {
            this.render();
        }
    },

    render: function() {

        this.$el.html(this.template());
        var container = document.createDocumentFragment();

        for(i = 0; i < this.collection.length; i++) {
            var name = 'content_nextsteps_lesson_'+ i;
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
 * View that wraps all the content explore cards on the home page
 */
window.ContentExploreView = BaseView.extend({

    template: HB.template("contentrec/content-explore"),

    initialize: function() {
        _.bindAll(this);
        if (typeof this.collection === "undefined") {
            this.collection = new SuggestedContentCollection([], {explore: true});
            this.listenTo(this.collection, "sync", this.render);
            this.collection.fetch();
        } else {
            this.render();
        }

    },

    render: function() {

        this.$el.html(this.template());
        var container = document.createDocumentFragment();

        for(i = 0; i < this.collection.length; i++) {
            var name = 'content_explore_topic_' + i;
            this[name] = this.add_subview(ContentExploreTopicView, {
                model: this.collection.models[i]
            });
            container.appendChild(this[name].el);
        }

        this.$("#content-explore-topics").append(container);
    }

});



