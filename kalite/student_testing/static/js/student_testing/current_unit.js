var units = new CurrentUnitList;

var errorFunc = function(model, resp) {
//    alert("Did not successfully set the current unit.  Try to reload the page.");
//    console.log('==> errorFunc', 'model==', model, 'resp==', resp);
    handleFailedAPI(resp)
    units.fetch({data: {'force': true}});
};

var successFunc = function(model, resp) {
    // force to render the list
//    console.log('==> successFunc', 'model==', model, 'resp==', resp);
    handleSuccessAPI(resp)
    units.fetch({data: {'force': true}});
};


var CurrentUnitView = Backbone.View.extend({
    tagName: "tr",
    className: "current-unit",
    template: _.template($("#all-current-unit-entry-template").html()),
    initialize: function(options) {
//        console.log('==> initialize', this);
//        this.facility_name = this.model.get('facility_name');
        this.listenTo(this.model, 'change', this.render);
    },
    render: function() {
        console.log('==> render', this, this.model.get('facility_name'));
        var dict = this.model.toJSON();
//        console.log('====> render', dict, this.template(dict));
        this.$el.html(this.template(dict));
        return this;
    },
    events: {
        'click button.previous': 'set_previous',
        'click button.next': 'set_next',
        'click a.selected-unit': 'set_unit'
    },
    set_current_unit: function(ev, is_previous, is_next) {
        ev.preventDefault();
        var selected_unit = ev.target.dataset.selectedUnit;
        var current_unit = this.model.get('current_unit');
        data = {
            'is_previous': is_previous,
            'is_next': is_next,
            'current_unit': current_unit,
            'selected_unit': selected_unit
        };
        this.model.save(data, {error: errorFunc, success: successFunc});
    },
    set_unit: function(ev) {
        this.set_current_unit(ev, false, false);
    },
    set_previous: function(ev) {
        this.set_current_unit(ev, true, false);
    },
    set_next: function(ev) {
        this.set_current_unit(ev, false, true);
    }
});


var AppView = Backbone.View.extend({
    initialize: function() {
        this.listenTo(units, 'add', this.addNewUnit);
        this.listenTo(units, 'reset', this.addAllUnits);
//        this.listenTo(units, 'sync', this.addAllUnits);
        units.fetch();
        console.log('==> AppView.initialize', units);
    },
    addNewUnit: function(unit) {
        console.log('==> unit', unit);
        var view = new CurrentUnitView({model: unit});
        $("#current-units").append(view.render().el);
    },
    addAllUnits: function() {
        console.log('==> addAllUnits', units);
        units.each(this.addNewUnit);
    }
});


$(function() {
//    $("tr.facility_name+tr").hide();
    var app = new AppView;
});
