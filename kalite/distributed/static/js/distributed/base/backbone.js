// This file provides a thin wrapper around Backbone to customize it for our purposes.

var Backbone = require("backbone");
var _ = require("underscore");
require("./backbone-tastypie.js");

var api = require("../utils/api");

Backbone.$ = require("./jQuery");

// Customize the Backbone.js ajax method to call our success and fail handlers for error display
Backbone.ajax = function() {
    return Backbone.$.ajax.apply(Backbone.$, arguments)
        .success(function(resp) {
            api.handleSuccessAPI(resp);
        })
        .fail(function(resp) {
            api.handleFailedAPI(resp);
        });
};

var $ = Backbone.$;

require("jquery-ui/autocomplete");
require("jquery-plainoverlay/jquery.plainoverlay");

/*
 * jQuery UI Autocomplete HTML Extension
 *
 * Copyright 2010, Scott González (http://scottgonzalez.com)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 *
 * http://github.com/scottgonzalez/jquery-ui-extensions
 */
(function( $ ) {

var proto = $.ui.autocomplete.prototype,
	initSource = proto._initSource;

function filter( array, term ) {
	var matcher = new RegExp( $.ui.autocomplete.escapeRegex(term), "i" );
	return $.grep( array, function(value) {
		return matcher.test( $( "<div>" ).html( value.label || value.value || value ).text() );
	});
}

$.extend( proto, {
	_initSource: function() {
		if ( this.options.html && $.isArray(this.options.source) ) {
			this.source = function( request, response ) {
				response( filter( this.options.source, request.term ) );
			};
		} else {
			initSource.call( this );
		}
	},

	_renderItem: function( ul, item) {
		return $( "<li></li>" )
			.data( "item.autocomplete", item )
			.append( $( "<a></a>" )[ this.options.html ? "html" : "text" ]( item.label ) )
			.appendTo( ul );
	}
});

})( $ );

require('jquery-ui-touch-punch');

module.exports = Backbone;