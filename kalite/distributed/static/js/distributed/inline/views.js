window.ButtonView = Backbone.View.extend({
    //el: '#inline-btn',

    template: HB.template("inline/inline"),

    initialize: function() {
        _.bindAll(this);  
        console.log("backbone view for inline button initializedddd");
        this.render();
    },

    events: {
        "click": "clickCallback"
    },

    clickCallback: function() {
        var self = this;
        this.model.fetch({ 
            success: function(model, response, options) {
                //how do i get the object that sync returns????
                // MCG -- by using self.model, and self.model.get("whatever attribute, like intro")

                //var url = window.location.pathname;

                //obtain narrative object
                var narr = self.model.get("intro");

                //translate narrative object into specific, intro ramework-based object (introjs)
                var response = this.parseNarrative(narr);

                //build options with this narrative object, for intro injection
                var options = this.buildOptions(response);

                //set the options on introjs object
                var intro = introJs();
                intro.setOption('tooltipPosition', 'auto');
                intro.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top']);
                intro.setOptions(options);

                //start the intro
                intro.start();
            }
        });
    },

    //Parses fetched narrative into a JSON object that can be used for 
    //the intro framework
    parseNarrative: function(response) {
        var url = Object.keys(response);
        var parsedResponse = {};

        //Parse the array containing selector objects for a given URL
        var newselector = [];
        newselector = _.map(response[url], function(element) {
            var selectorKey = Object.keys(element);
            var attributes = [];
            attributes = element[selectorKey];

            console.log("This is selectorKey: " + selectorKey)

            //Parse array of intro.js attributes for a given selector
            var parsed = [];
            parsed = _.map(attributes, function(attribute) {
                var key = Object.keys(attribute);
                key = key[0];
                var value = attribute[key];
                var newkey = null;
                var newvalue = null;

                //Change the attributes to match the framework
                if (key === "step") {
                    newkey = "data-step";
                    newvalue = value;
                }
                else if (key === "text") {
                    newkey = "intro";
                    newvalue = value;
                }
                else if (key === "position") {
                    newkey = "position";
                    newvalue = value;
                }

                var newattr = {};
                newattr[newkey] = newvalue;
                return newattr; 
            }); 

            //new object {selector: [{attr1: val}, {attr2: val}] } for introjs syntax
            var newElement = {};
            newElement[selectorKey] = parsed;
            return newElement;
        });

        //add new array of selector objects to json object
        parsedResponse[url] = newselector;
        return parsedResponse;
    },

    buildOptions: function(response) {
        var url = Object.keys(response);
        var options = {};         
        var steps = [];
        
        //Set the key:value pairs for the steps object
        _.map(response[url], function(element) {
            var selectorKey = String(Object.keys(element));
            var attributes = [];
            attributes = element[selectorKey];
            var step = {};

            if (selectorKey != "unattached") {
                step["element"] = selectorKey; 
            }

            _.map(attributes, function(attribute) {
                var key = Object.keys(attribute);
                key = key[0];
                var value = attribute[key];

                var newkey = null;

                //Attach options for intro framework.
                if (key === "text"){
                    newkey = "intro";
                }
                else if (key === "position") {
                    newkey = "position";
                }
                else { 
                    return;
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

      console.log("HAH idk brb");

      $("body").append(this.el);
    }
});


// On page load
$(function() {
    var narrative = new NarrativeModel();
    var buttonView = new ButtonView( {model: narrative} );
});

//Given JSON form of YAML file for this page, parse and return JSON object
//that can be used for intro framework. 
/**function parseResponse(response) {
  var url = Object.keys(response);
  var parsedResponse = {};

  //Parse the array containing selector objects for a given URL
  var newselector = [];
  newselector = _.map(response[url], function(element) {
    var selectorKey = Object.keys(element);
    var attributes = [];
    attributes = element[selectorKey];

    console.log("This is selectorKey: " + selectorKey)

    //Parse array of intro.js attributes for a given selector
    var parsed = [];
    parsed = _.map(attributes, function(attribute) {
      var key = Object.keys(attribute);
      key = key[0];
      var value = attribute[key];
      
      var newkey = null;
      var newvalue = null;

      //Change the attributes to match the framework
      if (key === "step") {
        newkey = "data-step";
        newvalue = value;
      }
      else if (key === "text") {
        newkey = "intro";
        newvalue = value;
      }
      else if (key === "position") {
        newkey = "position";
        newvalue = value;
      }

      var newattr = {};
      newattr[newkey] = newvalue;
      return newattr; 
    }); 

    //new object {selector: [{attr1: val}, {attr2: val}] } for introjs syntax
    var newElement = {};
    newElement[selectorKey] = parsed;
    return newElement;

  });

  //add new array of selector objects to json object
  parsedResponse[url] = newselector;
  return parsedResponse;

} 

//Iterate through the jsonResponse object to build options for introJs()
function buildOptions(response) {
  var url = Object.keys(response);
  var options = {};         
  var steps = [];
  
  //Set the key:value pairs for the steps object
  _.map(response[url], function(element) {
    var selectorKey = String(Object.keys(element));
    var attributes = [];
    attributes = element[selectorKey];
    var step = {};

    if (selectorKey != "unattached") {
      step["element"] = selectorKey; 
    }

    _.map(attributes, function(attribute) {
      var key = Object.keys(attribute);
      key = key[0];
      var value = attribute[key];

      var newkey = null;

      //Attach options for intro framework.
      if (key === "text"){
        newkey = "intro";
      }
      else if (key === "position") {
        newkey = "position";
      }
      else { 
        return;
      }

      step[newkey] = value;
    });
    steps.push(step);
  });

  options["steps"] = steps;
  return options;
} **/
