window.StoreWrapperView = Backbone.View.extend({

    template: HB.template("store/store-wrapper"),

    events: {

    },

    initialize: function() {

        _.bindAll(this);

        this.render();

        this.purchased_items = new PurchasedStoreItemCollection;
        this.available_items = new AvailableStoreItemCollection;

        this.purchased_items.fetch();
        this.available_items.fetch();

    },

    render: function() {
        this.$el.html(this.template()); // this.model.attributes
        return this;
    },

});


window.AvailableStoreItemListView = Backbone.View.extend({

    item_template: HB.template("store/available-store-item"),

    initialize: function() {
        this.listenTo(this.collection, "add", this.add_item);
        this.listenTo(this.collection, "reset", this.add_all_items);
    },

    add_item: function(item) {
        console.log(item);
    },

    add_all_items: function() {
        this.$el.html("");

    }

});


window.PurchasedStoreItemListView = Backbone.View.extend({

    item_template: HB.template("store/store-item"),

    initialize: function() {
        this.listenTo(this.collection, "add", this.add_item);
        this.listenTo(this.collection, "reset", this.add_all_items);
    },

    add_item: function(item) {
        console.log(item);
    },

    add_all_items: function() {
        this.$el.html("");

    }

});


window.AvailableStoreItemView = Backbone.View.extend({

    item_template: HB.template("store/available-store-item")

});

window.PurchasedStoreItemView = Backbone.View.extend({

    item_template: HB.template("store/purchased-store-item")



});

