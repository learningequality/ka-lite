//on page load
$(function() {
  console.log( "ready!" );

  //Use relative URL to determine which YAML file to parse
  var relative_url = window.location.pathname;
  var response = getIntro(relative_url);
  
  //Parse YAML file into JSON to be used with intro.js !!! this is actually just a json object for nao.
  var jsonResponse = parseResponse(response);

  //Load from our new JSON object, and attach to elements in page
  attachAttributes(jsonResponse);



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
  return {"management/zone/None/": [{"ul.nav li a.admin-only": [{"step": 1}, {"text": "Welcome! This is the landing page for admins. If at any point you would like to navigate back to this page, click on this tab!"}]}, {"li.facility": [{"step": 2}, {"text": "Clicking on this tab will show you a quick overview of all facilities and devices"}]}, {"a.create-facility": [{"step": 3}, {"text": "To add new facilities, click here..."}]}, {"content-container .row:nth-child(3)": [{"step": 4}, {"text": "Information on your device status will be shown here"}]}, {"a.create-facility": [{"step": 5}, {"text": "If you decide to register your device to our central club, click here"}]}, {"a.create-facility": [{"step": 6}, {"text": "Questions about anything on the page? Be sure to consult the user manual or FAQ for more detailed walk throughs!"}]}]};
}

//Given a serialized JSON string, parse and return JSON object. 
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

      if (key === "step") {
        newkey = "data-step";
        newvalue = value;
      }
      else {
        newkey = "text";
        newvalue = value;
      }

      //Return a new object that uses appropriate introjs syntax
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
//    by utilizing the json object.
//------------------------------------------------------------------
function attachAttributes(jsonResponse) {
  //iterates through the elements from the JSON object
    //$(element).attr(data-step, 1)
    //$(element).attr(data-intro, "some text heres and")
  //attach attributes to these elements

  var url = Object.keys(jsonResponse);
  
  _.map(jsonResponse, function(element) {
    //selectorKey = selector element to apply attributes to
    var selectorKey = Object.keys(element);
    var attributes = [];
    attributes = element[selectorKey];

    _.map(attributes, function(attribute) {
      //key = attribute to be added to the element
      //value = numbered step or description in tooltip
      var key = Object.keys(attribute);
      key = key[0];
      var value = attribute[key];

      

      //append the intro key-value pair to the element.
      $(selectorKey).attr(key, value);

    });
  });


}


//don't care about url, go through array and then 
/**
for each object in the array, attached to the URL thing
1. get the selector
  2. get the object in the dom corresponding to this selector
  3. look at the array that is the value of the selector key
4. 
**/
