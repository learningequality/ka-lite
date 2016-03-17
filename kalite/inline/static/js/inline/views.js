var _ = require("underscore");
var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");

var introJs = require("intro.js");

/*
    Force the bootstrap script to be reloaded. This is meant to be run after the bootstrap API has been disabled.
    We might wish to disable the API, for example, to keep dropdown menus expanded.
*/
function reload_bootstrap() {
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.type = 'text/javascript';
    // window.bootstrap_src is defined by a template context variable
    script.src = window.bootstrap_src;
    head.appendChild(script);
}

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
            success: function(model, response) {
                //obtain narrative, JSON obj of elements and their attributes
                var narr = model.attributes;

                //translate narrative into build options for introjs
                var parsedNarr = self.parseNarrative(narr);
                var options = parsedNarr["options"];
                var before_showing = parsedNarr["before_showing"];

                var intro = introJs.introJs();
                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);

                intro.onbeforechange( function(targetElement) {
                    if( typeof before_showing[intro._currentStep] !== "undefined" ) {
                        _.each(before_showing[intro._currentStep], function(element, a_index, a_list) {
                            var action = Object.keys(element)[0];
                            var target = element[action];
                            if (action === "click") {
                                $(target).click();
                                if( $(targetElement).parents().hasClass("dropdown") ) {
                                    /* Imperfect solution. If a dropdown menu (or a child element) is clicked, then
                                        disable the bootstrap dropdown api, so that the dropdown remains expanded.
                                        Will be re-enabled by the introJs.onexit or introJs.oncomplete callbacks. */
                                    $(document).off(".dropdown.data-api");
                                }
                            } else if(action === "scroll-to") {
                                $(window).scrollTop(target);
                            }
                        });
                    }
                });

                // onexit and oncomplete are not both called, it's either one or the other
                intro.onexit(function(){
                    reload_bootstrap(); // In case we disabled it, for the dropdown menu
                });
                intro.oncomplete(function(){
                    reload_bootstrap(); // In case we disabled it, for the dropdown menu
                });

                intro.start();
            },

            error: function(model, response, options) {
                console.log("Unable to load inline tutorial narrative!");
                self.$("#inline-btn").prop("disabled", true);
            }
        });
    },

    //Translate narrative into JSON obj used to set introjs options
    parseNarrative: function(narr) {
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
                    step["intro"] = gettext(value);
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
