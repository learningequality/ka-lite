var Backbone = require("base/backbone");
var Handlebars = require("base/handlebars");
var messages = require("utils/messages");
var Models = require("./models");


var PlaylistProgressDetailView = Backbone.View.extend({

    template: require('./hbtemplates/playlist-progress-details.handlebars'),

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

    template: require('./hbtemplates/playlist-progress-container.handlebars'),

    events: {
        "click .toggle-details": "toggle_details"
    },

    initialize: function(options) {
        this.details_fetched = false;

        this.detailed_view = new PlaylistProgressDetailView({
            collection: new Models.PlaylistProgressDetailCollection([], {
                playlist_id: this.model.attributes.id,
                user_id: options.user_id
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
        this.$('.progress-indicator-sm').popover({
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
    template: require('./hbtemplates/student-progress-container.handlebars'),

    initialize: function(options) {
        this.user_id = options.user_id;

        this.collection =  new Models.PlaylistProgressCollection([], {user_id: this.user_id});

        this.listenTo(this.collection, 'add', this.add_one);
        
        var self = this;

        this.render();

        this.collection.fetch({
            success: function() {
                 if (self.collection.length === 0) {       //if the student visits the my progress page before attempting any quizes/videos
                              if (window.statusModel.is_student()) {
                                  messages.show_message("info", gettext("Click on the LEARN button above to get started on your learning journey."));
                              }
                              self.$el.html("");             //this is done to remove the 'Progress Report' header
                      }
                   }
               });
    },

    render: function() {
        // Only render container once
        this.$el.html(this.template());
    },

    add_one: function(playlist) {
        var view  = new PlaylistProgressView({
            model: playlist,
            user_id: this.user_id
        });
        this.$("#playlists-container").append(view.render().el);
    }
});

module.exports = {
    StudentProgressContainerView: StudentProgressContainerView,
    PlaylistProgressView: PlaylistProgressView,
    PlaylistProgressDetailView: PlaylistProgressDetailView
};
