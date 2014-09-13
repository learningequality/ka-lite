var TestModel = Backbone.Model.extend();
var TestCollection = Backbone.Collection.extend({
    // TODO(jamalex): remove need for ?force=true by having current unit-setting code
    // save directly to the Setting rather than going through the TestModel
    url: function() { return ALL_TESTS_URL + "?force=true"; },
    model: TestModel
});


var CurrentUnitModel = Backbone.Model.extend();
var CurrentUnitCollection = Backbone.Collection.extend({
    url: function() { return ALL_CURRENT_UNIT_URL; },
    model: CurrentUnitModel
});
