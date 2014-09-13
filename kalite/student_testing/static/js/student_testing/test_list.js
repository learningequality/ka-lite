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

    events: {
        'click button': 'exam_mode_toggle_button_clicked'
    },

    exam_mode_toggle_button_clicked: function(ev) {

        this.trigger("exam_mode_toggle", this.model);

    }

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
        this.listenTo(view, "exam_mode_toggle", this.exam_mode_toggle);
        this.$("#tests").append(view.render().el);
    },

    add_all_tests: function() {
        this.tests.each(this.add_new_test);
    },

    exam_mode_toggle: function(test) {

        // check exam_mode state of the selected test
        var is_exam_mode = test.get('is_exam_mode');

        // clear exam mode for all other tests
        // (no need to save since toggling current test will overwrite Setting)
        this.tests.each(function(t) {
            if (t.get("is_exam_mode")) {
                t.set("is_exam_mode", false);
            }
        });

        // toggle the exam state of the current test (and save)
        test.set("is_exam_mode", !is_exam_mode);
        test.save();
    }

});


