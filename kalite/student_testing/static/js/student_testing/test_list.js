var tests = new TestList;

var TestView = Backbone.View.extend({
    tagName: "tr",
    className: "test-row",
    template: _.template($("#all-tests-list-entry-template").html()),
    initialize: function(options) {
        this.title = this.model.get('title');
        this.listenTo(this.model, 'change', this.render);
    },
    render: function() {
        var dict = this.model.toJSON();
        this.$el.html(this.template(dict));
        return this;
    },
    events: {
        'click button': 'setExamMode'
    },
    setExamMode: function(ev) {
        ev.preventDefault();

        // toggle exam_mode state of the selected test
        var isExamMode = ! this.model.get('is_exam_mode');
        var errorFunc = function() {
            // make sure we render the list of tests with the one set to exam mode
            tests.fetch();
            alert("Did not successfully set the test into exam mode.  Try to reload the page.");
        };
        var successFunc = function() {
            // make sure we render the list of tests with the one set to exam mode
            tests.fetch();
        };
        this.model.save({is_exam_mode: isExamMode}, {error: errorFunc, success: successFunc});
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
