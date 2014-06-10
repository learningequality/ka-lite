var Test = Backbone.Model;

var TestList = Backbone.Collection.extend({
    url: function() { return ALL_TESTS_URL; },
    model: Test
//    parse: function(response) {
//        return response.objects;
//    }

});
