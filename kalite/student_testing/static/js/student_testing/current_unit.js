var units = new CurrentUnitList;

var CurrentUnitView = Backbone.View.extend({
    tagName: "tr",
    className: "current-unit-row",
    template: _.template($("#all-current-unit-entry-template").html()),
    initialize: function(options) {
        console.log('==> initialize', this);
//        this.facility_name = this.model.get('facility_name');
        this.listenTo(this.model, 'change', this.render);
    },
    render: function() {
        console.log('==> render', this);
        var dict = this.model.toJSON();
        console.log('====> render', dict, this.template(dict));
        this.$el.html(this.template(dict));
        return this;
    },
    events: {
        'click button.previous': 'setPrevious',
        'click button.next': 'setNext'
    },
    setPrevious: function(ev) {
        ev.preventDefault();
        console.log('==> setPrevious');
    },
    setNext: function(ev) {
        ev.preventDefault();
        console.log('==> setNext');
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
