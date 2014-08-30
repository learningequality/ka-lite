var TestModel = Backbone.Model.extend();
var TestCollection = Backbone.Collection.extend({
    url: function() { return ALL_TESTS_URL; },
    model: TestModel
});


var CurrentUnitModel = Backbone.Model.extend();
var CurrentUnitCollection = Backbone.Collection.extend({
    url: function() { return ALL_CURRENT_UNIT_URL; },
    model: CurrentUnitModel
});
