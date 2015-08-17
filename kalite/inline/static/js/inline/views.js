var _ = require("underscore");
var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");

var introJs = require("intro.js");

var ButtonView = BaseView.extend({
    template: require("./hbtemplates/inline.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");  
        this.render();
    },

    events: {
        "click": "clickCallback"
    },

    clickCallback: function() {
        var self = this;
        this.model.fetch({ 
            success: function(model, response, options) {
                //obtain narrative, JSON obj of elements and their attributes
                var narr = self.model.attributes;

                //translate narrative into build options for introjs
                options = _.extend(options, self.parseNarrative(narr));

                //set the options on introjs object
                var intro = introJs();
                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);

                intro.start();
            },

            error: function(model, response, options) {
                console.log("Unable to load inline tutorial narrative!");
            }
        });
    },

    //Translate narrative into JSON obj used to set introjs options
    parseNarrative: function(narr) {
        var options = {};
        var steps = [];

        var key = Object.keys(narr);
        key = key[1];

        // Parse narrative into obj using attribute keywords for intro framework
        var newselectors = _.map(narr[key], function(element) {
            var step = {};
            var selectorKey = String(Object.keys(element));
            var attributes = [];
            attributes = element[selectorKey];

            if (selectorKey != "unattached") {
                step["element"] = selectorKey;
            }

            //Set {key: value} pairs that define modal for each intro step
            var parsed = _.map(attributes, function(attribute) {
                var key = Object.keys(attribute);
                key = key[0];
                var value = attribute[key];
                var newkey = null;
                var newvalue = null;

                if (key === "text") {
                    newkey = "intro";
                    newvalue = value;
                }
                else if (key === "position") {
                    newkey = "position";
                    newvalue = value;
                }
                else if (key === "before-showing") {
                    //TO DO: user actions to taken before showing modal
                }
                step[newkey] = value;
            });
            steps.push(step);
        });

        options["steps"] = steps;
        return options;
    },

    render: function() {
        this.$el.html(this.template());
        $("#inline-btn-container").append(this.el);
    }
});

module.exports = ButtonView;