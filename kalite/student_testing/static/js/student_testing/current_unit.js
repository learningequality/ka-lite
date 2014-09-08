
window.CurrentUnitRowView = Backbone.View.extend({

    tagName: "tr",
    className: "current-unit",
    template: HB.template("student_testing/current-unit-row"),

    initialize: function(options) {
        _.bindAll(this);
        this.listenTo(this.model, "change:current_unit", this.render);
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    events: {
        'click button.previous': 'previous_button_clicked',
        'click button.next': 'next_button_clicked',
        'click a.selected-unit': 'unit_number_clicked'
    },

    unit_number_clicked: function(ev) {
        ev.preventDefault();
        var selected_unit = $(ev.target).data("selected-unit");
        this.set_unit(selected_unit);
    },

    previous_button_clicked: function(ev) {
        this.increment_current_unit(-1);
    },

    next_button_clicked: function(ev) {
        this.increment_current_unit(1);
    },

    increment_current_unit: function(amount) {
        var new_unit = this.model.get("current_unit") + amount;
        if ((new_unit >= this.model.get("min_unit")) && (new_unit <= this.model.get("max_unit"))) {
            this.set_unit(new_unit);
        }
    },

    set_unit: function(unit) {
        var check = confirm(gettext("Before changing units, make sure all students have finished purchasing items in the store, etc. Are you sure you want to change the current unit?"));
        if (!check) {
            return;
        }
        this.model.set("current_unit", unit);
        this.model.save();
    }

});


var CurrentUnitAppView = Backbone.View.extend({

    template: HB.template("student_testing/current-unit-container"),

    initialize: function() {
        _.bindAll(this);
        this.render();
        this.row_views = [];
        this.units = new CurrentUnitCollection();
        this.listenTo(this.units, 'add', this.add_unit);
        this.listenTo(this.units, 'reset', this.add_all_units);
        this.units.fetch().then(this.add_all_units);
    },

    render: function() {
        this.$el.html(this.template());
        return this;
    },

    add_unit: function(unit) {
        var view = new CurrentUnitRowView({model: unit});
        this.row_views.push(view);
        this.$("#current-units").append(view.render().el);
    },

    add_all_units: function() {
        _.each(this.row_views, function(row_view) {
            row_view.remove();
        });
        this.row_views = [];
        this.units.each(this.add_unit);
    }
});
