window.AvailableStoreItemModel = Backbone.Model.extend({

});

window.PurchasedStoreItemModel = Backbone.Model.extend({
    urlRoot: "/api/store/storetransactionlog/"
});

window.AvailableStoreItemCollection = Backbone.Collection.extend({

    url: "/api/store/storeitem/",

    model: AvailableStoreItemModel
});


window.PurchasedStoreItemCollection = Backbone.Collection.extend({

    model: PurchasedStoreItemModel,

    url: function() {
        return "/api/store/storetransactionlog/?" + $.param({
            user: statusModel.get("user_id")
        });
    }

});
