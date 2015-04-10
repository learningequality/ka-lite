// Views

/**
 * View that wraps the content resume card on the learn page
 */
window.ContentResumeView = BaseView.extend({

    template: HB.template("contentrec/content-resume"),
    
    initialize: function() {
        this.model = new Backbone.Model();
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
    }

});

$(function(){
	//window.content_resume = new ContentResumeView();
	//$("#content-area").append(window.content_resume.$el);
	window.content_resume = new ContentResumeView({
		el: "#content-area"
	});
});
