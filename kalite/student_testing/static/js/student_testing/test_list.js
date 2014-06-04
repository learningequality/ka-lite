var tests = new TestList;

var TestView = Backbone.View.extend({

    tagName: "tr",

    className: "test-row",

    template: _.template($("#all-tests-list-entry-template").html()),

    initialize: function(options) {
        this.title = this.model.title;
        this.listenTo(this.model, 'change', this.render);
    },

    render: function() {
        var dict = this.model.toJSON();
        this.$el.html(this.template(dict));
        return this;
    }

});


var AppView = Backbone.View.extend({

    initialize: function() {
        this.listenTo(tests, 'add', this.addNewTest);
        this.listenTo(tests, 'reset', this.addAllTests);

        tests.fetch();
    },

    addNewTest: function(test) {
        var view = new TestView({model: test});
        $("#tests").append(view.render().el);
    },

    addAllTests: function() {
        tests.each(this.addNewTest);
    }

});


$(function() {
    $("tr.title+tr").hide();
    var app = new AppView;
});
