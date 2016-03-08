var BaseView = require("../base/baseview");
var Handlebars = require("../base/handlebars");
var _ = require("underscore");
var api = require("../utils/api");
var messages = require("utils/messages");
var sprintf = require("sprintf-js").sprintf;

require("../../../css/distributed/search_autocomplete.less");

var SearchBarTemplate = require("./hbtemplates/search-bar.handlebars");
var SearchBarItemTemplate = require("./hbtemplates/search-item.handlebars");
var AutoCompleteView = BaseView.extend({

    template: SearchBarTemplate,

    item_template: SearchBarItemTemplate,

    tagName: "li",

    attributes: { // required for a11y conformance tests
        role: "menuitem",
        id: "search_box_cont"
    },

    events: {
        "input #search": "input_changed",
        "focus #search": "fetch_topic_tree",
        "click #search-button": "submit_form"
    },

    initialize: function() {

        _.bindAll(this, "render",  "select_item", "input_changed", "submit_form", "render_item");

        this._titles = {};
        this._keywords = {};

        this.render();

    },

    search_items: ["tags", "keywords"],


    render: function() {

        this.$el.html(this.template({search_url: window.Urls.search()}));

        this.$("#search").autocomplete({
            autoFocus: false,
            minLength: 3,
            appendTo: ".navbar-collapse",
            html: true,  // extension allows html-based labels
            source: window.Urls.search_api(window.sessionModel.get("CHANNEL")),
            select: this.select_item
        }).data("ui-autocomplete")._renderItem = this.render_item;

        this.input_changed();

    },

    render_item: function(ul, item) {
        return $(this.item_template(item)).appendTo(ul);
    },

    select_item: function( event, ui ) {
        // When they click a specific item, just go there (if we recognize it)
        if (ui.item.path) {
            if ("channel_router" in window) {
                window.channel_router.navigate(ui.item.path, {trigger: true});
            } else {
                window.location.href = window.Urls.learn() + ui.item.path;
            }
        } else {
            messages.show_message("error", gettext("Unexpected error: no search data found for selected item. Please select another item."));
        }
        this.$("#search-box input").val("");
        return false;
    },

    input_changed: function() {
        if (this.$("#search").val() !== "") {
           this.$("#search-button").removeAttr("disabled");
        }else {
           this.$("#search-button").attr('disabled', 'disabled');
        }
    },

    submit_form: function() {
        this.$("#search-box").submit();
    }
});

module.exports = AutoCompleteView;