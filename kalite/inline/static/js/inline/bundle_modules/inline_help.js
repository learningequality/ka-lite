var $ = require("base/jQuery");
var NarrativeModel = require("../models");
var ButtonView = require("../views");


// Only load button and narrative if there is one defined for page
$(function() {
    var narrative = new NarrativeModel ({id: window.location.pathname});
    var buttonView = new ButtonView( {model: narrative});
});
