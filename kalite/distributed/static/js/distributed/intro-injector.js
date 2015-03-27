//on page load
$(function() {
  console.log( "ready!" );

  //Use relative URL to determine which YAML file to parse
  var relative_url = window.location.pathname;
  var response = getIntro(relative_url);
  
  //Parse YAML file into JSON to be used with intro.js !!! this is actually just a json object for nao.
  var jsonResponse = parseResponse(response);

console.log(jsonResponse);

  //Load from our new JSON object, and attach to elements in page
  attachAttributes(jsonResponse);

  console.log("uhh hello?");

});

function startTour() {
            var tour = introJs()
            tour.setOption('tooltipPosition', 'auto');
            tour.setOption('positionPrecedence', ['left', 'right', 'bottom', 'top'])
            tour.start()
        }


//Returns the yaml blob given the relative_url? <<<< jk that isn't right.
//make an ajax request to some url that we haven' tyet defined and then we would wait until
//the server returns a response and what we expet is a json object (Serialized)
//that we can parse directly into an actual json object
//
function getIntro(relative_url) {
  return {"management/zone/None/": [{"a#manage.admin-only": [{"step": 1}, {"text": "Welcome! This is the landing page for admins. If at any point you would like to navigate back to this page, click on this tab!"}]}, {"li.facility": [{"step": 2}, {"text": "Clicking on this tab will show you a quick overview of all facilities and devices"}]}, {"a.create-facility": [{"step": 3}, {"text": "To add new facilities, click here..."}]}, {"content-container .row:nth-child(3)": [{"step": 4}, {"text": "Information on your device status will be shown here"}]}, {"a.create-facility": [{"step": 5}, {"text": "If you decide to register your device to our central club, click here"}]}, {"#not-registered": [{"step": 6}, {"text": "Questions about anything on the page? Be sure to consult the user manual or FAQ for more detailed walk throughs!"}]}]};
}

//Given JSON form of YAML file for this page, parse and return JSON object
//that can be used for intro framework. 
function parseResponse(response) {
  var url = Object.keys(response);
  var parsedResponse = {};

  //Parse the array containing selector objects for a given URL
  var newselector = [];
  newselector = _.map(response[url], function(element) {
    var selectorKey = Object.keys(element);
    var attributes = [];
    attributes = element[selectorKey];

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
      else {
        newkey = "data-intro";
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
//------------------------------------------------------------------
// Attaches attributes for intro.js to HTML elements 
//    by iterating through elements from JSON object.
//------------------------------------------------------------------
function attachAttributes(jsonResponse) {
  var url = Object.keys(jsonResponse);

  _.map(jsonResponse[url], function(element) {
    //selectorKey = selector element to apply attributes to
    var selectorKey = Object.keys(element);
    var attributes = [];
    attributes = element[selectorKey];

    _.map(attributes, function(attribute) {
      //key = attribute to be added to the element
      //value = numbered step or description in tooltip
      var key = Object.keys(attribute);
      key = String(key[0]);
      var value = String(attribute[key]);

      //append the intro key-value pair to the element.
      selectorKey = String(selectorKey);
      $(selectorKey).attr(key, value);
      console.log("THIS IS SELECTOR KEY AT THE END THO:" +selectorKey);
    });
  }); 


/**
  var selectorKey = "a#manage.admin-only";
  var key = "data-step";
  var value = 1;
  $(selectorKey).attr(key, value); **/

}
