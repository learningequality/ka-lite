(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
require('../third_party/jquery.mobile.vmouse.js');
window.DrawingScratchpad = function (elem) {
    var pen = 'M25.31,2.872l-3.384-2.127c-0.854-0.536-1.979-0.278-2.517,0.576l-1.334,2.123l6.474,4.066l1.335-2.122C26.42,4.533,26.164,3.407,25.31,2.872zM6.555,21.786l6.474,4.066L23.581,9.054l-6.477-4.067L6.555,21.786zM5.566,26.952l-0.143,3.819l3.379-1.787l3.14-1.658l-6.246-3.925L5.566,26.952z';
    var erase = 'M24.778,21.419 19.276,15.917 24.777,10.415 21.949,7.585 16.447,13.087 10.945,7.585 8.117,10.415 13.618,15.917 8.116,21.419 10.946,24.248 16.447,18.746 21.948,24.248';
    var undo = 'M12.981,9.073V6.817l-12.106,6.99l12.106,6.99v-2.422c3.285-0.002,9.052,0.28,9.052,2.269c0,2.78-6.023,4.263-6.023,4.263v2.132c0,0,13.53,0.463,13.53-9.823C29.54,9.134,17.952,8.831,12.981,9.073z';
    var rainbow = '0-#00ff00-#ff0000:50-#0000ff';
    var nextRainbowStroke = function () {
        var freq = 0.05;
        var iter = 0;
        return function () {
            var red = Math.sin(freq * iter + -3) * 127 + 128;
            var green = Math.sin(freq * iter + -1) * 127 + 128;
            var blue = Math.sin(freq * iter + 1) * 127 + 128;
            iter++;
            return 'rgb(' + red + ',' + green + ',' + blue + ')';
        };
    }();
    if (!elem) {
        throw new Error('No element provided to DrawingScratchpad');
    }
    var container = $(elem);
    var pad = Raphael(container[0], container.width(), container.height());
    this.resize = function () {
        pad.setSize(container.width(), container.height());
    };
    var palette = pad.set(), stroke = rainbow, colors = [
            rainbow,
            '#000000',
            '#3f3f3f',
            '#7f7f7f',
            '#bfbfbf',
            '#ff0000',
            '#ff7f00',
            '#ffff00',
            '#00ff00',
            '#00ffff',
            '#007fff',
            '#0000ff',
            '#7f00ff'
        ];
    for (var i = 0; i < colors.length; i++) {
        (function (color) {
            var setcolor = function (e) {
                stroke = color;
                palette.animate({ y: 7 }, 100);
                this.animate({ y: 15 }, 100);
                penclick();
            };
            palette.push(pad.rect(90 + i * 27, 7, 24, 24).attr({
                fill: color,
                stroke: '#ccc'
            }).touchstart(setcolor).click(setcolor));
        }(colors[i]));
    }
    palette[0].attr({ y: 15 });
    var selected = pad.rect(2, 2, 30, 30).attr({
        r: 5,
        stroke: '',
        fill: 'rgba(30, 157, 186, 0.5)'
    });
    var line_default = {
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round'
    };
    var shapes = pad.set();
    var undoHistory = [[]];
    function saveState() {
        for (var i = 0, state = []; i < shapes.length; i++) {
            if (!shapes[i].removed) {
                if (shapes[i].type === 'path') {
                    state.push({
                        path: shapes[i].attr('path').toString(),
                        stroke: shapes[i].attr('stroke'),
                        type: 'path'
                    });
                }
            }
        }
        undoHistory.push(state);
    }
    function loadState(state) {
        shapes.remove();
        for (var i = 0; i < state.length; i++) {
            if (state[i].type === 'path') {
                shapes.push(pad.path(state[i].path).attr(line_default).attr({
                    stroke: state[i].stroke,
                    'clip-rect': [
                        0,
                        40,
                        pad.width,
                        pad.height - 40
                    ]
                }));
            }
        }
    }
    var tools = pad.set();
    tools.push(pad.path(pen).scale(0.8).translate(0, 0));
    tools.push(pad.path(erase).translate(30, 0));
    tools.push(pad.path(undo).scale(0.7).translate(60, 1));
    var tool = 'draw';
    function penclick() {
        selected.animate({ x: 2 }, 100);
        tool = 'draw';
    }
    pad.rect(2, 2, 30, 30).attr({
        stroke: '',
        fill: 'black',
        'fill-opacity': 0
    }).click(penclick).touchstart(penclick);
    function eraseclick() {
        selected.animate({ x: 2 + 30 }, 100);
        tool = 'erase';
    }
    pad.rect(2 + 30, 2, 30, 30).attr({
        stroke: '',
        fill: 'black',
        'fill-opacity': 0
    }).click(eraseclick).touchstart(eraseclick);
    function undoclick() {
        if (undoHistory.length) {
            loadState(undoHistory.pop());
        }
    }
    pad.rect(2 + 30 * 2, 2, 30, 30).attr({
        stroke: '',
        fill: 'black',
        'fill-opacity': 0
    }).click(undoclick).touchstart(undoclick);
    tools.attr({
        fill: '#000',
        stroke: 'none'
    });
    var path = null, pathstr = '', prevPen;
    var eraser = null;
    function mousedown(X, Y, e) {
        if (!X || !Y || !e) {
            return;
        }
        if (Y <= 40) {
            return;
        }
        if (eraser) {
            eraser.remove();
            eraser = null;
        }
        if (tool === 'draw') {
            saveState();
            startPen(X, Y);
        } else if (tool === 'erase') {
            eraser = pad.rect(X, Y, 0, 0).attr({
                'fill-opacity': 0.15,
                'stroke-opacity': 0.5,
                'fill': '#ff0000',
                'stroke': '#ff0000'
            });
            eraser.sx = X;
            eraser.sy = Y;
        }
    }
    function startPen(x, y) {
        var singleColorStroke = stroke === rainbow ? nextRainbowStroke() : stroke;
        path = pad.path('M' + x + ',' + y).attr(line_default).attr({
            stroke: singleColorStroke,
            'clip-rect': [
                0,
                40,
                pad.width,
                pad.height - 40
            ]
        });
        pathstr = path.attr('path');
        shapes.push(path);
        prevPen = {
            x: x,
            y: y
        };
    }
    function rectsIntersect(r1, r2) {
        return r2.x < r1.x + r1.width && r2.x + r2.width > r1.x && r2.y < r1.y + r1.height && r2.y + r2.height > r1.y;
    }
    function mouseup(x, y) {
        if (tool === 'draw' && path) {
            pathstr += 'L' + x + ',' + y;
            prevPen = null;
            path.attr('path', pathstr);
        }
        path = null;
        if (tool === 'erase' && eraser) {
            saveState();
            var actuallyErased = false;
            var ebox = eraser.getBBox();
            for (var i = 0; i < shapes.length; i++) {
                if (rectsIntersect(ebox, shapes[i].getBBox())) {
                    actuallyErased = true;
                    shapes[i].remove();
                }
            }
            if (!actuallyErased) {
                undoHistory.pop();
            }
            var e = eraser;
            eraser = null;
            e.animate({ opacity: 0 }, 100, function () {
                e.remove();
            });
        }
    }
    function mousemove(X, Y) {
        if (tool === 'draw' && path) {
            pathstr += 'Q' + prevPen.x + ',' + prevPen.y + ',' + (prevPen.x + X) / 2 + ',' + (prevPen.y + Y) / 2;
            prevPen = {
                x: X,
                y: Y
            };
            path.attr('path', pathstr);
        } else if (tool === 'erase' && eraser) {
            var x1 = Math.min(X, eraser.sx), x2 = Math.max(X, eraser.sx), y1 = Math.max(40, Math.min(Y, eraser.sy)), y2 = Math.max(40, Math.max(Y, eraser.sy));
            eraser.attr({
                x: x1,
                y: y1,
                width: x2 - x1,
                height: y2 - y1
            });
        }
    }
    var handleMousemove = function (e) {
        var offset = $(container).offset();
        mousemove(e.pageX - offset.left, e.pageY - offset.top);
        e.preventDefault();
    };
    $(container).on('vmousedown', function (e) {
        var offset = $(container).offset();
        mousedown(e.pageX - offset.left, e.pageY - offset.top, e);
        e.preventDefault();
        $(document).on('vmousemove', handleMousemove);
        $(document).one('vmouseup', function (e) {
            mouseup(e.pageX - offset.left, e.pageY - offset.top, e);
            e.preventDefault();
            $(document).off('vmousemove', handleMousemove);
        });
    });
    this.clear = function () {
        shapes.remove();
        undoHistory = [[]];
    };
};
},{"../third_party/jquery.mobile.vmouse.js":2}],2:[function(require,module,exports){
/*
* jQuery Mobile Framework : "mouse" plugin
* Copyright (c) jQuery Project
* Dual licensed under the MIT or GPL Version 2 licenses.
* http://jquery.org/license
*/

// This plugin is an experiment for abstracting away the touch and mouse
// events so that developers don't have to worry about which method of input
// the device their document is loaded on supports.
//
// The idea here is to allow the developer to register listeners for the
// basic mouse events, such as mousedown, mousemove, mouseup, and click,
// and the plugin will take care of registering the correct listeners
// behind the scenes to invoke the listener at the fastest possible time
// for that device, while still retaining the order of event firing in
// the traditional mouse environment, should multiple handlers be registered
// on the same element for different events.
//
// The current version exposes the following virtual events to jQuery bind methods:
// "vmouseover vmousedown vmousemove vmouseup vclick vmouseout vmousecancel"

(function( $, window, document, undefined ) {

var dataPropertyName = "virtualMouseBindings",
	touchTargetPropertyName = "virtualTouchID",
	virtualEventNames = "vmouseover vmousedown vmousemove vmouseup vclick vmouseout vmousecancel".split( " " ),
	touchEventProps = "clientX clientY pageX pageY screenX screenY".split( " " ),
	mouseHookProps = $.event.mouseHooks ? $.event.mouseHooks.props : [],
	mouseEventProps = $.event.props.concat( mouseHookProps ),
	activeDocHandlers = {},
	resetTimerID = 0,
	startX = 0,
	startY = 0,
	didScroll = false,
	clickBlockList = [],
	blockMouseTriggers = false,
	blockTouchTriggers = false,
	eventCaptureSupported = "addEventListener" in document,
	$document = $( document ),
	nextTouchID = 1,
	lastTouchID = 0;

$.vmouse = {
	moveDistanceThreshold: 10,
	clickDistanceThreshold: 10,
	resetTimerDuration: 1500
};

function getNativeEvent( event ) {

	while ( event && typeof event.originalEvent !== "undefined" ) {
		event = event.originalEvent;
	}
	return event;
}

function createVirtualEvent( event, eventType ) {

	var t = event.type,
		oe, props, ne, prop, ct, touch, i, j;

	event = $.Event(event);
	event.type = eventType;

	oe = event.originalEvent;
	props = $.event.props;

	// addresses separation of $.event.props in to $.event.mouseHook.props and Issue 3280
	// https://github.com/jquery/jquery-mobile/issues/3280
	if ( t.search(/mouse/) >-1 ) {
		props = mouseEventProps;
	}

	// copy original event properties over to the new event
	// this would happen if we could call $.event.fix instead of $.Event
	// but we don't have a way to force an event to be fixed multiple times
	if ( oe ) {
		for ( i = props.length, prop; i; ) {
			prop = props[ --i ];
			event[ prop ] = oe[ prop ];
		}
	}

	// make sure that if the mouse and click virtual events are generated
	// without a .which one is defined
	if ( t.search(/mouse(down|up)|click/) > -1 && !event.which ){
		event.which = 1;
	}

	if ( t.search(/^touch/) !== -1 ) {
		ne = getNativeEvent( oe );
		t = ne.touches;
		ct = ne.changedTouches;
		touch = ( t && t.length ) ? t[0] : ( (ct && ct.length) ? ct[ 0 ] : undefined );

		if ( touch ) {
			for ( j = 0, len = touchEventProps.length; j < len; j++){
				prop = touchEventProps[ j ];
				event[ prop ] = touch[ prop ];
			}
		}
	}

	return event;
}

function getVirtualBindingFlags( element ) {

	var flags = {},
		b, k;

	while ( element ) {

		b = $.data( element, dataPropertyName );

		for (  k in b ) {
			if ( b[ k ] ) {
				flags[ k ] = flags.hasVirtualBinding = true;
			}
		}
		element = element.parentNode;
	}
	return flags;
}

function getClosestElementWithVirtualBinding( element, eventType ) {
	var b;
	while ( element ) {

		b = $.data( element, dataPropertyName );

		if ( b && ( !eventType || b[ eventType ] ) ) {
			return element;
		}
		element = element.parentNode;
	}
	return null;
}

function enableTouchBindings() {
	blockTouchTriggers = false;
}

function disableTouchBindings() {
	blockTouchTriggers = true;
}

function enableMouseBindings() {
	lastTouchID = 0;
	clickBlockList.length = 0;
	blockMouseTriggers = false;

	// When mouse bindings are enabled, our
	// touch bindings are disabled.
	disableTouchBindings();
}

function disableMouseBindings() {
	// When mouse bindings are disabled, our
	// touch bindings are enabled.
	enableTouchBindings();
}

function startResetTimer() {
	clearResetTimer();
	resetTimerID = setTimeout(function(){
		resetTimerID = 0;
		enableMouseBindings();
	}, $.vmouse.resetTimerDuration );
}

function clearResetTimer() {
	if ( resetTimerID ){
		clearTimeout( resetTimerID );
		resetTimerID = 0;
	}
}

function triggerVirtualEvent( eventType, event, flags ) {
	var ve;

	if ( ( flags && flags[ eventType ] ) ||
				( !flags && getClosestElementWithVirtualBinding( event.target, eventType ) ) ) {

		ve = createVirtualEvent( event, eventType );

		$( event.target).trigger( ve );
	}

	return ve;
}

function mouseEventCallback( event ) {
	var touchID = $.data(event.target, touchTargetPropertyName);

	if ( !blockMouseTriggers && ( !lastTouchID || lastTouchID !== touchID ) ){
		var ve = triggerVirtualEvent( "v" + event.type, event );
		if ( ve ) {
			if ( ve.isDefaultPrevented() ) {
				event.preventDefault();
			}
			if ( ve.isPropagationStopped() ) {
				event.stopPropagation();
			}
			if ( ve.isImmediatePropagationStopped() ) {
				event.stopImmediatePropagation();
			}
		}
	}
}

function handleTouchStart( event ) {

	var touches = getNativeEvent( event ).touches,
		target, flags;

	if ( touches && touches.length === 1 ) {

		target = event.target;
		flags = getVirtualBindingFlags( target );

		if ( flags.hasVirtualBinding ) {

			lastTouchID = nextTouchID++;
			$.data( target, touchTargetPropertyName, lastTouchID );

			clearResetTimer();

			disableMouseBindings();
			didScroll = false;

			var t = getNativeEvent( event ).touches[ 0 ];
			startX = t.pageX;
			startY = t.pageY;

			triggerVirtualEvent( "vmouseover", event, flags );
			triggerVirtualEvent( "vmousedown", event, flags );
		}
	}
}

function handleScroll( event ) {
	if ( blockTouchTriggers ) {
		return;
	}

	if ( !didScroll ) {
		triggerVirtualEvent( "vmousecancel", event, getVirtualBindingFlags( event.target ) );
	}

	didScroll = true;
	startResetTimer();
}

function handleTouchMove( event ) {
	if ( blockTouchTriggers ) {
		return;
	}

	var t = getNativeEvent( event ).touches[ 0 ],
		didCancel = didScroll,
		moveThreshold = $.vmouse.moveDistanceThreshold;
		didScroll = didScroll ||
			( Math.abs(t.pageX - startX) > moveThreshold ||
				Math.abs(t.pageY - startY) > moveThreshold ),
		flags = getVirtualBindingFlags( event.target );

	if ( didScroll && !didCancel ) {
		triggerVirtualEvent( "vmousecancel", event, flags );
	}

	triggerVirtualEvent( "vmousemove", event, flags );
	startResetTimer();
}

function handleTouchEnd( event ) {
	if ( blockTouchTriggers ) {
		return;
	}

	disableTouchBindings();

	var flags = getVirtualBindingFlags( event.target ),
		t;
	triggerVirtualEvent( "vmouseup", event, flags );

	if ( !didScroll ) {
		var ve = triggerVirtualEvent( "vclick", event, flags );
		if ( ve && ve.isDefaultPrevented() ) {
			// The target of the mouse events that follow the touchend
			// event don't necessarily match the target used during the
			// touch. This means we need to rely on coordinates for blocking
			// any click that is generated.
			t = getNativeEvent( event ).changedTouches[ 0 ];
			clickBlockList.push({
				touchID: lastTouchID,
				x: t.clientX,
				y: t.clientY
			});

			// Prevent any mouse events that follow from triggering
			// virtual event notifications.
			blockMouseTriggers = true;
		}
	}
	triggerVirtualEvent( "vmouseout", event, flags);
	didScroll = false;

	startResetTimer();
}

function hasVirtualBindings( ele ) {
	var bindings = $.data( ele, dataPropertyName ),
		k;

	if ( bindings ) {
		for ( k in bindings ) {
			if ( bindings[ k ] ) {
				return true;
			}
		}
	}
	return false;
}

function dummyMouseHandler(){}

function getSpecialEventObject( eventType ) {
	var realType = eventType.substr( 1 );

	return {
		setup: function( data, namespace ) {
			// If this is the first virtual mouse binding for this element,
			// add a bindings object to its data.

			if ( !hasVirtualBindings( this ) ) {
				$.data( this, dataPropertyName, {});
			}

			// If setup is called, we know it is the first binding for this
			// eventType, so initialize the count for the eventType to zero.
			var bindings = $.data( this, dataPropertyName );
			bindings[ eventType ] = true;

			// If this is the first virtual mouse event for this type,
			// register a global handler on the document.

			activeDocHandlers[ eventType ] = ( activeDocHandlers[ eventType ] || 0 ) + 1;

			if ( activeDocHandlers[ eventType ] === 1 ) {
				$document.bind( realType, mouseEventCallback );
			}

			// Some browsers, like Opera Mini, won't dispatch mouse/click events
			// for elements unless they actually have handlers registered on them.
			// To get around this, we register dummy handlers on the elements.

			$( this ).bind( realType, dummyMouseHandler );

			// For now, if event capture is not supported, we rely on mouse handlers.
			if ( eventCaptureSupported ) {
				// If this is the first virtual mouse binding for the document,
				// register our touchstart handler on the document.

				activeDocHandlers[ "touchstart" ] = ( activeDocHandlers[ "touchstart" ] || 0) + 1;

				if (activeDocHandlers[ "touchstart" ] === 1) {
					$document.bind( "touchstart", handleTouchStart )
						.bind( "touchend", handleTouchEnd )

						// On touch platforms, touching the screen and then dragging your finger
						// causes the window content to scroll after some distance threshold is
						// exceeded. On these platforms, a scroll prevents a click event from being
						// dispatched, and on some platforms, even the touchend is suppressed. To
						// mimic the suppression of the click event, we need to watch for a scroll
						// event. Unfortunately, some platforms like iOS don't dispatch scroll
						// events until *AFTER* the user lifts their finger (touchend). This means
						// we need to watch both scroll and touchmove events to figure out whether
						// or not a scroll happenens before the touchend event is fired.

						.bind( "touchmove", handleTouchMove )
						.bind( "scroll", handleScroll );
				}
			}
		},

		teardown: function( data, namespace ) {
			// If this is the last virtual binding for this eventType,
			// remove its global handler from the document.

			--activeDocHandlers[ eventType ];

			if ( !activeDocHandlers[ eventType ] ) {
				$document.unbind( realType, mouseEventCallback );
			}

			if ( eventCaptureSupported ) {
				// If this is the last virtual mouse binding in existence,
				// remove our document touchstart listener.

				--activeDocHandlers[ "touchstart" ];

				if ( !activeDocHandlers[ "touchstart" ] ) {
					$document.unbind( "touchstart", handleTouchStart )
						.unbind( "touchmove", handleTouchMove )
						.unbind( "touchend", handleTouchEnd )
						.unbind( "scroll", handleScroll );
				}
			}

			var $this = $( this ),
				bindings = $.data( this, dataPropertyName );

			// teardown may be called when an element was
			// removed from the DOM. If this is the case,
			// jQuery core may have already stripped the element
			// of any data bindings so we need to check it before
			// using it.
			if ( bindings ) {
				bindings[ eventType ] = false;
			}

			// Unregister the dummy event handler.

			$this.unbind( realType, dummyMouseHandler );

			// If this is the last virtual mouse binding on the
			// element, remove the binding data from the element.

			if ( !hasVirtualBindings( this ) ) {
				$this.removeData( dataPropertyName );
			}
		}
	};
}

// Expose our custom events to the jQuery bind/unbind mechanism.

for ( var i = 0; i < virtualEventNames.length; i++ ){
	$.event.special[ virtualEventNames[ i ] ] = getSpecialEventObject( virtualEventNames[ i ] );
}

// Add a capture click handler to block clicks.
// Note that we require event capture support for this so if the device
// doesn't support it, we punt for now and rely solely on mouse events.
if ( eventCaptureSupported ) {
	document.addEventListener( "click", function( e ){
		var cnt = clickBlockList.length,
			target = e.target,
			x, y, ele, i, o, touchID;

		if ( cnt ) {
			x = e.clientX;
			y = e.clientY;
			threshold = $.vmouse.clickDistanceThreshold;

			// The idea here is to run through the clickBlockList to see if
			// the current click event is in the proximity of one of our
			// vclick events that had preventDefault() called on it. If we find
			// one, then we block the click.
			//
			// Why do we have to rely on proximity?
			//
			// Because the target of the touch event that triggered the vclick
			// can be different from the target of the click event synthesized
			// by the browser. The target of a mouse/click event that is syntehsized
			// from a touch event seems to be implementation specific. For example,
			// some browsers will fire mouse/click events for a link that is near
			// a touch event, even though the target of the touchstart/touchend event
			// says the user touched outside the link. Also, it seems that with most
			// browsers, the target of the mouse/click event is not calculated until the
			// time it is dispatched, so if you replace an element that you touched
			// with another element, the target of the mouse/click will be the new
			// element underneath that point.
			//
			// Aside from proximity, we also check to see if the target and any
			// of its ancestors were the ones that blocked a click. This is necessary
			// because of the strange mouse/click target calculation done in the
			// Android 2.1 browser, where if you click on an element, and there is a
			// mouse/click handler on one of its ancestors, the target will be the
			// innermost child of the touched element, even if that child is no where
			// near the point of touch.

			ele = target;

			while ( ele ) {
				for ( i = 0; i < cnt; i++ ) {
					o = clickBlockList[ i ];
					touchID = 0;

					if ( ( ele === target && Math.abs( o.x - x ) < threshold && Math.abs( o.y - y ) < threshold ) ||
								$.data( ele, touchTargetPropertyName ) === o.touchID ) {
						// XXX: We may want to consider removing matches from the block list
						//      instead of waiting for the reset timer to fire.
						e.preventDefault();
						e.stopPropagation();
						return;
					}
				}
				ele = ele.parentNode;
			}
		}
	}, true);
}
})( jQuery, window, document );

},{}]},{},[1]);
