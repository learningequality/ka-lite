var TestModel = Backbone.Model.extend();
var TestList = Backbone.Collection.extend({
    url: function() { return ALL_TESTS_URL; },
    model: TestModel
});


var CurrentUnitModel = Backbone.Model.extend();
var CurrentUnitList = Backbone.Collection.extend({
    url: function() { return ALL_CURRENT_UNIT_URL; },
    model: CurrentUnitModel
});
