window.StoreWrapperView = Backbone.View.extend({

    template: HB.template("store/store-wrapper"),

    events: {

    },

    initialize: function() {

        _.bindAll(this);

        this.render();

        this.available_items = new AvailableStoreItemCollection;
        this.purchased_items = new PurchasedStoreItemCollection;

        this.available_item_view = new AvailableStoreItemListView({
            collection: this.available_items,
            el: this.$(".available-store-items")
        });

        this.purchased_item_view = new PurchasedStoreItemListView({
            collection: this.purchased_items,
            el: this.$(".purchased-store-items")
        });

        this.available_items.fetch();
        this.purchased_items.fetch();

        this.listenTo(statusModel, "change:totalpoints", this.update_points);

    },

    render: function() {
        this.$el.html(this.template({
            points: statusModel.get("totalpoints")
        }));
        return this;
    },

    update_points: function() {
        this.$(".points-remaining").text(statusModel.get("totalpoints"));
    }

});


window.AvailableStoreItemListView = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.item_views = [];

        this.listenTo(this.collection, "add", this.add_item);
        this.listenTo(this.collection, "reset", this.add_all_items);
    },

    add_item: function(item) {
        var view = new AvailableStoreItemView({
            model: item
        });
        this.$el.append(view.render().el);
        this.item_views.push(view);
    },

    add_all_items: function() {
        _.each(this.item_views, function(view) {
            view.remove();
        });
        this.collection.each(this.add_item);
    }

});


window.PurchasedStoreItemListView = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.item_views = [];

        this.listenTo(this.collection, "add", this.add_item);
        this.listenTo(this.collection, "reset", this.add_all_items);
    },

    add_item: function(item) {
        var view = new PurchasedStoreItemView({
            model: item
        });
        this.$el.append(view.render().el);
        this.item_views.push(view);
    },

    add_all_items: function() {
        _.each(this.item_views, function(view) {
            view.remove();
        });
        this.collection.each(this.add_item);
    }

});


window.AvailableStoreItemView = Backbone.View.extend({

    template: HB.template("store/available-store-item"),

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    }

});

window.PurchasedStoreItemView = Backbone.View.extend({

    template: HB.template("store/purchased-store-item"),

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    }

});

