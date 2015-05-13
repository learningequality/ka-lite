var TabularReportView = BaseView.extend({

    template: HB.template("tabular_reports/tabular-view"),

    initialize: function() {
        _.bindAll(this);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({students: students, exercises: exercises}));
    }

});
