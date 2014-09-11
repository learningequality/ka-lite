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
            el: this.$(".purchased-store-items"),
            available_items: this.available_items
        });

        this.available_items.fetch();
        this.purchased_items.fetch();

        this.listenTo(statusModel, "change:totalpoints", this.update_points);

        this.listenTo(this.available_item_view, "purchase_requested", this.make_purchase);

    },

    render: function() {
        this.$el.html(this.template({
            points: statusModel.get("totalpoints")
        }));
        return this;
    },

    update_points: function() {
        this.$(".points-remaining").text(statusModel.get("totalpoints"));
    },

    make_purchase: function(item) {
        var points_remaining = statusModel.get("totalpoints");
        var cost = item.get("cost");

        if (cost > points_remaining) {
            alert("Sorry, you don't have enough points to purchase that right now.");
            return;
        }

        var purchased_model = new PurchasedStoreItemModel({
            item: item.id,
            purchased_at: statusModel.get_server_time(),
            reversible: item.get("returnable"),
            context_id: 0, // TODO-BLOCKER: put the current unit in here
            context_type: "unit",
            user: statusModel.get("user_uri"),
            value: -cost
        });

        purchased_model.save();

        // add the item to the collection of purchased items so it will show in that list
        this.purchased_items.add(purchased_model);

        // decrement the visible number of remaining points
        statusModel.set("newpoints", statusModel.get("newpoints") - cost);

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
        if(item.get("shown")){
            var self = this;
            var view = new AvailableStoreItemView({
                model: item
            });
            this.$el.append(view.render().el);
            this.item_views.push(view);
            this.listenTo(view, "purchase_requested", function(item) { self.trigger("purchase_requested", item); });
        }
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

    add_item: function(model) {
        var item = this.options.available_items.get(model.get("item"))
        if (item && item.get("shown")) {
            var view = new PurchasedStoreItemView({
                model: model,
                available_items: this.options.available_items
            });
            this.$el.append(view.render().el);
            this.item_views.push(view);
        }
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

    events: {
        "click .store-item-purchase-button": "purchase_button_clicked"
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    purchase_button_clicked: function(ev) {
        $(ev.target)
            .switchClass("btn-primary", "btn-success", 100)
            .switchClass("btn-success", "btn-primary", 400);
        this.trigger("purchase_requested", this.model);
    }

});

window.PurchasedStoreItemView = Backbone.View.extend({

    template: HB.template("store/purchased-store-item"),

    render: function() {
        // retrieve the item object itself, for rendering
        var item = this.options.available_items.get(this.model.get("item"));
        this.$el.html(this.template(item.attributes));
        return this;
    }

});

