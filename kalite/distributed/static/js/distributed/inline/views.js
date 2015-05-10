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
                //Obtain narrative - array of elements and their attributes
                var narr = self.model.url;

                console.log("AFTER RETRIEVING NARR FORM INSIDE VIEWS");
                console.log(narr);

                //translate narrative into build options for introjs (array->object)
                var options = self.parseNarrative(narr);

                //set the options on introjs object
                var intro = introJs();
                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);

                //start the intro
                intro.start();
            },

            // error: function(model, response, options) {
            //     console.log("Error fetching narrative model sorry bye");
            // }
        });
    },

    //Translate narrative (array)->JSON object that sets introjs options
    parseNarrative: function(narr) {
        var options = {};
        var steps = [];

        // Parse for selector keys, modals may be unattached.
        var newselectors = _.map(narr, function(element) {
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
                step[newkey] = value;
            });
            steps.push(step);
        });

        options["steps"] = steps;
        console.log(options);
        return options;
    },

    render: function() {
        this.$el.html(this.template());
        $("body").append(this.el);
    }
});


//On page load
$(function() {
    console.log("INSIDE PAGELOAD VIEWS");

    // Strip pathname of first '/'
    var pathname = window.location.pathname;
    pathname = pathname.substring(1, pathname.length);
    console.log("pathname inside pageload views:");
    console.log(pathname);
    var narrative = new NarrativeModel({id: pathname});
    var buttonView = new ButtonView( {model: narrative} );
});
