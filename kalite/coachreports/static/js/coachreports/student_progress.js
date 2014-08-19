// Handles the data export functionality of the control panel

// Models 
var PlaylistProgressModel = Backbone.Model.extend();

var PlaylistProgressDetailModel = Backbone.Model.extend();

// Collections
var PlaylistProgressCollection = Backbone.Collection.extend({
    model: PlaylistProgressModel,
    url: sprintf("%(playlist_url)s?user_id=%(user_id)s", {"playlist_url": PLAYLIST_PROGRESS_URL, "user_id": STUDENT_ID})
});

var PlaylistProgressDetailCollection = Backbone.Collection.extend({
    model: PlaylistProgressDetailModel,

    initialize: function(models, options) {
        console.log("A new PlaylistProgressDetailCollection was born!");
        this.playlist_id = options.playlist_id;
    },

    url: function() {
        var base = sprintf("%(playlist_url)s?user_id=%(user_id)s&playlist_id=", {"playlist_url": PLAYLIST_PROGRESS_URL, "user_id": STUDENT_ID});
        window.dat = this;
        return base + this.playlist_id;
    }
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
        // Render container once
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

    events: {
        "click .show-details": "showDetailedReport"
    },

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    },

    showDetailedReport: function(e) {
        console.log("button click for " + this.model.attributes.id)
        var self = this; // TODO(dylan): is this needed? 
        var view = new PlaylistProgressDetailView({
            collection: new PlaylistProgressDetailCollection([], {
                playlist_id: this.model.attributes.id 
            })
        });
    }
});

var PlaylistProgressDetailView = Backbone.View.extend({

    template: HB.template('student_progress/playlist-progress-details'),

    initialize: function() {
        console.log("A new PlaylistProgressDetailView was born!")

        this.listenTo(this.collection, 'sync', this.render)

        this.collection.fetch();

        window.dat = this;
    },

    render: function() {
        console.log("Le render de le progress details is le happening.");
    }
})

// Start the app on page load
$(function() {
    var container_view = new StudentProgressContainerView({
        el: $("#student-progress-container")
    });
});