//var UnitModel = Backbone.Model;

var TestList = Backbone.Collection.extend({
    url: function() { return ALL_TESTS_URL; },
    model: Backbone.Model
});


var CurrentUnitList = Backbone.Collection.extend({
    url: function() { return ALL_CURRENT_UNIT_URL; },
    model: Backbone.Model
});
