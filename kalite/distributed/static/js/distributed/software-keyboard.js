window.SoftwareKeyboardView = Backbone.View.extend({

    events: {
       "click button.key" : "keyPressed"
     },

    initialize: function () {

        _.bindAll(this);

       this.inputs = this.$el.find( ":input" )
           .prop( "readonly", true )
           .css( "-webkit-tap-highlight-color", "rgba(0, 0, 0, 0)" );
       this.field = this.inputs.first();
       this.render();

    },

    keyPressed: function( ev ) {
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

        this.$el.append("<div class='container-fluid' id='software-keyboard'></div>");
        var keys = [ [ "1", "2", "3" ], [ "4", "5", "6" ], [ "7", "8", "9" ], ["/", "0", "-" ],[ ".", "c", "bs" ] ];
        var corners = {
            "1": "ui-corner-tl",
            "3": "ui-corner-tr",
            ".": "ui-corner-bl",
            "bs": "ui-corner-br"
        };

        var softwareKeyboard = this.$el.find("#software-keyboard");

        jQuery.each( keys, function( i, row ) {
            var rowDiv = jQuery( "<div>" )
                .attr( "class", "row" )
                .appendTo( softwareKeyboard );

            jQuery.each( row, function( j, key ) {
                var keySpan = $("<div class='.col-xs-4'><button class='key btn btn-success " + (key === "bs" ? "key-bs" : "") + "' value='" + key + "'>" + (key === "bs" ? "Del" : key) + "</button></div>").appendTo( rowDiv );

            } );
        } );

    }

})