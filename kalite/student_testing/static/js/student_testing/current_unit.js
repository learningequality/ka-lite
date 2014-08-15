var units = new CurrentUnitList;


var error_func = function (model, resp) {
//    console.log('==> error_func', 'model==', model, 'resp==', resp);
    handleFailedAPI(resp);
    units.fetch({data: {'force': true}});
};

var success_func = function (model, resp) {
    // force to render the list
//    console.log('==> success_func', 'model==', model, 'resp==', resp);
    handleSuccessAPI(resp);
    units.fetch({data: {'force': true}});
};


var CurrentUnitView = Backbone.View.extend({
    tagName: "tr",
    className: "current-unit",
    template: HB.template("student_testing/current-unit-row"),
    initialize: function (options) {
        this.listenTo(this.model, 'change', this.render);
//        console.log('======> CurrentUnitView initialize', this);
        _.bindAll(this);
        this.render();
    },
    render: function () {
        var variables = this.model.toJSON();
        var template = this.$el.html(this.template(variables));
//        console.log('======> CurrentUnitView render', this, 'template==', template);
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
        this.listenTo(units, 'add', this.add_new_unit);
        this.listenTo(units, 'reset', this.add_all_units);
//        this.listenTo(units, 'sync', this.add_all_units);
        units.fetch();
//        console.log('==> AppView.initialize', units);
    },
    add_new_unit: function (unit) {
        var view = new CurrentUnitView({model: unit});
        $("#current-units").append(view.render().el);
    },
    add_all_units: function () {
        units.each(this.add_new_unit);
    }
});


$(function () {
    var app = new AppView;
});
