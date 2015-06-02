window.TestListRowView = Backbone.View.extend({

    tagName: "tr",
    className: "test-row",
    template: HB.template("student_testing/test-list-row"),

    initialize: function(options) {
        this.listenTo(this.model, 'change', this.render);
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },
});


window.TestSettingAppView = Backbone.View.extend({

    template: HB.template("student_testing/test-setting-container"),

    initialize: function() {
        this.render();
        this.tests = new TestCollection();
        this.listenTo(this.tests, 'add', this.add_new_test);
        this.listenTo(this.tests, 'reset', this.add_all_tests);
        this.tests.fetch();
    },

    render: function() {
        this.$el.html(this.template());
        return this;
    },

    add_new_test: function(test) {
        var view = new TestListRowView({model: test});
        var grade = test.get("grade");
        this.$("#grade-" + grade + "-test").append(view.render().el);
    },

    add_all_tests: function() {
        this.tests.each(this.add_new_test);
    },

});


