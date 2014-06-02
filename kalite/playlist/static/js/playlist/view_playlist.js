
window.PlaylistView = Backbone.View.extend({

    initialize: function() {

        var self = this;

        _.bindAll(this);

        this.render();

        this.content_view = new PlaylistContentAreaView({
            el: this.$el
        });

        this.model.fetch()
            .then(function() {
                self.sidebar_view = new PlaylistSidebarView({
                    // el: self.$("..."),
                    model: self.model
                });

                self.listenTo(self.sidebar_view, "entry_requested", self.entry_requested);

            });

    },

    render: function() {

    },

    entry_requested: function(entry) {
        switch(entry.get("entity_kind")) {
            case "Exercise":
                var view = new ExercisePracticeView({
                    // el: $(".exercise-wrapper"),
                    exercise_id: entry.get("entity_id")
                });
                this.content_view.show_view(view);
                // view.exercise_view.khan_loaded()
                break;

        }
    }


});

window.PlaylistContentAreaView = Backbone.View.extend({

    template: HB.template("playlists/playlist-content-area"),

    initialize: function() {

        _.bindAll(this);

        this.model = new Backbone.Model();

        this.render();

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    show_view: function(view) {
        // close the currently shown view, if possible
        if (this.currently_shown_view && _.isFunction(this.currently_shown_view.close)) {
            this.currently_shown_view.close();
        }
        // set the new view as the current view
        this.currently_shown_view = view;
        // show the view
        this.$(".playlist-content").html("").append(view.$el);
    }

});

window.PlaylistSidebarView = Backbone.View.extend({

    el: ".playlist-sidebar-wrapper",

    template: HB.template("playlists/playlist-sidebar"),

    initialize: function() {

        _.bindAll(this);

        this.render();

        this._entry_views = [];

        this.add_all_entries();

        this.listenTo(this.model.get('entries'), 'add', this.add_new_entry);
        this.listenTo(this.model.get('entries'), 'reset', this.add_all_entries);

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    add_new_entry: function(entry) {
        var view = new PlaylistSidebarEntryView({model: entry});
        this._entry_views.push(view);
        this.$(".playlist-sidebar").append(view.render().$el);
        this.listenTo(view, "clicked", this.item_clicked);
    },

    add_all_entries: function() {
        this.render();
        this.model.get('entries').map(this.add_new_entry);
    },

    item_clicked: function(view) {
        // only trigger an entry_requested event if the item wasn't already active
        if (!view.model.get("active")) {
            this.trigger("entry_requested", view.model);
        }
        // mark the clicked view as active, and unmark all the others
        _.each(this._entry_views, function(v) {
            v.model.set("active", v == view);
        });
    }

});

window.PlaylistSidebarEntryView = Backbone.View.extend({

    tagName: "ul",

    template: HB.template("playlists/playlist-sidebar-entry"),

    events: {
        "click .playlist-sidebar-entry-link": "clicked"
    },

    initialize: function() {

        _.bindAll(this);

        this.listenTo(this.model, "change:active", this.render);

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    clicked: function() {
        this.trigger("clicked", this);
        return false;
    },

});

