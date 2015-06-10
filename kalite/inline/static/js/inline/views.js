window.ButtonView = Backbone.View.extend({
    template: HB.template("inline/inline"),

    initialize: function() {
        _.bindAll(this);  
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
                var before_showing = [];
                var options = self.parseNarrative(narr, before_showing);

                //set the options on introjs object
                var intro = introJs();
                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);

                //runs before-showing, if applicable (before-showing[] populated)
                var i = 0;
                if (before_showing.length !== 0) {
                    intro.onafterchange(function(target) {
                        if (target == document.querySelector(before_showing[0]["element"]) ){ 
                            console.log("an action should be performed on this element");
                            $(target).trigger(before_showing[0]["action"]);
                            i++;
                        }
                    });
                }
                intro.start();
            },

            error: function(model, response, options) {
                console.log("Unable to load inline tutorial narrative!");
            }
        });
    },

    //Translate narrative into JSON obj used to set introjs options
    parseNarrative: function(narr, before_showing) {
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
                    //add the before-showing attribute to a separate
                    //"before-showing" array to be used in intro.onchange()
                    var before_showing_obj = {};
                    before_showing_obj["element"] = selectorKey;
                    before_showing_obj["action"] = value;
                    before_showing.push(before_showing_obj);
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

// Only load button and narrative if there is one defined for page
$(function() {
    var narrative = new NarrativeModel ({id: window.location.pathname});
    var buttonView = new ButtonView( {model: narrative});
});
