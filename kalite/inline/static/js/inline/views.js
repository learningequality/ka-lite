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
                var before_showing = [];
                var options = self.parseNarrative(narr, before_showing);

                //set the options on introjs object
                var intro = introJs();
                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);


                //runs before-showing, if applicable (before-showing[] populated)
                var i = 0;
                var step = 0;

                //set before-showing functions on elements if needed for page

                if (before_showing.length !== 0) {
                    intro.onafterchange(function(target) {
                        console.log("the before_showing object");
                        console.log(before_showing[i]);
                        if (target == document.querySelector(before_showing[i]["element"]) ){ 
                            console.log("inside onafterchange(), going to set the click function on btn");

                            //perform action after the "next" button is clicked on the tooltip
                            $("a.introjs-button.introjs-nextbutton").click(function() {
                                console.log(" 'NEXT' button has been clicked in modal!");
                                console.log(before_showing[i]["action"]);

                                //when user clicks on 'next' CHECK NEXT ELEMENT:
                                //if null, wait for next element to load,
                                //else if element exists, trigger action
                                $(target).trigger(before_showing[i]["action"]);
                                setTimeout(function(){
                                    console.log("Waiting for next element to load");
                                    }, 2000);
                                i++;
                            }); 
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
                // var newvalue = null;

                if (key === "text") {
                    newkey = "intro";
                }
                else if (key === "position") {
                    newkey = "position";
                }
                else if (key === "step") {
                    newkey = "step";
                }
                else if (key === "before-showing") {
                    //add the before-showing attribute to a separate
                    //"before-showing" array to be used in intro.onchange()
                    console.log("inside before-showing building");
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

module.exports = ButtonView;
