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
        this.playlist_id = options.playlist_id;
    },

    url: function() {
        var base = sprintf("%(playlist_url)s?user_id=%(user_id)s&playlist_id=", {"playlist_url": PLAYLIST_PROGRESS_DETAIL_URL, "user_id": STUDENT_ID});
        return base + this.playlist_id;
    }
});

// Views

var PlaylistProgressDetailView = Backbone.View.extend({

    template: HB.template('student_progress/playlist-progress-details'),

    initialize: function() {
        this.listenTo(this.collection, 'sync', this.render);
    },

    render: function() {
        this.$el.html(this.template({
            data: this.collection.models
        }));

        return this;
    }
});

var PlaylistProgressView = Backbone.View.extend({

    template: HB.template('student_progress/playlist-progress-container'),

    events: {
        "click .toggle-details": "toggle_details"
    },

    initialize: function() {
        this.details_fetched = false;

        this.detailed_view = new PlaylistProgressDetailView({
            collection: new PlaylistProgressDetailCollection([], {
                playlist_id: this.model.attributes.id
            })
        });

        this.listenTo(this.detailed_view.collection, "sync", this.render_details);
    },

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    },

    render_details: function() {
        this.$(".playlist-progress-details").html(this.detailed_view.render().el).show();

        // opt in bootstrap tooltip functionality
        $('.progress-indicator-sm').popover({
            trigger: 'click hover',
            animation: false
        });
    },

    toggle_details: function() {
        // Fetch data if we don't have it yet
        var self = this;
        if (!this.details_fetched) {
            this.detailed_view.collection.fetch({
                success: function() {
                    self.details_fetched = true;
                }
            });
        }

        // Show or hide details
        this.$(".expand-collapse").toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
        this.$(".playlist-progress-details").slideToggle();
    }
});

var StudentProgressContainerView = Backbone.View.extend({
    // The containing view
    template: HB.template('student_progress/student-progress-container'),

    initialize: function() {
        this.listenTo(this.collection, 'add', this.add_one);

        this.render();

        this.collection.fetch();
    },

    render: function() {
        // Only render container once
        this.$el.html(this.template());
    },

    add_one: function(playlist) {
        var view  = new PlaylistProgressView({
            model: playlist
        });
        this.$("#playlists-container").append(view.render().el);
    }
});

// Start the app on page load
$(function() {
    var container_view = new StudentProgressContainerView({
        el: $("#student-progress-container"),
        collection: new PlaylistProgressCollection()
    });
});
