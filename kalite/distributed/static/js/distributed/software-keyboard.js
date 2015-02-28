window.SoftwareKeyboardView = Backbone.View.extend({

    template: HB.template("exercise/software-keyboard"),

    events: {
       "click button.key" : "key_pressed",
       "click button#show-keyboard": "toggle_keypad",
       "keypress button": "catch_keypress"
     },


    keys: [
        [ "1", "2", "3" ],
        [ "4", "5", "6" ],
        [ "7", "8", "9" ],
        [ "/", "0", "-" ],
        [ ".", "c", "Del" ]
    ],

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
        if (key == "Del") {
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

        if (typeof Exercises.PerseusBridge.itemRenderer !== "undefined") {
            var inputPaths = Exercises.PerseusBridge.itemRenderer.getInputPaths() || [];
            if (inputPaths.length > 0) {
                Exercises.PerseusBridge.itemRenderer.setInputValue(inputPaths[0], this.field.val());
            }
        }

        return false;
    },

    render: function () {
        var self = this;

        this.$el.html(this.template({keys: this.keys}));

        this.software_keyboard = this.$("#software-keyboard");

        if(!this.touch){
            this.toggle_keypad();
        }

    },

    hide: function() {
        this.$el.hide();
    },

    show: function() {
        this.$el.show();
    },

    catch_keypress: function(event) {
        event.preventDefault();
        if (event.which == 13 || event.keyCode == 13) {
            this.trigger("enter_pressed");
        }
        return false;
    }

});