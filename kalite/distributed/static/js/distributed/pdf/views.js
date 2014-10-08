window.PDFViewerView = Backbone.View.extend({

    template: HB.template("pdf/pdf-viewer"),

    initialize: function() {

        this.POINTS_PER_PAGE = 50;

        ContentBaseView.prototype.initialize.apply(this, arguments);

    },

    render: function() {
        this.$el.html(this.template({pdf: "04TLVP4.pdf"}));
        window.statusModel.set("points", this.log_model.get("points"));
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
        var contextWindow = ev.target;
        if (contextWindow.PDFView.previousPageNumber !== contextWindow.currentPageNumber) { // the page actually changed
            console.log("page actually changed!");
            this.update_progress(contextWindow.PDFView);
        }
    },

    page_loaded: function(ev) {
        console.log("Page successfully loaded!")

        var contextWindow = ev.target.defaultView;
        var pdfview = contextWindow.PDFView;
        this.update_progress(pdfview);
    },

    update_progress: function(pdfview) {
        if (!window.statusModel.get("is_logged_in") ) {
            console.log("Not logged in; skipping update!")
            return;
        }

        if (window.statusModel.get("is_django_user")) {
            console.log("Not a student; skipping update!")
            return;
        }

        if (this.log_model.get("complete")) {
            console.log("PDF already completed; skipping update!");
            return;
        }

        // check if our current page is is higher than the user's highest
        // page viewed. If so, do an update.
        var numpages = pdfview.pages.length;
        var current_page = pdfview.page;
        var highest_page = this.log_model.get("highest_page");

        if (current_page > highest_page) {
            console.log("Moved to a new page; updating progress!");
            this.log_model.set("highest_page", current_page);
            highest_page = current_page;

            // increment the user's points
            var current_points = this.log_model.get("points");
            this.log_model.set("points", current_points + this.POINTS_PER_PAGE);
        }

        // also check if we are in the last page.
        if (highest_page === numpages) {
            console.log("Seen all pages; setting to complete!");
            this.log_model.set_complete();
        }

        // for realtime updating of points
        window.statusModel.set("points", this.log_model.get("points"));

        this.log_model.save();
    },

    user_data_loaded: function() {
        this.log_model = this.log_collection.get_first_log_or_new_log();

        // set some default attributes specific to pdf content tracking
        if (!this.log_model.get("highest_page")) {
            this.log_model.set("highest_page", 0);
        }
        
        this.render();
    },

});
