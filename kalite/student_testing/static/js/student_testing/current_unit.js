var units = new CurrentUnitList;

var errorFunc = function() {
    units.fetch({data: {'force': true}});
    alert("Did not successfully set the current unit.  Try to reload the page.");
};
var successFunc = function() {
    // force to render the list
    units.fetch({data: {'force': true}});
};

var CurrentUnitView = Backbone.View.extend({
    tagName: "tr",
    className: "current-unit-row",
    template: _.template($("#all-current-unit-entry-template").html()),
    initialize: function(options) {
//        console.log('==> initialize', this);
//        this.facility_name = this.model.get('facility_name');
        this.listenTo(this.model, 'change', this.render);
    },
    render: function() {
//        console.log('==> render', this);
        var dict = this.model.toJSON();
//        console.log('====> render', dict, this.template(dict));
        this.$el.html(this.template(dict));
        return this;
    },
    events: {
        'click button.previous': 'setPrevious',
        'click button.next': 'setNext',
        'click a.selected-unit': 'setUnit'
    },
    setUnit: function(ev) {
        ev.preventDefault();
//        console.log('==> setUnit', this, ' ev ==', ev);
        var selectedUnit = ev.target.dataset.selectedUnit;
        var currentUnit = this.model.get('current_unit');
        data = {
            'is_previous': false,
            'is_next': false,
            'current_unit': currentUnit,
            'selected_unit': selectedUnit
        };
        this.model.save(data, {error: errorFunc, success: successFunc});
    },
    setPrevious: function(ev) {
        ev.preventDefault();
//        console.log('==> setPrevious');
        var selectedUnit = 0;
        var currentUnit = this.model.get('current_unit');
        data = {
            'is_previous': true,
            'is_next': false,
            'current_unit': currentUnit,
            'selected_unit': selectedUnit
        };
        this.model.save(data, {error: errorFunc, success: successFunc});
    },
    setNext: function(ev) {
        ev.preventDefault();
//        console.log('==> setNext', this.model);
        var selectedUnit = 0;
        var currentUnit = this.model.get('current_unit');
        data = {
            'is_previous': false,
            'is_next': true,
            'current_unit': currentUnit,
            'selected_unit': selectedUnit
        };
        this.model.save(data, {error: errorFunc, success: successFunc});
    }

});


var AppView = Backbone.View.extend({
    initialize: function() {
        this.listenTo(units, 'add', this.addNewUnit);
        this.listenTo(units, 'reset', this.addAllUnits);
//        this.listenTo(units, 'sync', this.addAllUnits);
        units.fetch();
//        console.log('==> AppView.initialize', units);
    },
    addNewUnit: function(unit) {
//        console.log('==> unit', unit);
        var view = new CurrentUnitView({model: unit});
        $("#current-units").append(view.render().el);
    },
    addAllUnits: function() {
//        console.log('==> addAllUnits', units);
        units.each(this.addNewUnit);
    }
});


$(function() {
//    $("tr.facility_name+tr").hide();
    var app = new AppView;
});
