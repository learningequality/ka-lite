var units = new CurrentUnitList();


var error_func = function (model, resp) {
    handleFailedAPI(resp);
    units.fetch();
};


var success_func = function (model, resp) {
    handleSuccessAPI(resp);
    units.fetch();
};


var CurrentUnitView = Backbone.View.extend({
    tagName: "tr",
    className: "current-unit",
    template: HB.template("student_testing/current-unit-row"),
    initialize: function (options) {
        this.render();
    },
    render: function () {
        var variables = this.model.toJSON();
        this.$el.html(this.template(variables));
        return this;
    },
    events: {
        'click button.previous': 'set_previous',
        'click button.next': 'set_next',
        'click a.selected-unit': 'set_unit'
    },
    set_current_unit: function (ev, is_previous, is_next) {
        ev.preventDefault();
        var selected_unit = ev.target.dataset.selectedUnit;
        var current_unit = this.model.get('current_unit');
        data = {
            'is_previous': is_previous,
            'is_next': is_next,
            'current_unit': current_unit,
            'selected_unit': selected_unit
        };
        this.model.save(data, {error: error_func, success: success_func});
    },
    set_unit: function (ev) {
        this.set_current_unit(ev, false, false);
    },
    set_previous: function (ev) {
        this.set_current_unit(ev, true, false);
    },
    set_next: function (ev) {
        this.set_current_unit(ev, false, true);
    }
});


var AppView = Backbone.View.extend({
    initialize: function () {
        this.listenTo(units, 'sync', this.add_all_units);
        units.fetch();
    },
    add_unit: function (unit, collection, options) {
        var view = new CurrentUnitView({model: unit});
        $("#current-units").append(view.render().el);
    },
    add_all_units: function (model, response, options) {
        // clear the rows
        $("#current-units").find("tr.current-unit").remove();
        units.each(this.add_unit);
    }
});


$(function () {
    var app = new AppView;
});
