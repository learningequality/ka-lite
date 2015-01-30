window.SoftwareKeyboardView = Backbone.View.extend({

    events: {
       "click button.key" : "key_pressed",
       "click button#show-keyboard": "toggle_keypad"
     },

    initialize: function () {

        _.bindAll(this);

        this.touch = Modernizr.touch;
        this.enabled = true;
        this.render();

    },

    set_input: function(el) {
        this.inputs = $(el)
            .prop("readonly", this.enabled)
            .css("-webkit-tap-highlight-color", "rgba(0, 0, 0, 0)");
        this.field = this.inputs.first();
    },

    toggle_keypad: function() {
        var self = this;
        this.enabled = !this.enabled;
        this.software_keyboard.toggle();
        if (typeof this.inputs !== "undefined") {
            this.inputs.prop("readonly", function(index, value){
                return self.enabled;
            });
        }
        this.$("#show-keyboard").text(function(i, text){
            return text === gettext("Show Keypad") ? gettext("Hide Keypad") : gettext("Show Keypad");
        });
        return false;
    },

    key_pressed: function(ev) {
        if(!this.enabled) {
            return false;
        }
        var field = this.field[0];
        var key = $(ev.target).val();
        // backspace key
        if (key == "bs") {
            if (_.isFunction(field.setRangeText)) {
                // delete the currently selected text or the last character
                if (field.selectionStart === field.selectionEnd) {
                    field.selectionStart = field.value.length - 1;
                    field.selectionEnd = field.value.length;
                }
                field.setRangeText("");
            } else {
                this.field.val(this.field.val().slice(0, -1));
            }
        //clear key
        } else if (key == "c") {
            this.field.val('');
        } else {
            //normal key
            if (_.isFunction(field.setRangeText)) {
                // overwrite the current selection with the new key (which will just insert if nothing is selected)
                field.setRangeText(key);
                field.selectionStart = field.selectionEnd = field.value.length;
            } else {
                this.field.val(this.field.val() + key);
            }
        }

        this.field.trigger("keypress");

        // The only way it seems we can set the value for a Perseus exercise is by using the
        // setInputValue method of the itemRenderer. Directly interacting with the DOM element
        // doesn't seem to trigger the right events for the React Element to notice.
        var inputPaths = Exercises.PerseusBridge.itemRenderer.getInputPaths() || [];
        if (inputPaths.length > 0) {
            Exercises.PerseusBridge.itemRenderer.setInputValue(inputPaths[0], this.field.val());
        }

        return false;
    },

    render: function () {
        var self = this;

        // TODO-BLOCKER (rtibbles): 0.13 - Turn this into a handlebars template, conditionally render templates based on exercise types.

        this.$el.append("<button class='simple-button orange' id='show-keyboard'>" + gettext("Hide Keypad") + "</button>");

        this.$el.append("<div class='container-fluid' id='software-keyboard'></div>");

        // TODO-BLOCKER (rtibbles): 0.13 - Remove extraneous &nbsp; added here to make styling work without Bootstrap

        var keys = [ [ "1", "2", "3" ], [ "4", "5", "6" ], [ "7", "8", "9" ], ["/&nbsp;", "0", "&nbsp;-" ],[ ".", "c", "bs" ] ];
        var corners = {
            "1": "ui-corner-tl",
            "3": "ui-corner-tr",
            ".": "ui-corner-bl",
            "bs": "ui-corner-br"
        };

        this.software_keyboard = this.$("#software-keyboard");

        jQuery.each(keys, function(i, row) {
            var rowDiv = jQuery("<div>")
                .attr("class", "row")
                .appendTo(self.software_keyboard);

            jQuery.each(row, function(j, key) {
                var keySpan = $("<div class='.col-xs-4'><button class='key simple-button' value='" + key + "'>" + (key === "bs" ? "Del" : key) + "</button></div>").appendTo(rowDiv);
            });
        });

        if(!this.touch){
            this.toggle_keypad();
        }

    },

    hide: function() {
        this.$el.hide();
    },

    show: function() {
        this.$el.show();
    }

});