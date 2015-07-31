(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
require('../third_party/jquery.mobile.vmouse.js');
$.extend(KhanUtil, {
    initUnitCircle: function (degrees) {
        var graph = KhanUtil.currentGraph;
        var options = {
            xpixels: 514,
            ypixels: 514,
            range: [
                [
                    -1.2,
                    1.2
                ],
                [
                    -1.2,
                    1.2
                ]
            ]
        };
        options.scale = [
            options.xpixels / (options.range[0][1] - options.range[0][0]),
            options.ypixels / (options.range[1][1] - options.range[1][0])
        ];
        graph.init(options);
        graph.xpixels = options.xpixels;
        graph.ypixels = options.ypixels;
        graph.range = options.range;
        graph.scale = options.scale;
        graph.angle = 0;
        graph.revolutions = 0;
        graph.quadrant = 1;
        graph.dragging = false;
        graph.highlight = false;
        graph.degrees = degrees;
        graph.style({
            stroke: '#ddd',
            strokeWidth: 1,
            arrows: '->'
        }, function () {
            graph.circle([
                0,
                0
            ], 1);
            graph.line([
                -1.2,
                0
            ], [
                1.2,
                0
            ]);
            graph.line([
                0,
                -1.2
            ], [
                0,
                1.2
            ]);
            graph.line([
                1.2,
                0
            ], [
                -1.2,
                0
            ]);
            graph.line([
                0,
                1.2
            ], [
                0,
                -1.2
            ]);
        });
        graph.style({ strokeWidth: 2 }, function () {
            graph.line([
                -1,
                -5 / graph.scale[0]
            ], [
                -1,
                5 / graph.scale[0]
            ]);
            graph.line([
                1,
                -5 / graph.scale[0]
            ], [
                1,
                5 / graph.scale[0]
            ]);
            graph.line([
                -5 / graph.scale[0],
                -1
            ], [
                5 / graph.scale[0],
                -1
            ]);
            graph.line([
                -5 / graph.scale[0],
                1
            ], [
                5 / graph.scale[0],
                1
            ]);
        });
        graph.triangle = KhanUtil.bogusShape;
        graph.rightangle = KhanUtil.bogusShape;
        graph.spiral = KhanUtil.bogusShape;
        graph.arrow = KhanUtil.bogusShape;
        graph.cosLabel = KhanUtil.bogusShape;
        graph.sinLabel = KhanUtil.bogusShape;
        graph.radiusLabel = KhanUtil.bogusShape;
        graph.angleLabel = KhanUtil.bogusShape;
        graph.angleLines = KhanUtil.bogusShape;
        KhanUtil.initMouseHandlers();
        KhanUtil.setAngle(graph.angle);
    },
    bogusShape: {
        animate: function () {
        },
        attr: function () {
        },
        remove: function () {
        }
    },
    initMouseHandlers: function () {
        var graph = KhanUtil.currentGraph;
        graph.mouselayer = Raphael('unitcircle', graph.xpixels, graph.ypixels);
        $(graph.mouselayer.canvas).css('z-index', 1);
        Khan.scratchpad.disable();
        graph.style({
            stroke: KhanUtil.ORANGE,
            fill: KhanUtil.ORANGE
        }, function () {
            graph.dragPoint = graph.circle([
                1,
                0
            ], 4 / graph.scale[0]);
        });
        graph.mouseTarget = graph.mouselayer.circle((1 - graph.range[0][0]) * graph.scale[0], (graph.range[1][1] - 0) * graph.scale[1], 15);
        graph.mouseTarget.attr({
            fill: '#000',
            'opacity': 0
        });
        $(graph.mouseTarget[0]).css('cursor', 'move');
        $(graph.mouseTarget[0]).bind('vmousedown vmouseover vmouseout', function (event) {
            var graph = KhanUtil.currentGraph;
            if (event.type === 'vmouseover') {
                graph.highlight = true;
                if (!graph.dragging) {
                    KhanUtil.highlightAngle();
                }
            } else if (event.type === 'vmouseout') {
                graph.highlight = false;
                if (!graph.dragging) {
                    KhanUtil.unhighlightAngle();
                }
            } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                event.preventDefault();
                $(document).bind('vmousemove vmouseup', function (event) {
                    event.preventDefault();
                    graph.dragging = true;
                    var mouseY = event.pageY - $('#unitcircle').offset().top;
                    var mouseX = event.pageX - $('#unitcircle').offset().left;
                    var coordX = mouseX / graph.scale[0] + graph.range[0][0];
                    var coordY = graph.range[1][1] - mouseY / graph.scale[1];
                    if (event.type === 'vmousemove') {
                        var angle;
                        if (coordX) {
                            angle = Math.atan(coordY / coordX);
                        } else {
                            if (coordY > 0) {
                                angle = -Math.PI / 2;
                            } else {
                                angle = -Math.PI / 2;
                            }
                        }
                        angle = Math.round(angle / (Math.PI / 36)) * (Math.PI / 36);
                        if (coordX > 0 && coordY >= 0) {
                            if (graph.quadrant === 4) {
                                ++graph.revolutions;
                            }
                            graph.quadrant = 1;
                        } else if (coordX <= 0 && coordY > 0) {
                            angle += Math.PI;
                            graph.quadrant = 2;
                        } else if (coordX < 0 && coordY <= 0) {
                            angle += Math.PI;
                            graph.quadrant = 3;
                        } else if (coordX >= 0 && coordY < 0) {
                            angle += 2 * Math.PI;
                            if (graph.quadrant === 1) {
                                --graph.revolutions;
                            }
                            graph.quadrant = 4;
                        }
                        if (graph.revolutions <= -3) {
                            graph.revolutions = -3;
                            angle = 2 * Math.PI;
                        } else if (graph.revolutions >= 2) {
                            graph.revolutions = 2;
                            angle = 0;
                        }
                        if (graph.angle !== angle + graph.revolutions * 2 * Math.PI) {
                            KhanUtil.setAngle(angle + graph.revolutions * 2 * Math.PI);
                        }
                    } else if (event.type === 'vmouseup') {
                        $(document).unbind('vmousemove vmouseup');
                        graph.dragging = false;
                        if (!graph.highlight) {
                            KhanUtil.unhighlightAngle();
                        }
                    }
                });
            }
        });
    },
    highlightAngle: function () {
        var graph = KhanUtil.currentGraph;
        graph.dragPoint.animate({ scale: 2 }, 50);
        graph.angleLines.animate({ stroke: KhanUtil.ORANGE }, 100);
        graph.spiral.animate({ stroke: KhanUtil.ORANGE }, 100);
        graph.arrow.animate({ fill: KhanUtil.ORANGE }, 100);
        $(graph.angleLabel).animate({ color: KhanUtil.ORANGE }, 100);
    },
    unhighlightAngle: function () {
        var graph = KhanUtil.currentGraph;
        graph.dragPoint.animate({ scale: 1 }, 50);
        graph.angleLines.animate({ stroke: KhanUtil.BLUE }, 100);
        graph.spiral.animate({ stroke: KhanUtil.BLUE }, 100);
        graph.arrow.animate({ fill: KhanUtil.BLUE }, 100);
        $(graph.angleLabel).animate({ color: KhanUtil.BLUE }, 100);
    },
    setAngle: function (angle) {
        var graph = KhanUtil.currentGraph;
        graph.angle = angle;
        graph.quadrant = Math.floor((angle + 10 * Math.PI) / (Math.PI / 2)) % 4 + 1;
        graph.revolutions = Math.floor(angle / (2 * Math.PI));
        graph.triangle.remove();
        graph.rightangle.remove();
        graph.spiral.remove();
        graph.arrow.remove();
        graph.cosLabel.remove();
        graph.sinLabel.remove();
        graph.radiusLabel.remove();
        graph.angleLabel.remove();
        graph.angleLines.remove();
        var highlightColor = KhanUtil.BLUE;
        if (graph.dragging || graph.highlight) {
            highlightColor = KhanUtil.ORANGE;
        }
        graph.style({
            stroke: highlightColor,
            strokeWidth: 3
        });
        graph.angleLines = graph.path([
            [
                1,
                0
            ],
            [
                0,
                0
            ],
            [
                Math.cos(angle),
                Math.sin(angle)
            ]
        ]);
        graph.style({
            stroke: KhanUtil.BLUE,
            strokeWidth: 1
        });
        graph.triangle = graph.path([
            [
                0,
                0
            ],
            [
                Math.cos(angle),
                0
            ],
            [
                Math.cos(angle),
                Math.sin(angle)
            ],
            [
                0,
                0
            ]
        ]);
        var cosText = KhanUtil.roundTo(3, Math.cos(angle));
        var sinText = KhanUtil.roundTo(3, Math.sin(angle));
        var prettyAngles = {
            '0.866': '\\frac{\\sqrt{3}}{2}\\;(0.866)',
            '-0.866': '-\\frac{\\sqrt{3}}{2}\\;(-0.866)',
            '0.707': '\\frac{\\sqrt{2}}{2}\\;(0.707)',
            '-0.707': '-\\frac{\\sqrt{2}}{2}\\;(-0.707)',
            '0.5': '\\frac{1}{2}\\;(0.5)',
            '-0.5': '-\\frac{1}{2}\\;(-0.5)'
        };
        cosText = prettyAngles[cosText] ? prettyAngles[cosText] : cosText;
        sinText = prettyAngles[sinText] ? prettyAngles[sinText] : sinText;
        if (angle % Math.PI === 0) {
            graph.cosLabel = graph.label([
                Math.cos(angle) / 2,
                0
            ], cosText, 'below');
        } else if (angle % (Math.PI / 2) === 0) {
            graph.sinLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle) / 2
            ], sinText, 'right');
        } else if (graph.quadrant === 1) {
            graph.cosLabel = graph.label([
                Math.cos(angle) / 2,
                0
            ], cosText, 'below');
            graph.sinLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle) / 2
            ], sinText, 'right');
            graph.radiusLabel = graph.label([
                Math.cos(angle) / 2,
                Math.sin(angle) / 2
            ], 1, 'above left');
            graph.rightangle = graph.path([
                [
                    Math.cos(angle) - 0.04,
                    0
                ],
                [
                    Math.cos(angle) - 0.04,
                    0.04
                ],
                [
                    Math.cos(angle),
                    0.04
                ]
            ]);
        } else if (graph.quadrant === 2) {
            graph.cosLabel = graph.label([
                Math.cos(angle) / 2,
                0
            ], cosText, 'below');
            graph.sinLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle) / 2
            ], sinText, 'left');
            graph.radiusLabel = graph.label([
                Math.cos(angle) / 2,
                Math.sin(angle) / 2
            ], 1, 'above right');
            graph.rightangle = graph.path([
                [
                    Math.cos(angle) + 0.04,
                    0
                ],
                [
                    Math.cos(angle) + 0.04,
                    0.04
                ],
                [
                    Math.cos(angle),
                    0.04
                ]
            ]);
        } else if (graph.quadrant === 3) {
            graph.cosLabel = graph.label([
                Math.cos(angle) / 2,
                0
            ], cosText, 'above');
            graph.sinLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle) / 2
            ], sinText, 'left');
            graph.radiusLabel = graph.label([
                Math.cos(angle) / 2,
                Math.sin(angle) / 2
            ], 1, 'below right');
            graph.rightangle = graph.path([
                [
                    Math.cos(angle) + 0.04,
                    0
                ],
                [
                    Math.cos(angle) + 0.04,
                    -0.04
                ],
                [
                    Math.cos(angle),
                    -0.04
                ]
            ]);
        } else if (graph.quadrant === 4) {
            graph.cosLabel = graph.label([
                Math.cos(angle) / 2,
                0
            ], cosText, 'above');
            graph.sinLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle) / 2
            ], sinText, 'right');
            graph.radiusLabel = graph.label([
                Math.cos(angle) / 2,
                Math.sin(angle) / 2
            ], 1, 'below left');
            graph.rightangle = graph.path([
                [
                    Math.cos(angle) - 0.04,
                    0
                ],
                [
                    Math.cos(angle) - 0.04,
                    -0.04
                ],
                [
                    Math.cos(angle),
                    -0.04
                ]
            ]);
        }
        var points = [];
        for (var i = 0; i <= 50; ++i) {
            points.push([
                Math.cos(i * angle / 50) * (0.1 + i * Math.abs(angle) / 50 / Math.PI * 0.02),
                Math.sin(i * angle / 50) * (0.1 + i * Math.abs(angle) / 50 / Math.PI * 0.02)
            ]);
        }
        graph.style({
            strokeWidth: 2,
            stroke: highlightColor
        });
        graph.spiral = graph.path(points);
        var spiralEndX = points[50][0];
        var spiralEndY = points[50][1];
        graph.style({
            stroke: false,
            fill: highlightColor
        }, function () {
            if (angle > Math.PI / 12) {
                graph.arrow = graph.path([
                    [
                        spiralEndX,
                        spiralEndY - 0.005
                    ],
                    [
                        spiralEndX - 0.02,
                        spiralEndY - 0.03
                    ],
                    [
                        spiralEndX + 0.02,
                        spiralEndY - 0.03
                    ],
                    [
                        spiralEndX,
                        spiralEndY - 0.005
                    ]
                ]);
                graph.arrow.rotate((angle - Math.PI / 20) * (-180 / Math.PI), (spiralEndX - graph.range[0][0]) * graph.scale[0], (graph.range[1][1] - spiralEndY) * graph.scale[1]);
            } else if (angle < -Math.PI / 12) {
                graph.arrow = graph.path([
                    [
                        spiralEndX,
                        spiralEndY + 0.005
                    ],
                    [
                        spiralEndX - 0.02,
                        spiralEndY + 0.03
                    ],
                    [
                        spiralEndX + 0.02,
                        spiralEndY + 0.03
                    ],
                    [
                        spiralEndX,
                        spiralEndY + 0.005
                    ]
                ]);
                graph.arrow.rotate((angle + Math.PI / 20) * (-180 / Math.PI), (spiralEndX - graph.range[0][0]) * graph.scale[0], (graph.range[1][1] - spiralEndY) * graph.scale[1]);
            } else {
                graph.arrow = KhanUtil.bogusShape;
            }
        });
        var angleText = angle;
        if (graph.degrees) {
            angleText *= 180 / Math.PI;
            angleText = Math.round(angleText);
            angleText += '^{\\circ}';
        } else if (-15 < angle && angle < 15 && angle !== 0) {
            angleText = KhanUtil.piFraction(angle);
        }
        if (angle < -3.5 * Math.PI) {
            graph.angleLabel = graph.label([
                -0.2,
                0.2
            ], angleText, 'center');
        } else if (angle < -0.15 * Math.PI) {
            graph.angleLabel = graph.label([
                Math.cos(angle / 2) / 5,
                Math.sin(angle / 2) / 5
            ], angleText, 'center');
        } else if (angle < 0.15 * Math.PI) {
            graph.angleLabel = graph.label([
                0,
                0
            ], angleText, 'left');
        } else if (angle < 3.5 * Math.PI) {
            graph.angleLabel = graph.label([
                Math.cos(angle / 2) / 5,
                Math.sin(angle / 2) / 5
            ], angleText, 'center');
        } else {
            graph.angleLabel = graph.label([
                -0.2,
                -0.2
            ], angleText, 'center');
        }
        $(graph.angleLabel).css('color', highlightColor);
        graph.mouseTarget.attr('cx', (Math.cos(angle) - graph.range[0][0]) * graph.scale[0]);
        graph.mouseTarget.attr('cy', (graph.range[1][1] - Math.sin(angle)) * graph.scale[1]);
        graph.dragPoint.attr('cx', (Math.cos(angle) - graph.range[0][0]) * graph.scale[0]);
        graph.dragPoint.attr('cy', (graph.range[1][1] - Math.sin(angle)) * graph.scale[1]);
        graph.angleLines.toFront();
        graph.dragPoint.toFront();
    },
    goToAngle: function (angle) {
        var graph = KhanUtil.currentGraph;
        if (graph.degrees) {
            angle *= Math.PI / 180;
        }
        var duration = 1000 * Math.abs(angle - graph.angle) / Math.PI;
        $(graph).animate({ angle: angle }, {
            duration: duration,
            easing: 'linear',
            step: function (now, fx) {
                KhanUtil.setAngle(now);
            }
        });
    },
    showCoordinates: function (angle, highlightCoord) {
        var graph = KhanUtil.currentGraph;
        if (graph.degrees) {
            angle *= Math.PI / 180;
        }
        graph.style({
            stroke: 0,
            fill: KhanUtil.BLUE
        }, function () {
            graph.circle([
                Math.cos(angle),
                Math.sin(angle)
            ], 4 / graph.scale[0]);
        });
        graph.dragPoint.toFront();
        var xCoord = KhanUtil.roundTo(3, Math.cos(angle));
        var yCoord = KhanUtil.roundTo(3, Math.sin(angle));
        if (highlightCoord === 'x') {
            xCoord = '\\pink{' + xCoord + '}';
        }
        if (highlightCoord === 'y') {
            yCoord = '\\pink{' + yCoord + '}';
        }
        var coordText = '(' + xCoord + ', ' + yCoord + ')';
        if (Math.floor(angle / Math.PI) % 2) {
            graph.coordLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle)
            ], coordText, 'below');
        } else {
            graph.coordLabel = graph.label([
                Math.cos(angle),
                Math.sin(angle)
            ], coordText, 'above');
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
