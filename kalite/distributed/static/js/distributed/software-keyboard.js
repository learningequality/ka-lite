window.SoftwareKeyboardView = Backbone.View.extend({

    events: {
       "click button.key" : "key_pressed",
       "click button#show-keyboard": "toggle_keypad"
     },

    initialize: function () {

        _.bindAll(this);

       this.inputs = this.$el.find( ":input" )
           .prop( "readonly", true )
           .css( "-webkit-tap-highlight-color", "rgba(0, 0, 0, 0)" );
       this.field = this.inputs.first();
       this.touch = Modernizr.touch;
       this.enabled = true;
       this.render();

    },

    toggle_keypad: function() {
        this.enabled = !this.enabled;
        this.software_keyboard.toggle();
        this.inputs.prop("readonly", function(index, value){
            return !value;
        });
        this.$el.find("#show-keyboard").text(function(i, text){
            // TODO
            return text === gettext("Show Keypad") ? gettext("Hide Keypad") : gettext("Show Keypad");
        });
        return false;
    },

    key_pressed: function( ev ) {
        if(!this.enabled) {
            return false;
        }
        var key = $(ev.target).val();
        // backspace key
        if ( key == "bs" ) {
            this.field.val( this.field.val().slice( 0, -1 ) );
        //clear key
        } else if(key == "c"){
            this.field.val('');
        } else {
            //normal key
            this.field.val( this.field.val() + key );
        }

        this.field.trigger("keypress");

        return false;
    },

    render: function () {
        self = this;

        // TODO-BLOCKER (rtibbles): 0.13 - Turn this into a handlebars template, conditionally render templates based on exercise types.

        this.$el.append("<button id='show-keyboard'>" + gettext("Hide Keypad") + "</button>");

        this.$el.append("<div class='container-fluid' id='software-keyboard'></div>");

        // TODO-BLOCKER (rtibbles): 0.13 - Remove extraneous &nbsp; added here to make styling work without Bootstrap

        var keys = [ [ "1", "2", "3" ], [ "4", "5", "6" ], [ "7", "8", "9" ], ["/&nbsp;", "0", "&nbsp;-" ],[ ".", "c", "bs" ] ];
        var corners = {
            "1": "ui-corner-tl",
            "3": "ui-corner-tr",
            ".": "ui-corner-bl",
            "bs": "ui-corner-br"
        };

        this.software_keyboard = this.$el.find("#software-keyboard");

        jQuery.each( keys, function( i, row ) {
            var rowDiv = jQuery( "<div>" )
                .attr( "class", "row" )
                .appendTo( self.software_keyboard );

            jQuery.each( row, function( j, key ) {
                var keySpan = $("<div class='.col-xs-4'><button class='key green_button " + (key === "bs" ? "key-bs" : "") + "' value='" + key + "'>" + (key === "bs" ? "Del" : key) + "</button></div>").appendTo( rowDiv );

            } );
        } );

        if(!this.touch){
            this.toggle_keypad();
        }

    }

});