var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");
var _ = require("underscore");
var $ = require("base/jQuery");

var Modernizr = require("browsernizr");

var SoftwareKeyboardView = BaseView.extend({

    template: require("./hbtemplates/software-keyboard.handlebars"),

    events: {
       "click button.key" : "key_pressed",
       "click button#show-keyboard": "toggle_keypad",
       "keypress button": "catch_keypress"
     },


    keys: [
        [ {display: "1", value: "1"}, {display: "2", value: "2"}, {display: "3", value: "3"} ],
        [ {display: "4", value: "4"}, {display: "5", value: "5"}, {display: "6", value: "6"} ],
        [ {display: "7", value: "7"}, {display: "8", value: "8"}, {display: "9", value: "9"} ],
        [ {display: "(", value: "("}, {display: "0", value: "0"}, {display: ")", value: ")"} ],
        [ {display: "/", value: "/"}, {display: ".", value: "."}, {display: "-", value: "-"} ],
        [ {display: "c", value: "c"}, {display: "␣", value: " "}, {display: "Del", value: "Del"} ]
    ],

    initialize: function () {

        _.bindAll(this, "set_input", "toggle_keypad", "key_pressed", "render", "hide", "show", "catch_keypress");

        this.touch = Modernizr.touch;
        this.enabled = true;
        this.render();

    },

    set_input: function(el) {
        this.inputs = $(el)
            .prop("readonly", this.enabled)
            .css("-webkit-tap-highlight-color", "rgba(0, 0, 0, 0)");
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

        var input = this.inputs.first();
        var inputIndex = 0;

        $(this.inputs).each(function (index) {
            if ( $(this).attr("id") == "selected-input" ) {
                input = $(this);
                inputIndex = index;
            }
        });

        this.field = input;

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

        //The only way it seems we can set the value for a Perseus exercise is by using the
        //setInputValue method of the itemRenderer. Directly interacting with the DOM element
        //doesn't seem to trigger the right events for the React Element to notice.

        if (typeof Exercises.PerseusBridge.itemRenderer !== "undefined") {
            var inputPaths = Exercises.PerseusBridge.itemRenderer.getInputPaths() || [];
            if (inputPaths.length > 0) {
                Exercises.PerseusBridge.itemRenderer.setInputValue(inputPaths[inputIndex], this.field.val());
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

module.exports = SoftwareKeyboardView;