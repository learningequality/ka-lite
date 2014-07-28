var PlaylistTableView = Backbone.View.extend({

    initialize: function() {
        this.render();
    },

    render: function() {
      var variables = { title: "Assigned Playlists" };
      var template = _.template($("#playlist-table").html(), variables);
      this.$el.html(template);
    },

    add_playlist: function(playlist) {
        var format = formatPlaylist(playlist.toJSON());
        this.$el.find("#playlists").append(format);
    }

});

var AppView = Backbone.View.extend({

    initialize: function() {

        $("#playlist-table-container").hide(); // hide the playlist table regardless
        $(".loading").hide();

        this.listenTo(window.statusModel, "sync", this.setup_elements_for_user);
    },

    setup_elements_for_user: function(statusModel) {

        // check to see if we are a student. If so, render the playlist table
        // and fetch the data to populate it
        if (statusModel.get('is_logged_in') && !statusModel.get('is_admin')) { // we're a student

            var playlists = new PlaylistList();

            this.listenTo(playlists, "sync", this.display_playlist_table);

            $(".loading").show();
            playlists.fetch();
        }
    },

    display_playlist_table: function(playlists) {

        var playlist_table_view = new PlaylistTableView({ el: $("#playlist-table-container") });

        // TODO (aron): transfer to proper playlist view.  Did this to
        // make things closer to how jomel implemented things
        playlists.map(function(playlist) {
            playlist_table_view.add_playlist(playlist);
        });

        $(".loading").hide();
        $("#playlist-table-container").show();

        $(".cell-content").dotdotdot({
            ellipsis: '...',
            wrap: 'word',
            fallbackToLetter: true,
            after: null,
            watch: false,
            height: null,
            tolerance: 0
        });

    }

});

$(function() {

    var app = new AppView();

});


function formatPlaylist(data) {
    data.num_videos = data.entries.filter(function(e) { return e.get('entity_kind') == 'Video'; }).length;
    data.num_exercises = data.entries.filter(function(e) { return e.get('entity_kind') == 'Exercise'; }).length;
    data.playlist_link = sprintf(VIEW_PLAYLIST_TEMPLATE_URL, {playlist_id: data.id});
    var format = HB.template("playlist/homepage-playlists-table-cell");
    return format(data);


}
