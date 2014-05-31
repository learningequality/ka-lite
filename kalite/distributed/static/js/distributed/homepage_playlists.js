var PlaylistTableView = Backbone.View.extend({

    initialize: function() {


    }

});

var AppView = Backbone.View.extend({

    initialize: function() {

        $("#playlist-table").hide(); // hide the playlist table regardless
        $(".loading").hide();

        this.listenTo(window.statusModel, "sync", this.setupElementsForUser);
    },

    setupElementsForUser: function(statusModel) {

        // check to see if we are a student. If so, render the playlist table
        // and fetch the data to populate it
        if (statusModel.get('is_logged_in') && !statusModel.get('is_admin')) { // we're a student

            var playlists = new PlaylistList;

            this.listenTo(playlists, "sync", this.displayPlaylistTable);

            $(".loading").show();
            playlists.fetch();
        }
    },

    displayPlaylistTable: function(playlists) {

        // TODO (aron): transfer to proper playlist view.  Did this to
        // make things closer to how jomel implemented things
        playlists.map(function(playlist) {
            var format = formatPlaylist(playlist.toJSON());
            $("#playlists").append(format);
        });

        $(".loading").hide();
        $("#playlist-table").show();

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

    var app = new AppView;

});


function formatPlaylist(data) {
    data.numVideos = data.entries.filter(function(e) { return e.get('entity_kind') == 'Video'; }).length;
    data.numExercises = data.entries.filter(function(e) { return e.get('entity_kind') == 'Exercise'; }).length;
    var format = HB.template("playlists/homepage-playlists-table-cell");
    return format(data);


}
