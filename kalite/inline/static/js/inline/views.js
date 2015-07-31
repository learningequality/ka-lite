var _ = require("underscore");
var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");

var introJs = require("./intro");

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
                var parsedNarr = self.parseNarrative(narr);
                var options = parsedNarr["options"];
                var before_showing = parsedNarr["before_showing"];

                var intro = introJs.introJs();

                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);
                intro.onbeforechange( function(targetElement) {
                    console.log(targetElement);
                });

                intro.start();
            },

            error: function(model, response, options) {
                console.log("Unable to load inline tutorial narrative!");
            }
        });
    },

    //Translate narrative into JSON obj used to set introjs options
    parseNarrative: function(narr, before_showing) {
        var steps = [];
        var before_showing = [];

        var key = Object.keys(narr)[1];

        // Parse narrative into obj using attribute keywords for intro framework
        _.each(narr[key], function(element, el_index, el_list) {
            var step = {};
            var selectorKey = String(Object.keys(element));
            var attributes = element[selectorKey];

            if (selectorKey != "unattached") {
                step["element"] = selectorKey;
            }

            //Set {key: value} pairs that define modal for each intro step
            _.each(attributes, function(attribute, att_index, att_list) {
                var key = Object.keys(attribute)[0];
                var value = attribute[key];

                if (key === "text") {
                    step["intro"] = value;
                } else if (key === "position") {
                    step["position"] = value;
                } else if (key === "step") {
                    step["step"] = value;
                } else if (key === "before-showing") {
                    before_showing[el_index] = value;
                }
            });
            steps.push(step);
        });

        return {
            "options": {"steps": steps},
            "before_showing": before_showing
        };
    },

    render: function() {
        this.$el.html(this.template());
        $("#inline-btn-container").append(this.el);
    }
});

module.exports = ButtonView;
