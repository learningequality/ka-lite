var playlist = new Playlist({id: CURRENT_PLAYLIST_ID});

var PlaylistView = Backbone.View.extend({

    initialize: function() {
        _.bindAll(this);
        this.listenTo(this.model.get('entries'), 'add', this.addNewEntry);
        this.listenTo(this.model.get('entries'), 'reset', this.addAllEntries);

        this.addAllEntries();
    },

    addNewEntry: function(entry) {
        var view = new PlaylistEntrySidebarView({model: entry});
        $("#playlist-items").append(view.render().el);
    },

    addAllEntries: function() {
        this.model.get('entries').map(this.addNewEntry);
    }
});

var PlaylistEntrySidebarView = Backbone.View.extend({

    id: "playlist-item",

    template: _.template($("#playlist-sidebar-entry-template").html()),

    render: function() {
        var dict = this.model.toJSON();
        this.$el.html(this.template(dict));

        return this;
    }
});

var AppView = Backbone.View.extend({

    initialize: function() {
        this.listenTo(playlist, "sync", this.renderPlaylist);
        playlist.fetch();
    },

    renderPlaylist: function(playlist) {
        var view = new PlaylistView({model: playlist});
    }

});

$(function() {

    var app = new AppView;

});
