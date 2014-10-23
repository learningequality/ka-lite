window.PDFViewerView = ContentBaseView.extend({

    template: HB.template("pdf/pdf-viewer"),

    render: function() {
        if (!this.log_model.get("highest_page")) {
            this.log_model.set("highest_page", 0);
        }
        this.$el.html(this.template(this.data_model.attributes));
        this.$(".pdf-iframe").load(this.initialize_listeners);
    },

    initialize_listeners: function(ev) {
        var contentWindow = ev.target.contentWindow; // the window object inside the iframe

        this.listenToDOM(contentWindow, "pageshow", this.page_loaded);
        this.listenToDOM(contentWindow, "pagechange", this.page_changed); // page changed
    },

    page_changed: function(ev) {
        var contextWindow = ev.target;
        this.update_progress(contextWindow.PDFView);
    },

    page_loaded: function(ev) {
        var contextWindow = ev.target.defaultView;
        var pdfview = contextWindow.PDFView;
        this.activate();
        this.update_progress(pdfview);
    },

    content_specific_progress: function(pdfview) {

        // check if our current page is is higher than the user's highest
        // page viewed. If so, do an update.
        var numpages = pdfview.pages.length;
        var current_page = pdfview.page;
        var highest_page = this.log_model.get("highest_page");

        if (current_page > highest_page) {
            this.log_model.set("highest_page", current_page);
            highest_page = current_page;
        }

        var progress = highest_page/numpages;

        return progress;
    }

});
