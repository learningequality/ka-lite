// Handles the data export functionality of the control panel

// Models 
var PlaylistProgressModel = Backbone.Model.extend();

// Collections
var PlaylistProgressCollection = Backbone.Collection.extend({
    model: PlaylistProgressModel,
    url: sprintf("%(playlist_url)s?user_id=%(user_id)s", {"playlist_url": PLAYLIST_PROGRESS_URL, "user_id": STUDENT_ID})
});

var Playlists = new PlaylistProgressCollection;

// Views 
var StudentProgressContainerView = Backbone.View.extend({
    // The containing view
    template: HB.template('student_progress/student-progress-container'),

    initialize: function() {
        // handle changes to the playlist collection
        this.listenTo(Playlists, 'add', this.addOne);

        this.render();

        Playlists.fetch();
    },

    render: function() {
        // Render container
        this.$el.html(this.template());
    },

    addOne: function(playlist) {
        var view  = new PlaylistProgressView({
            model: playlist
        });
        this.$("#playlists-container").append(view.render().el); 
    }
});

var PlaylistProgressView = Backbone.View.extend({

    template: HB.template('student_progress/playlist-progress-container'),

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    }
});

// Start up the app 
$(function() {
    var container_view = new StudentProgressContainerView({
        el: $("#student-progress-container")
    });
});