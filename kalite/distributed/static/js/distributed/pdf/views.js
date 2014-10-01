window.PDFViewerView = Backbone.View.extend({

    template: HB.template("pdf/pdf-viewer"),

    initialize: function() {

        _.bindAll(this);

        var self = this;

        // NOTE (aron): You know, this piece
        // of code is shared between this view
        // and AudioPlayerView. I'm thinking of
        // putting this into a mixin, based
        // on rico's blog post:
        // http://ricostacruz.com/backbone-patterns/#mixins
        window.statusModel.loaded.then(function() {
            // load the info about the content itself
            self.data_model = new ContentDataModel({id: self.options.id});
            if (self.data_model.get("id")) {
                self.data_model.fetch().then(function() {

                    if (window.statusModel.get("is_logged_in")) {

                        self.log_collection = new ContentLogCollection([], {content_model: self.data_model});
                        self.log_collection.fetch().then(self.user_data_loaded);

                    }
                });
            }

        });

        this.render();
    },

    render: function() {
        this.$el.html(this.template({pdf: "04TLVP4.pdf"}));
        this.$(".pdf-iframe").load(this.initialize_listeners);
    },

    initialize_listeners: function(ev) {
        var contentWindow = ev.target.contentWindow; // the window object inside the iframe

        // NOTE (aron): I used addEventListener here since contentWindow
        // is a plain JS object and not a JQuery object, which listenTo
        // needs to function. I can't seem to coerce it cleanly into
        // a JQuery object.

        // TODO (aron): don't forget to clean these listeners up.
        contentWindow.addEventListener("pageshow", this.page_loaded); // document loaded for the first time
        contentWindow.addEventListener("pagechange", this.page_changed); // page changed
    },

    page_changed: function(ev) {
        var viewerWindow = ev.target;
        if (viewerWindow.PDFView.previousPageNumber !== viewerWindow.currentPageNumber) { // the page actually changed
            console.log("page actually changed!");
            this.update_progress(viewerWindow.PDFView);
        }
    },

    page_loaded: function(ev) {
        console.log("Page successfully loaded!")

        var pdfview = ev.target.PDFView;
        this.update_progress(pdfview);
    },

    update_progress: function(pdfview) {
        console.log("I'm updating the progress!");

        // check if our current page is is higher than the user's highest
        // page viewed. If so, do an update.
    },

    user_data_loaded: function() {
        this.log_model = this.log_collection.get_first_log_or_new_log();
    },

});
