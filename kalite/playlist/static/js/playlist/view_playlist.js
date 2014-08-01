
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
                    exercise_id: entry.get("entity_id")
                });
                this.content_view.show_view(view);
                break;

            case "Video":
                var view = new VideoWrapperView({
                    video_id: entry.get("entity_id")
                });
                this.content_view.show_view(view);
                break;

            case "Quiz":
                var view = new ExerciseQuizView({
                    quiz_model: new QuizDataModel({entry: entry})
                });
                this.content_view.show_view(view);
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

        // hide any messages being shown for the old view
        clear_messages();

        // close the currently shown view, if possible
        if (this.currently_shown_view) {
            // try calling the close method if available, otherwise remove directly
            if (_.isFunction(this.currently_shown_view.close)) {
                this.currently_shown_view.close();
            } else {
                this.currently_shown_view.remove();
            }
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

        var self = this;

        _.bindAll(this);

        this.render();

        this._entry_views = [];

        this.add_all_entries();

        this.listenTo(this.model.get('entries'), 'add', this.add_new_entry);
        this.listenTo(this.model.get('entries'), 'reset', this.add_all_entries);

        this.sidebar = this.$('').bigSlide({
            menu: this.$(".panel"),
            // push: "#page-container, #footer, .playlist-sidebar-tab",
            push: ".playlist-sidebar-tab",
            menuWidth: "220px"
        });

        this.$(".playlist-sidebar").slimScroll({
            height: "auto",
            color: "#033000",
            size: "8px",
            distance: "2px",
            disableFadeOut: true
        });

        // resize the scrollable part of sidebar to the page height
        $(window).resize(_.throttle(function() {
            var height = $(window).height() - self.$(".slimScrollDiv").position().top;
            self.$(".slimScrollDiv, .playlist-sidebar").height(height);
        }, 200));
        $(window).resize();

        this.state_model = new Backbone.Model({
            open: false
        });

        this.listenTo(this.state_model, "change:open", this.update_sidebar_visibility);

        this.$(".playlist-sidebar-tab").click(this.toggle_sidebar);

        // this.$(".playlist-sidebar-tab").hide();
        // setTimeout(function() { self.$(".playlist-sidebar-tab").show(); }, 5000);

        this.show_sidebar();

        _.defer(function() {
            self.$("a:first").click();
        });

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    toggle_sidebar: function(ev) {
        // this.$(".playlist-sidebar-tab").css("color", this.state_model.get("open") ? "red" : "blue")
        this.state_model.set("open", !this.state_model.get("open"));
        ev.preventDefault();
        return false;
    },

    update_sidebar_visibility: function() {
        if (this.state_model.get("open")) {
            this.sidebar.open();
        } else {
            this.sidebar.close();
        }
    },

    show_sidebar: function() {
        this.state_model.set("open", true);
    },

    hide_sidebar: function() {
        this.state_model.set("open", false);
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
        this.hide_sidebar();
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

    tagName: "li",

    template: HB.template("playlists/playlist-sidebar-entry"),

    events: {
        "click": "clicked"
    },

    initialize: function() {

        _.bindAll(this);

        this.listenTo(this.model, "change:active", this.render);

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    clicked: function(ev) {
        ev.preventDefault();
        this.trigger("clicked", this);
        return false;
    },

});

