window.StoreItemModel = Backbone.Model.extend({

});


window.AvailableStoreItemCollection = Backbone.Collection.extend({

    url: "/api/store/storeitem/",

    model: StoreItemModel
});


window.PurchasedStoreItemCollection = Backbone.Collection.extend({

    model: StoreItemModel,

    url: function() {
        return "/api/store/storetransactionlog/?" + $.param({
            user: statusModel.get("user_id")
        });
    }

});


window.StoreStateModel = Backbone.Collection.extend({
    defaults: {
        points_remaining: 0
    }
})