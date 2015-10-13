// Views
var _ = require("underscore");
var models = require("./models");
var BaseView = require("../base/baseview");

require("../../../css/distributed/content_recommendation.less");

/*All 3 cards go into this wrapper, which makes the page responsive*/
var HomepageWrapper = BaseView.extend({

    template: require("./hbtemplates/content-rec-wrapper.handlebars"),
    
    initialize: function() {
        _.bindAll(this, "set_collection", "data_load");
        this.set_collection();
        this.listenTo(window.statusModel, "change:user_id", this.set_collection);
    },

    set_collection: function() {
        this.collection = new models.SuggestedContentCollection([], {
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
        var resumeCollection = new models.SuggestedContentCollection(this.collection.where({resume:true}));
        
        var nextStepsCollection = new models.SuggestedContentCollection(this.collection.where({next:true}));
        
        var exploreCollection = new models.SuggestedContentCollection(this.collection.where({explore:true}));
        
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

    template: require("./hbtemplates/content-resume.handlebars"),
    
    initialize: function() {
        _.bindAll(this, "render");

        if (typeof this.collection === "undefined") {
            this.collection = new models.SuggestedContentCollection([], {resume: true});
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

    template: require("./hbtemplates/content-nextsteps-lesson.handlebars"),

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

    template: require("./hbtemplates/content-nextsteps.handlebars"),
    
    initialize: function() {
        _.bindAll(this, "render");
        
        if (typeof this.collection === "undefined") {
            this.collection = new models.SuggestedContentCollection([], {next: true});
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

    template: require("./hbtemplates/content-explore-topic.handlebars"),

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

    template: require("./hbtemplates/content-explore.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
        if (typeof this.collection === "undefined") {
            this.collection = new models.SuggestedContentCollection([], {explore: true});
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

module.exports = {
    HomepageWrapper: HomepageWrapper,
    ContentExploreView: ContentExploreView,
    ContentResumeView: ContentResumeView,
    ContentNextStepsView: ContentNextStepsView,
    ContentExploreTopicView: ContentExploreTopicView,
    ContentNextStepsLessonView: ContentNextStepsLessonView
};
