(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
require('../third_party/jquery.mobile.vmouse.js');
$.extend(KhanUtil, {
    FN_COLOR: '#6495ED',
    DDX_COLOR: '#FFA500',
    TANGENT_COLOR: '#AAA',
    TANGENT_LINE_LENGTH: 200,
    TANGENT_GROWTH_FACTOR: 3,
    TANGENT_SHIFT: 5,
    initAutoscaledGraph: function (range, options) {
        var graph = KhanUtil.currentGraph;
        options = $.extend({
            xpixels: 500,
            ypixels: 500,
            xdivisions: 20,
            ydivisions: 20,
            labels: true,
            unityLabels: true,
            range: typeof range === 'undefined' ? [
                [
                    -10,
                    10
                ],
                [
                    -10,
                    10
                ]
            ] : range
        }, options);
        options.scale = [
            options.xpixels / (options.range[0][1] - options.range[0][0]),
            options.ypixels / (options.range[1][1] - options.range[1][0])
        ];
        options.gridStep = [
            (options.range[0][1] - options.range[0][0]) / options.xdivisions,
            (options.range[1][1] - options.range[1][0]) / options.ydivisions
        ];
        graph.xpixels = options.xpixels;
        graph.ypixels = options.ypixels;
        graph.range = options.range;
        graph.scale = options.scale;
        graph.graphInit(options);
    },
    initDerivativeIntuition: function (fnx, ddx, points) {
        var graph = KhanUtil.currentGraph;
        KhanUtil.fnx = fnx;
        KhanUtil.ddx = ddx;
        KhanUtil.points = points;
        KhanUtil.highlight = false;
        KhanUtil.dragging = false;
        KhanUtil.ddxShown = false;
        graph.tangentLines = [];
        graph.tangentPoints = [];
        graph.slopePoints = [];
        graph.mouseTargets = [];
        graph.mouselayer = Raphael('ddxplot', graph.xpixels, graph.ypixels);
        $(graph.mouselayer.canvas).css('z-index', 1);
        Khan.scratchpad.disable();
        $(points).each(function (index, xval) {
            KhanUtil.plotTangentLine(index);
        });
        $(points).each(function (index, xval) {
            KhanUtil.plotTangentPoint(index);
            KhanUtil.plotSlopePoint(index);
        });
        $(Exercises).one('newProblem', function () {
            $(points).each(function (index, xval) {
                KhanUtil.setSlope(index, 0);
            });
        });
    },
    plotTangentLine: function (index) {
        var graph = KhanUtil.currentGraph;
        var xval = KhanUtil.points[index];
        var yval = KhanUtil.fnx(xval);
        var xshift = xval;
        var yshift = yval;
        var perpslope = 0;
        var ddx1 = KhanUtil.ddx(xval);
        var ddx2 = (KhanUtil.ddx(xval - 0.001) - KhanUtil.ddx(xval + 0.001)) / 0.002;
        if (ddx1 !== 0) {
            perpslope = -1 / (ddx1 * (graph.scale[1] / graph.scale[0])) / (graph.scale[1] / graph.scale[0]);
            if (ddx2 > 0 && perpslope > 0 || ddx2 < 0 && perpslope < 0) {
                xshift = xval + Math.cos(Math.atan(perpslope * (graph.scale[1] / graph.scale[0]))) * KhanUtil.TANGENT_SHIFT / (2 * graph.scale[0]);
                yshift = perpslope * (xshift - xval) + yval;
            } else if (ddx2 < 0 && perpslope > 0 || ddx2 > 0 && perpslope < 0) {
                xshift = xval - Math.cos(Math.atan(perpslope * (graph.scale[1] / graph.scale[0]))) * KhanUtil.TANGENT_SHIFT / (2 * graph.scale[0]);
                yshift = perpslope * (xshift - xval) + yval;
            }
        } else {
            if (ddx2 < 0) {
                yshift = yval - KhanUtil.TANGENT_SHIFT / (2 * graph.scale[1]);
            } else if (ddx2 > 0) {
                yshift = yval + KhanUtil.TANGENT_SHIFT / (2 * graph.scale[1]);
            }
        }
        graph.style({
            stroke: KhanUtil.TANGENT_COLOR,
            strokeWidth: 2
        }, function () {
            graph.tangentLines[index] = graph.line([
                xshift - KhanUtil.TANGENT_LINE_LENGTH / (2 * graph.scale[0]),
                yshift
            ], [
                xshift + KhanUtil.TANGENT_LINE_LENGTH / (2 * graph.scale[0]),
                yshift
            ]);
        });
    },
    plotTangentPoint: function (index) {
        var graph = KhanUtil.currentGraph;
        var xval = KhanUtil.points[index];
        graph.style({
            fill: KhanUtil.FN_COLOR,
            stroke: KhanUtil.FN_COLOR
        }, function () {
            graph.tangentPoints[index] = graph.ellipse([
                xval,
                KhanUtil.fnx(xval)
            ], [
                4 / graph.scale[0],
                4 / graph.scale[1]
            ]);
        });
    },
    plotSlopePoint: function (index) {
        var graph = KhanUtil.currentGraph;
        var xval = KhanUtil.points[index];
        graph.style({
            fill: KhanUtil.DDX_COLOR,
            stroke: KhanUtil.DDX_COLOR
        }, function () {
            graph.slopePoints[index] = graph.ellipse([
                xval,
                0
            ], [
                4 / graph.scale[0],
                4 / graph.scale[1]
            ]);
        });
        var $ddxplot = $('#ddxplot');
        var $solutionAreaText = $('div#solutionarea :text').eq(index);
        var $solutionAreaLabel = $('div#solutionarea .answer-label').eq(index);
        graph.mouseTargets[index] = graph.mouselayer.circle((xval - graph.range[0][0]) * graph.scale[0], (graph.range[1][1] - 0) * graph.scale[1], 22);
        graph.mouseTargets[index].attr({
            fill: '#000',
            'opacity': 0
        });
        $(graph.mouseTargets[index][0]).css('cursor', 'move');
        $(graph.mouseTargets[index][0]).bind('vmousedown vmouseover vmouseout', function (event) {
            event.preventDefault();
            var graph = KhanUtil.currentGraph;
            if (event.type === 'vmouseover') {
                KhanUtil.highlight = true;
                if (!KhanUtil.dragging) {
                    graph.slopePoints[index].animate({ scale: 2 }, 50);
                    graph.tangentLines[index].animate({ 'stroke': KhanUtil.DDX_COLOR }, 100);
                }
            } else if (event.type === 'vmouseout') {
                KhanUtil.highlight = false;
                if (!KhanUtil.dragging) {
                    graph.slopePoints[index].animate({ scale: 1 }, 50);
                    graph.tangentLines[index].animate({ 'stroke': KhanUtil.TANGENT_COLOR }, 100);
                }
            } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                event.preventDefault();
                graph.tangentLines[index].toFront();
                graph.tangentPoints[index].toFront();
                graph.slopePoints[index].toFront();
                graph.tangentLines[index].animate({ scale: KhanUtil.TANGENT_GROWTH_FACTOR }, 200);
                KhanUtil.dragging = true;
                var ddxplotTop = $ddxplot.offset().top;
                $(document).bind('vmousemove vmouseup', function (event) {
                    event.preventDefault();
                    var mouseY = event.pageY - ddxplotTop;
                    mouseY = Math.max(10, Math.min(graph.ypixels - 10, mouseY));
                    var coordY = graph.range[1][1] - mouseY / graph.scale[1];
                    if (event.type === 'vmousemove') {
                        $solutionAreaText.val(KhanUtil.roundTo(2, coordY));
                        $solutionAreaLabel.text(KhanUtil.roundTo(2, coordY));
                        graph.tangentLines[index].rotate(-Math.atan(coordY * (graph.scale[1] / graph.scale[0])) * (180 / Math.PI), true);
                        graph.slopePoints[index].attr('cy', mouseY);
                        graph.mouseTargets[index].attr('cy', mouseY);
                    } else if (event.type === 'vmouseup') {
                        $(document).unbind('vmousemove vmouseup');
                        KhanUtil.setSlope(index, coordY);
                        KhanUtil.dragging = false;
                        graph.tangentLines[index].animate({ scale: 1 }, 200);
                        if (!KhanUtil.highlight) {
                            graph.slopePoints[index].animate({ scale: 1 }, 200);
                            graph.tangentLines[index].animate({ 'stroke': KhanUtil.TANGENT_COLOR }, 100);
                        }
                        var answers = $.map($('div#solutionarea .answer-label'), function (x) {
                            return parseFloat($(x).text());
                        });
                        var correct = $.map(KhanUtil.points, function (x) {
                            return KhanUtil.roundTo(2, KhanUtil.ddx(x));
                        });
                        if (answers.join() === correct.join()) {
                            KhanUtil.revealDerivative(400);
                        }
                    }
                });
            }
        });
    },
    setSlope: function (index, coordY) {
        var graph = KhanUtil.currentGraph;
        var answer = KhanUtil.ddx(KhanUtil.points[index]);
        var degreesOff = Math.abs(Math.atan(answer * graph.scale[1] / graph.scale[0]) - Math.atan(coordY * graph.scale[1] / graph.scale[0])) * (180 / Math.PI);
        if (degreesOff < 7) {
            coordY = answer;
        }
        $($('div#solutionarea :text')[index]).val(KhanUtil.roundTo(2, coordY));
        $($('div#solutionarea .answer-label')[index]).text(KhanUtil.roundTo(2, coordY));
        graph.tangentLines[index].rotate(-Math.atan(coordY * (graph.scale[1] / graph.scale[0])) * (180 / Math.PI), true);
        graph.slopePoints[index].attr('cy', (graph.range[1][1] - coordY) * graph.scale[1]);
        graph.mouseTargets[index].attr('cy', (graph.range[1][1] - coordY) * graph.scale[1]);
    },
    revealDerivative: function (duration) {
        if (!KhanUtil.ddxShown) {
            var graph = KhanUtil.currentGraph;
            var ddxplot;
            duration = duration || 0;
            graph.style({
                stroke: KhanUtil.DDX_COLOR,
                strokeWidth: 1,
                opacity: duration === 0 ? 1 : 0
            }, function () {
                ddxplot = graph.plot(function (x) {
                    return KhanUtil.ddx(x);
                }, KhanUtil.tmpl.getVAR('XRANGE'));
            });
            $('span#ddxspan').show();
            $('span#ddxspan').fadeTo(duration, 1);
            ddxplot.animate({ opacity: 1 }, duration);
            KhanUtil.ddxShown = true;
        }
    }
});
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
