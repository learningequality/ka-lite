
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
                    model: new VideoPlayerModel(
                        // TODO-BLOCKER(jamalex): get actual video data loading for this
                        {"ancestor_ids": ["root", "math", "arithmetic", "addition-subtraction", "basic_addition"], "available": true, "description": "Introduction to addition. Multiple visual ways to represent addition.", "duration": 462, "keywords": "Math, Addition, Khan, Academy, CC_1_OA_1, CC_1_OA_2, CC_1_OA_3, CC_1_OA_6", "related_exercise": {"path": "/math/arithmetic/addition-subtraction/basic_addition/e/addition_1/", "slug": "addition_1", "id": "addition_1", "title": "1-digit addition"}, "video_urls": {"stream": "/content/AuX7nPBqDts.mp4", "on_disk": true, "stream_type": "video/mp4", "language_name": "English", "thumbnail": "/content/AuX7nPBqDts.png", "subtitles": [{"url": "/static/srt/ar/subtitles/AuX7nPBqDts.srt", "code": "ar", "name": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"}, {"url": "/static/srt/es/subtitles/AuX7nPBqDts.srt", "code": "es", "name": "Espa\u00f1ol, Castellano"}]}, "dubs_available": true, "download_urls": {"mp4": "http://s3.amazonaws.com/KA-youtube-converted/AuX7nPBqDts.mp4/AuX7nPBqDts.mp4", "png": "http://s3.amazonaws.com/KA-youtube-converted/AuX7nPBqDts.mp4/AuX7nPBqDts.png", "m3u8": "http://s3.amazonaws.com/KA-youtube-converted/AuX7nPBqDts.m3u8/AuX7nPBqDts.m3u8"}, "path": "/math/arithmetic/addition-subtraction/basic_addition/v/basic-addition/", "availability": {"en": {"stream": "/content/AuX7nPBqDts.mp4", "on_disk": true, "stream_type": "video/mp4", "language_name": "English", "thumbnail": "/content/AuX7nPBqDts.png", "subtitles": [{"url": "/static/srt/ar/subtitles/AuX7nPBqDts.srt", "code": "ar", "name": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"}, {"url": "/static/srt/es/subtitles/AuX7nPBqDts.srt", "code": "es", "name": "Espa\u00f1ol, Castellano"}]}, "es": {"language_name": "Espa\u00f1ol, Castellano", "on_disk": true, "stream_type": "video/mp4", "thumbnail": "/content/yHeTx8SAaOQ.png", "stream": "/content/yHeTx8SAaOQ.mp4"}}, "selected_language": "en", "kind": "Video", "title": "Basic addition", "on_disk": true, "video_id": "AuX7nPBqDts", "slug": "basic-addition", "parent_id": "basic_addition", "id": "AuX7nPBqDts", "youtube_id": "AuX7nPBqDts", "subtitle_urls": [{"url": "/static/srt/ar/subtitles/AuX7nPBqDts.srt", "code": "ar", "name": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"}, {"url": "/static/srt/es/subtitles/AuX7nPBqDts.srt", "code": "es", "name": "Espa\u00f1ol, Castellano"}], "readable_id": "basic-addition"}
                    )
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

        this.sidebar = this.$('.playlist-sidebar-tab').bigSlide({
            menu: this.$(".panel"),
            // push: "#page-container, #footer, .playlist-sidebar-tab",
            push: ".playlist-sidebar-tab",
            menuWidth: "220px"
        });

        this.show_sidebar();

    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    show_sidebar: function() {
        this.sidebar.open();
    },

    hide_sidebar: function() {
        this.sidebar.close();
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

    tagName: "li",

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

