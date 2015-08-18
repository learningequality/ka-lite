var Backbone = require("base/backbone");
var sprintf = require("sprintf-js").sprintf;

var PlaylistProgressModel = Backbone.Model.extend();

var PlaylistProgressDetailModel = Backbone.Model.extend();

// Collections
var PlaylistProgressCollection = Backbone.Collection.extend({
    model: PlaylistProgressModel,

    initialize: function(model, options) {
        this.user_id = options.user_id;
    },

    url: function() {
        return sprintf("%(playlist_url)s?user_id=%(user_id)s", {"playlist_url": PLAYLIST_PROGRESS_URL, "user_id": this.user_id});
    }
});

var PlaylistProgressDetailCollection = Backbone.Collection.extend({
    model: PlaylistProgressDetailModel,

    initialize: function(models, options) {
        this.playlist_id = options.playlist_id;
        this.user_id = options.user_id;
    },

    url: function() {
        var base = sprintf("%(playlist_url)s?user_id=%(user_id)s&playlist_id=", {"playlist_url": PLAYLIST_PROGRESS_DETAIL_URL, "user_id": this.user_id});
        return base + this.playlist_id;
    }
});

module.exports = {
    PlaylistProgressModel: PlaylistProgressModel,
    PlaylistProgressDetailModel: PlaylistProgressDetailModel,
    PlaylistProgressCollection: PlaylistProgressCollection,
    PlaylistProgressDetailCollection: PlaylistProgressDetailCollection
};