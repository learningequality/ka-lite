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
        this.star_view_1 = this.add_subview(StarView, {el: this.$("#star-container-1")});
        this.star_view_2 = this.add_subview(StarView, {el: this.$("#star-container-2")});
        this.star_view_3 = this.add_subview(StarView, {el: this.$("#star-container-3")});
        this.text_view = this.add_subview(TextView, {el: this.$("#text-container")});
    }

});


/*
    Widget to rate something from 1 to 5 stars.
*/
var StarView = BaseView.extend({

    template: require("./hbtemplates/star.handlebars"),

    events: {
        "click .star-rating-option": "rate_value_callback"
    },

    initialize: function(options) {
        this.model = options.model || new Backbone.Model();
        this.rating_attr = options.rating_attr || "rating";
        _.bindAll(this, "rate_value_callback", "rating_change")

        this.model.on("change:"+this.rating_attr, this.rating_change);

        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
    },

    rate_value_callback: function(ev) {
        var val = $(ev.target).attr("data-val");
        this.model.set(this.rating_attr, val);
    },

    rating_change: function() {
        opts = this.$(".star-rating-option");
        _.each(opts, function(opt, index, list) {
            $opt = $(opt);
            $opt.toggleClass("activated", $opt.attr("data-val") <= this.model.get(this.rating_attr));
        }, this);
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