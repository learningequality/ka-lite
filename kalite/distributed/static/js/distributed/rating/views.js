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

    events: {
        "click .rating-delete": "delete_callback"
    },

    initialize: function(options) {
        /*
            Prepare self and subviews.
        */
        this.model = options.model || function() {
            var model = new Backbone.Model();
            model.url = "/api/not/gonna/work";
            return model;
        }();
        _.bindAll(this, "delete_callback", "renderAll", "renderSequence", "render");
        this.quality_label_values = {
            1:  "Poor quality",
            2:  "Somewhat poor",
            3:  "Average",
            4:  "Somewhat high",
            5:  "High quality"
        };
        this.difficulty_label_values = {
            1:  "Very easy",
            2:  "Easy",
            3:  "Average",
            4:  "Hard",
            5:  "Very hard"
        };
    },

    render: function() {
        /*
            If the model is new (never been synced) or empty (such as if it was deleted) render each component in
            sequence. Otherwise, render all components together, for review.
        */
        if( this.model.isNew() || this.model.get("quality") === 0 || this.model.get("difficulty") === 0) {
            this.renderSequence();
        } else {
            this.renderAll();
        }
    },

    renderSequence: function() {
        /*
            Present each rating widget one by one, waiting for user interaction before growing to show the next.
            Then once the user has filled out the rating completely, call renderAll to allow review/editing.
        */
        this.$el.html(this.template());

        this.star_view_quality = this.add_subview(StarView, {title: "Quality", el: this.$("#star-container-quality"), model: this.model, rating_attr: "quality", label_values: this.quality_label_values});

        var self = this;

        this.listenToOnce(this.model, "change:quality", function(){
            self.star_view_difficulty = self.add_subview(StarView, {title: "Difficulty", el: self.$("#star-container-difficulty"), model: self.model, rating_attr: "difficulty", label_values: this.difficulty_label_values});
        });

        this.listenToOnce(this.model, "change:difficulty", this.renderAll);
    },

    renderAll: function() {
        /*
            Renders itself, then attaches all subviews.
            Called when: 1) The view's model is fetched successfully or
                         2) The view's model is not fetched, and the user finishes filling out the new form.
        */
        this.$el.html(this.template());
        var views_and_opts = [
            ["star_view_quality", StarView, {title: "Quality", el: this.$("#star-container-quality"), model: this.model, rating_attr: "quality", label_values: this.quality_label_values}],
            ["star_view_difficulty", StarView, {title: "Difficulty", el: this.$("#star-container-difficulty"), model: this.model, rating_attr: "difficulty", label_values: this.difficulty_label_values}],
            ["text_view", TextView, {el: this.$("#text-container"), model: this.model, rating_attr: "text"}]
        ];
        var self = this;
        _.each(views_and_opts, function(el, ind, list){
            self[el[0]] = self.add_subview(el[1], el[2]);
        });
    },

    delete_callback: function() {
        var self = this;
        this.$el.html("Deleting your review...");
        // Don't simply clear & destroy the model, we wish to remember some attributes (like content_kind and user_uri)
        this.model.save({
            quality: 0,
            difficulty: 0,
            text: ""
        },
        {
            error: function(){
                console.log("failed to clear rating model attributes...");
            },
            success: function(){
                self.renderSequence();
            },
            patch: true
        });
    }
});


/*
    Widget to rate something from 1 to 5 stars.
*/
var StarView = BaseView.extend({

    template: require("./hbtemplates/star.handlebars"),

    events: {
        "click .star-rating-option": "rate_value_callback",
        "click .star-rating-option >": "rate_value_callback",
        "mouseenter .star-rating-option >": "mouse_enter_callback",
        "mouseenter .star-rating-option": "mouse_enter_callback",
        "mouseleave .star-rating-option": "mouse_leave_callback"
    },

    label_values: {
        1: "Very Low",
        2: "Low",
        3: "Normal",
        4: "High",
        5: "Very High"
    },

    initialize: function(options) {
        this.model = options.model || new Backbone.Model();
        this.title = options.title || "";
        this.label_values = options.label_values || this.label_values;
        this.rating_attr = options.rating_attr || "rating";
        _.bindAll(this, "rate_value_callback", "rating_change");

        this.model.on("change:"+this.rating_attr, this.rating_change);

        this.render();
    },

    render: function() {
        var template_options = {};
        _.extend(template_options, this.model.attributes, {title: this.title, lowest_value: this.label_values[1], highest_value: this.label_values[5]});
        this.$el.html(this.template(template_options));
        this.rating_change();
    },

    // Debounced with immediate=true option, so that it's triggered _at most_ once per 100 ms, since it
    //   could be called by clicking on a child element as well.
    rate_value_callback: _.debounce(function(ev) {
        // The target event could be either the .star-rating-option or a child element, so whatever the case get the
        // parent .star-rating-option element.
        var target = $(ev.target).hasClass("star-rating-option") ? $(ev.target) : $(ev.target).parents(".star-rating-option")[0];
        var val = $(target).attr("data-val");
        this.model.set(this.rating_attr, val);
    }, 100, true),

    mouse_enter_callback: function(ev) {
        // The target event could be either the .star-rating-option or a child element, so whatever the case get the
        // parent .star-rating-option element.
        var target = $(ev.target).hasClass("star-rating-option") ? $(ev.target) : $(ev.target).parents(".star-rating-option")[0];
        var val = $(target).attr("data-val");
        this.$(".rating-label").text(this.label_values[val]);
    },

    mouse_leave_callback: function(ev) {
        this.$(".rating-label").text("");
    },

    rating_change: function() {
        opts = this.$(".star-rating-option");
        _.each(opts, function(opt, index, list) {
            $opt = $(opt);
            $opt.toggleClass("activated", parseInt($opt.attr("data-val")) <= parseInt(this.model.get(this.rating_attr)));
        }, this);
        this.model.save();
    }
});


/*
    Widget to accept/display free-form text input.
*/
var TextView = BaseView.extend({

    template: require("./hbtemplates/text.handlebars"),

    events: {
        "keyup .rating-text-feedback": "text_changed"
    },

    initialize: function(options) {
        this.model = options.model || new Backbone.Model();
        this.text_attr = options.text_attr || "text";
        _.bindAll(this, "text_changed");
        this.model.on("change:"+this.text_attr, this.text_changed);
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    text_changed: _.throttle(function() {
        this.model.set(this.text_attr, this.$(".rating-text-feedback")[0].value);
        this.model.save();
    }, 500),
});