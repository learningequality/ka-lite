var Backbone = require("../base/backbone");
var $ = require("../base/jQuery");
var _ = require("underscore");
var BaseView = require("../base/baseview");
var Handlebars = require("../base/handlebars");

/*
    Container view for feedback form.
    See the design document here: https://docs.google.com/a/learningequality.org/document/d/1W_2vv1cZU5wZp_MLjvPy6jHwkRVPW_iTJhHEpSOYrCs/edit?usp=drive_web
*/
module.exports = BaseView.extend({

    template: require("./hbtemplates/rating.handlebars"),

    initialize: function() {
        /*
            Prepare self and subviews.
        */
        this.render();
    },

    render: function() {
        /*
            Renders itself, then attaches (rendered) subviews.
        */
        this.$el.html(this.template());
        this.star_view = this.add_subview(StarView, {el: this.$("#star-container")});
        this.text_view = this.add_subview(TextView, {el: this.$("#text-container")});
    }

});


/*
    Widget to rate something from 1 to 5 stars.
*/
var StarView = BaseView.extend({

    template: require("./hbtemplates/star.handlebars"),

    initialize: function() {
        this.render();
    },

    render: function() {
        this.$el.html(this.template());
    }

});


/*
    Widget to accept/display free-form text input.
*/
var TextView = BaseView.extend({

    template: require("./hbtemplates/text.handlebars"),

    initialize: function() {
        this.render();
    },

    render: function() {
        this.$el.html(this.template());
    }

});