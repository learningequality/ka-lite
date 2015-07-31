(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var kmatrix = require('./kmatrix.js');
$.extend(KhanUtil, {
    drawHintLine: function (pt1, pt2, ticks) {
        var graphie = KhanUtil.currentGraph;
        var length = KhanUtil.eDist(pt1, pt2);
        var midpoint = [
            (pt1[0] + pt2[0]) / 2,
            (pt1[1] + pt2[1]) / 2
        ];
        var angle = Math.atan2(pt2[1] - pt1[1], pt2[0] - pt1[0]);
        var transform = function (point) {
            var matrix = kmatrix.makeMatrix([
                [
                    Math.cos(angle),
                    -Math.sin(angle),
                    midpoint[0]
                ],
                [
                    Math.sin(angle),
                    Math.cos(angle),
                    midpoint[1]
                ],
                [
                    0,
                    0,
                    1
                ]
            ]);
            var vector = kmatrix.makeMatrix([
                [point[0]],
                [point[1]],
                [1]
            ]);
            var prod = kmatrix.matrixMult(matrix, vector);
            return [
                prod[0],
                prod[1]
            ];
        };
        var hintLine = graphie.raphael.set();
        hintLine.push(graphie.line(transform([
            -length / 2,
            0
        ]), transform([
            length / 2,
            0
        ]), {
            stroke: KhanUtil.BLUE,
            strokeWidth: 1,
            strokeDasharray: '- '
        }));
        graphie.style({
            stroke: KhanUtil.BLUE,
            strokeWidth: 1
        }, function () {
            if (ticks === 1) {
                hintLine.push(graphie.line(transform(graphie.unscaleVector([
                    0,
                    6
                ])), transform(graphie.unscaleVector([
                    0,
                    -6
                ]))));
            } else if (ticks === 2) {
                hintLine.push(graphie.line(transform(graphie.unscaleVector([
                    -3,
                    6
                ])), transform(graphie.unscaleVector([
                    -3,
                    -6
                ]))));
                hintLine.push(graphie.line(transform(graphie.unscaleVector([
                    3,
                    6
                ])), transform(graphie.unscaleVector([
                    3,
                    -6
                ]))));
            } else if (ticks === 3) {
                hintLine.push(graphie.line(transform(graphie.unscaleVector([
                    -6,
                    6
                ])), transform(graphie.unscaleVector([
                    -6,
                    -6
                ]))));
                hintLine.push(graphie.line(transform(graphie.unscaleVector([
                    0,
                    6
                ])), transform(graphie.unscaleVector([
                    0,
                    -6
                ]))));
                hintLine.push(graphie.line(transform(graphie.unscaleVector([
                    6,
                    6
                ])), transform(graphie.unscaleVector([
                    6,
                    -6
                ]))));
            }
        });
        return hintLine;
    },
    construction: {},
    showSnapPts: function () {
        var graphie = KhanUtil.currentGraph;
        var set = graphie.raphael.set();
        _.each(KhanUtil.construction.interPoints, function (pt) {
            set.push(graphie.circle(pt, 0.1, {
                stroke: KhanUtil.PINK,
                fill: KhanUtil.PINK
            }));
        });
        _.each(KhanUtil.construction.snapPoints, function (pt) {
            set.push(graphie.circle(pt.coord, 0.1, {
                stroke: KhanUtil.RED,
                fill: KhanUtil.RED
            }));
        });
        _.delay(function () {
            set.remove();
        }, 500);
    },
    addConstruction: function (graphieId) {
        var graphie = $('#' + graphieId).data('graphie');
        var construction = KhanUtil.construction = {
            tools: [],
            tool: {},
            snapPoints: [],
            interPoints: [],
            snapLines: []
        };
        construction.addCompass = function () {
            var start = [
                Math.random() * 4 - 2,
                Math.random() * 4 - 2
            ];
            var startRadius = Math.random() + 1.5;
            construction.tool = {
                interType: 'circle',
                center: graphie.addMovablePoint({
                    graph: graphie,
                    coord: start,
                    normalStyle: {
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }
                }),
                radius: startRadius,
                circ: graphie.circle(start, startRadius, {
                    stroke: KhanUtil.BLUE,
                    strokeDasharray: '- ',
                    fill: KhanUtil.ORANGE,
                    fillOpacity: 0
                }),
                perim: graphie.mouselayer.circle(graphie.scalePoint(start)[0], graphie.scalePoint(start)[1], graphie.scaleVector(startRadius)[0]).attr({
                    'stroke-width': 20,
                    'opacity': 0
                })
            };
            var t = construction.tool;
            $(t.center.mouseTarget.getMouseTarget()).bind('vmouseover vmouseout', function (event) {
                if (t.center.highlight) {
                    t.circ.animate({
                        stroke: KhanUtil.ORANGE,
                        'fill-opacity': 0.05
                    }, 50);
                } else {
                    t.circ.animate({
                        stroke: KhanUtil.BLUE,
                        'fill-opacity': 0
                    }, 50);
                }
            });
            construction.tools.push(t);
            construction.snapPoints.push(t.center);
            t.center.onMove = function (x, y) {
                t.circ.toFront();
                t.perim.toFront();
                t.center.visibleShape.toFront();
                t.center.mouseTarget.toFront();
                t.circ.attr({
                    cx: graphie.scalePoint(x)[0],
                    cy: graphie.scalePoint(y)[1]
                });
                t.perim.attr({
                    cx: graphie.scalePoint(x)[0],
                    cy: graphie.scalePoint(y)[1]
                });
            };
            t.center.onMoveEnd = function (x, y) {
                _.each(construction.snapLines, function (line) {
                    var distIntersect = KhanUtil.lDist(t.center.coord, line);
                    if (distIntersect[0] < 0.25) {
                        t.center.onMove(distIntersect[1][0], distIntersect[1][1]);
                        t.center.setCoord(distIntersect[1]);
                    }
                });
                var myPossibleSnaps = [];
                _.each(construction.snapPoints, function (point) {
                    if (KhanUtil.eDist(t.center.coord, point.coord) < 0.25 && t.center.coord !== point.coord) {
                        myPossibleSnaps.push(point.coord);
                    }
                });
                construction.updateIntersections();
                _.each(construction.interPoints, function (point) {
                    if (KhanUtil.eDist(t.center.coord, point) < 0.3 && t.center.coord !== point) {
                        myPossibleSnaps.push(point);
                    }
                });
                var mySnapPoint = [];
                var mySnapDist = null;
                _.each(myPossibleSnaps, function (sCoord) {
                    if (mySnapDist == null || KhanUtil.eDist(sCoord, t.center.coord) < mySnapDist) {
                        mySnapPoint = sCoord;
                        mySnapDist = KhanUtil.eDist(sCoord, t.center.coord);
                    }
                });
                if (mySnapPoint.length > 0) {
                    t.center.onMove(mySnapPoint[0], mySnapPoint[1]);
                    t.center.setCoord(mySnapPoint);
                }
            };
            $(t.perim[0]).css('cursor', 'move');
            $(t.perim[0]).bind('vmouseover vmouseout vmousedown', function (event) {
                if (event.type === 'vmouseover') {
                    t.highlight = true;
                    if (!KhanUtil.dragging) {
                        t.circ.animate({
                            stroke: KhanUtil.ORANGE,
                            'fill-opacity': 0.05
                        }, 50);
                        t.center.visibleShape.animate({
                            stroke: KhanUtil.ORANGE,
                            fill: KhanUtil.ORANGE
                        }, 50);
                    }
                } else if (event.type === 'vmouseout') {
                    t.highlight = false;
                    if (!t.dragging) {
                        t.circ.animate({
                            stroke: KhanUtil.BLUE,
                            'fill-opacity': 0
                        }, 50);
                        t.center.visibleShape.animate({
                            stroke: KhanUtil.BLUE,
                            fill: KhanUtil.BLUE
                        }, 50);
                    }
                } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                    event.preventDefault();
                    var data = t;
                    data.circ.toFront();
                    data.perim.toFront();
                    data.center.visibleShape.toFront();
                    data.center.mouseTarget.toFront();
                    $(document).bind('vmousemove vmouseup', function (event) {
                        event.preventDefault();
                        data.dragging = true;
                        KhanUtil.dragging = true;
                        if (event.type === 'vmousemove') {
                            var mouseX = event.pageX - $(graphie.raphael.canvas.parentNode).offset().left;
                            var mouseY = event.pageY - $(graphie.raphael.canvas.parentNode).offset().top;
                            data.radius = KhanUtil.eDist(data.center.coord, graphie.unscalePoint([
                                mouseX,
                                mouseY
                            ]));
                            data.perim.attr({ r: graphie.scaleVector(data.radius)[0] });
                            data.circ.attr({
                                rx: graphie.scaleVector(data.radius)[0],
                                ry: graphie.scaleVector(data.radius)[1]
                            });
                        } else if (event.type === 'vmouseup') {
                            $(document).unbind('vmousemove vmouseup');
                            data.dragging = false;
                            KhanUtil.dragging = false;
                            construction.updateIntersections();
                        }
                    });
                }
            });
            construction.updateIntersections();
        };
        construction.mark = function () {
            var x = -1;
            var y = Math.random() * 2;
            construction.tool = {
                interType: 'line',
                center: graphie.addMovablePoint({
                    graph: graphie,
                    coordX: x,
                    coordY: y,
                    normalStyle: {
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }
                })
            };
            construction.tool.line1 = graphie.addMovableLineSegment({
                graph: graphie,
                pointA: [
                    x + 0.2,
                    y + 0.2
                ],
                pointZ: [
                    x - 0.2,
                    y - 0.2
                ],
                normalStyle: {
                    stroke: KhanUtil.BLUE,
                    'stroke-width': 2
                },
                highlightStyle: {
                    stroke: KhanUtil.ORANGE,
                    'stroke-width': 3
                },
                movePointsWithLine: true
            });
            construction.tool.line2 = graphie.addMovableLineSegment({
                graph: graphie,
                pointA: [
                    x + 0.2,
                    y - 0.2
                ],
                pointZ: [
                    x - 0.2,
                    y + 0.2
                ],
                normalStyle: {
                    stroke: KhanUtil.BLUE,
                    'stroke-width': 2
                },
                highlightStyle: {
                    stroke: KhanUtil.ORANGE,
                    'stroke-width': 3
                },
                movePointsWithLine: true
            });
            $(construction.tool.center.mouseTarget.getMouseTarget()).bind('vmouseover vmouseout', construction.tool, function (event) {
                if (event.data.center.highlight) {
                    event.data.line1.visibleLine.animate({ stroke: KhanUtil.ORANGE }, 50);
                    event.data.line2.visibleLine.animate({ stroke: KhanUtil.ORANGE }, 50);
                } else {
                    event.data.line1.visibleLine.animate({ stroke: KhanUtil.BLUE }, 50);
                    event.data.line2.visibleShape.animate({ stroke: KhanUtil.BLUE }, 50);
                }
            });
            construction.tools.push(construction.tool);
            construction.snapPoints.push(construction.tool.center);
            var t = construction.tool;
            t.center.onMoveEnd = function (dX, dY) {
                t.line1.visibleLine.toFront();
                t.line1.mouseTarget.toFront();
                t.line2.visibleLine.toFront();
                t.line2.mouseTarget.toFront();
                t.center.visibleShape.toFront();
                t.center.mouseTarget.toFront();
            };
            $(t.center.mouseTarget.getMouseTarget()).bind('dblclick', function () {
                construction.removeTool(t, true);
            });
            construction.updateIntersections();
        };
        construction.addStraightedge = function (extend, fixed) {
            extend = extend == null ? true : extend;
            fixed = fixed == null ? false : fixed;
            construction.tool = {
                interType: 'line',
                first: graphie.addMovablePoint({
                    graph: graphie,
                    coordX: -1,
                    coordY: Math.random() * 2,
                    normalStyle: {
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }
                }),
                second: graphie.addMovablePoint({
                    graph: graphie,
                    coordX: 1,
                    coordY: Math.random() * 2,
                    normalStyle: {
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }
                })
            };
            construction.tool.edge = graphie.addMovableLineSegment({
                graph: graphie,
                pointA: construction.tool.first,
                pointZ: construction.tool.second,
                normalStyle: {
                    stroke: KhanUtil.BLUE,
                    'stroke-width': 2
                },
                highlightStyle: {
                    stroke: KhanUtil.ORANGE,
                    'stroke-width': 3
                },
                extendLine: extend,
                constraints: { fixed: fixed },
                movePointsWithLine: true
            });
            $(construction.tool.first.mouseTarget.getMouseTarget()).bind('vmouseover vmouseout', construction.tool, function (event) {
                if (event.data.first.highlight) {
                    event.data.edge.visibleLine.animate({ stroke: KhanUtil.ORANGE }, 50);
                    event.data.second.visibleShape.animate({
                        stroke: KhanUtil.ORANGE,
                        fill: KhanUtil.ORANGE
                    }, 50);
                } else {
                    event.data.edge.visibleLine.animate({ stroke: KhanUtil.BLUE }, 50);
                    event.data.second.visibleShape.animate({
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }, 50);
                }
            });
            $(construction.tool.second.mouseTarget.getMouseTarget()).bind('vmouseover vmouseout', construction.tool, function (event) {
                if (event.data.second.highlight) {
                    event.data.edge.visibleLine.animate({ stroke: KhanUtil.ORANGE }, 50);
                    event.data.first.visibleShape.animate({
                        stroke: KhanUtil.ORANGE,
                        fill: KhanUtil.ORANGE
                    }, 50);
                } else {
                    event.data.edge.visibleLine.animate({ stroke: KhanUtil.BLUE }, 50);
                    event.data.first.visibleShape.animate({
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }, 50);
                }
            });
            $(construction.tool.edge.mouseTarget.getMouseTarget()).bind('vmouseover vmouseout', construction.tool, function (event) {
                if (event.data.edge.highlight) {
                    event.data.first.visibleShape.animate({
                        stroke: KhanUtil.ORANGE,
                        fill: KhanUtil.ORANGE
                    }, 50);
                    event.data.second.visibleShape.animate({
                        stroke: KhanUtil.ORANGE,
                        fill: KhanUtil.ORANGE
                    }, 50);
                } else {
                    event.data.first.visibleShape.animate({
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }, 50);
                    event.data.second.visibleShape.animate({
                        stroke: KhanUtil.BLUE,
                        fill: KhanUtil.BLUE
                    }, 50);
                }
            });
            construction.tools.push(construction.tool);
            construction.snapPoints.push(construction.tool.first);
            construction.snapPoints.push(construction.tool.second);
            construction.snapLines.push(construction.tool.edge);
            var t = construction.tool;
            t.edge.onMoveEnd = function (dX, dY) {
                t.edge.visibleLine.toFront();
                t.edge.mouseTarget.toFront();
                t.first.visibleShape.toFront();
                t.first.mouseTarget.toFront();
                t.second.visibleShape.toFront();
                t.second.mouseTarget.toFront();
                t.first.onMoveEnd(t.first.coord[0], t.first.coord[1]);
                t.second.onMoveEnd(t.second.coord[0], t.second.coord[1]);
            };
            var endpointMoveEnd = function (x, y, end) {
                _.each(construction.snapLines, function (line) {
                    var distIntersect = KhanUtil.lDist(end.coord, line);
                    if (distIntersect[0] < 0.25) {
                        end.setCoord(distIntersect[1]);
                        end.updateLineEnds();
                    }
                });
                var myPossibleSnaps = [];
                _.each(construction.snapPoints, function (point) {
                    if (KhanUtil.eDist(end.coord, point.coord) < 0.25 && end.coord !== point.coord) {
                        myPossibleSnaps.push(point.coord);
                    }
                });
                construction.updateIntersections();
                _.each(construction.interPoints, function (point) {
                    if (KhanUtil.eDist(end.coord, point) < 0.3 && end.coord !== point) {
                        myPossibleSnaps.push(point);
                    }
                });
                var mySnapPoint = [];
                var mySnapDist = null;
                _.each(myPossibleSnaps, function (sCoord) {
                    if (mySnapDist == null || KhanUtil.eDist(sCoord, end.coord) < mySnapDist) {
                        mySnapPoint = sCoord;
                        mySnapDist = KhanUtil.eDist(sCoord, end.coord);
                    }
                });
                if (mySnapPoint.length > 0) {
                    end.setCoord(mySnapPoint);
                    end.updateLineEnds();
                }
                t.edge.visibleLine.toFront();
                t.edge.mouseTarget.toFront();
                t.first.visibleShape.toFront();
                t.first.mouseTarget.toFront();
                t.second.visibleShape.toFront();
                t.second.mouseTarget.toFront();
            };
            t.first.onMoveEnd = function (x, y) {
                endpointMoveEnd(x, y, t.first);
            };
            t.second.onMoveEnd = function (x, y) {
                endpointMoveEnd(x, y, t.second);
            };
            $(t.first.mouseTarget.getMouseTarget()).bind('dblclick', function () {
                construction.removeTool(t, true);
            });
            $(t.second.mouseTarget.getMouseTarget()).bind('dblclick', function () {
                construction.removeTool(t, true);
            });
            $(t.edge.mouseTarget.getMouseTarget()).bind('dblclick', function () {
                construction.removeTool(t, true);
            });
            construction.updateIntersections();
        };
        construction.removeTool = function (tool, updateTools) {
            _.each(_.keys(tool), function (key) {
                if (key === 'center' || key === 'perimeter' || key === 'first' || key === 'second') {
                    tool[key].visibleShape.remove();
                    tool[key].visible = false;
                    $(tool[key].mouseTarget.getMouseTarget()).remove();
                } else if (key === 'circ') {
                    tool[key].remove();
                } else if (key === 'edge') {
                    tool[key].remove();
                }
            });
            if (updateTools) {
                construction.tools.splice(_.indexOf(construction.tools, tool), 1);
            }
        };
        construction.removeAllTools = function () {
            var staticTools = [];
            _.each(construction.tools, function (tool) {
                if (tool.dummy) {
                    staticTools.push(tool);
                } else {
                    construction.removeTool(tool, false);
                }
            });
            construction.tools = staticTools;
            construction.snapPoints = construction.snapPoints.filter(function (point) {
                return point.dummy;
            });
            construction.interPoints = [];
            construction.snapLines = construction.snapLines.filter(function (line) {
                return line.dummy;
            });
        };
        construction.updateIntersections = function () {
            construction.interPoints = [];
            _.each(construction.tools, function (tool1) {
                _.each(construction.tools, function (tool2) {
                    if (tool1 !== tool2) {
                        if (tool1.interType === 'line' && tool2.interType === 'line') {
                            construction.interPoints.push(findIntersection([
                                tool1.first.coord,
                                tool1.second.coord
                            ], [
                                tool2.first.coord,
                                tool2.second.coord
                            ]).slice(0, 2));
                        } else if (tool1.interType === 'line' && tool2.interType === 'circle') {
                            var m = (tool1.second.coord[1] - tool1.first.coord[1]) / (tool1.second.coord[0] - tool1.first.coord[0]);
                            var yint = tool1.first.coord[1] - m * tool1.first.coord[0];
                            var cX = tool2.center.coord[0];
                            var cY = tool2.center.coord[1];
                            var rad = tool2.radius;
                            var a = 1 + Math.pow(m, 2);
                            var b = -2 * cX + 2 * m * yint - 2 * cY * m;
                            var c = Math.pow(yint, 2) - 2 * yint * cY + Math.pow(cY, 2) + Math.pow(cX, 2) - Math.pow(rad, 2);
                            var x1 = (-b + Math.sqrt(Math.pow(b, 2) - 4 * a * c)) / (2 * a);
                            var x2 = (-b - Math.sqrt(Math.pow(b, 2) - 4 * a * c)) / (2 * a);
                            if (!isNaN(x1)) {
                                var y1 = m * x1 + yint;
                                construction.interPoints.push([
                                    x1,
                                    y1
                                ]);
                            }
                            if (!isNaN(x2)) {
                                var y2 = m * x2 + yint;
                                construction.interPoints.push([
                                    x2,
                                    y2
                                ]);
                            }
                        } else if (tool1.center != null && tool2.center != null) {
                            var a = tool1.center.coord[0];
                            var b = tool1.center.coord[1];
                            var c = tool2.center.coord[0];
                            var d = tool2.center.coord[1];
                            var r = tool1.radius;
                            var s = tool2.radius;
                            var e = c - a;
                            var f = d - b;
                            var p = Math.sqrt(Math.pow(e, 2) + Math.pow(f, 2));
                            var k = (Math.pow(p, 2) + Math.pow(r, 2) - Math.pow(s, 2)) / (2 * p);
                            var x1 = a + e * k / p + f / p * Math.sqrt(Math.pow(r, 2) - Math.pow(k, 2));
                            var y1 = b + f * k / p - e / p * Math.sqrt(Math.pow(r, 2) - Math.pow(k, 2));
                            var x2 = a + e * k / p - f / p * Math.sqrt(Math.pow(r, 2) - Math.pow(k, 2));
                            var y2 = b + f * k / p + e / p * Math.sqrt(Math.pow(r, 2) - Math.pow(k, 2));
                            if (!isNaN(x1)) {
                                construction.interPoints.push([
                                    x1,
                                    y1
                                ]);
                            }
                            if (!isNaN(x2)) {
                                construction.interPoints.push([
                                    x2,
                                    y2
                                ]);
                            }
                        }
                    }
                });
            });
        };
    },
    addDummyStraightedge: function (coord1, coord2, extend) {
        var construction = KhanUtil.construction;
        extend = extend == null ? true : extend;
        construction.tool = {
            interType: 'line',
            dummy: true,
            first: {
                coord: [
                    coord1,
                    coord2
                ]
            },
            second: {
                coord: [
                    coord1,
                    coord2
                ]
            },
            edge: KhanUtil.currentGraph.addMovableLineSegment({
                coordA: coord1,
                coordZ: coord2,
                normalStyle: {
                    stroke: 'black',
                    'stroke-width': 2
                },
                highlightStyle: {
                    stroke: KhanUtil.BLUE,
                    'stroke-width': 3
                },
                extendLine: extend,
                fixed: true
            })
        };
        construction.tool.edge.dummy = true;
        if (construction.tools == null) {
            construction.tools = [construction.tool];
        } else {
            construction.tools.push(construction.tool);
        }
        if (construction.snapLines == null) {
            construction.snapLines = [construction.tool.edge];
        } else {
            construction.snapLines.push(construction.tool.edge);
        }
        KhanUtil.construction.updateIntersections();
    },
    addDummyCircle: function (center, radius) {
        var construction = KhanUtil.construction;
        var dummy = {
            coord: center,
            dummy: true
        };
        KhanUtil.currentGraph.circle(center, {
            r: radius,
            fill: 'none',
            stroke: 'black',
            'stroke-width': 2
        });
        if (construction.snapPoints == null) {
            construction.snapPoints = [dummy];
        } else {
            construction.snapPoints.push(dummy);
        }
        KhanUtil.construction.updateIntersections();
    },
    addDummyPoint: function (coordinates) {
        var dummy = {
            coord: coordinates,
            dummy: true
        };
        KhanUtil.currentGraph.circle(coordinates, {
            r: 0.08,
            fill: 'black',
            stroke: 'none'
        });
        var construction = KhanUtil.construction;
        if (construction.snapPoints == null) {
            construction.snapPoints = [dummy];
        } else {
            construction.snapPoints.push(dummy);
        }
        KhanUtil.construction.updateIntersections();
    },
    addDummyRay: function (end, other) {
        var construction = KhanUtil.construction;
        construction.tool = {
            interType: 'line',
            dummy: true,
            first: { coord: end },
            second: { coord: other },
            edge: {
                coordA: end,
                coordZ: other,
                dummy: true
            }
        };
        KhanUtil.currentGraph.line(end, other, {
            stroke: 'black',
            'stroke-width': 2,
            arrows: '->'
        });
        KhanUtil.addDummyPoint(end);
        if (construction.tools == null) {
            construction.tools = [construction.tool];
        } else {
            construction.tools.push(construction.tool);
        }
        if (construction.snapLines == null) {
            construction.snapLines = [construction.tool.edge];
        } else {
            construction.snapLines.push(construction.tool.edge);
        }
        KhanUtil.construction.updateIntersections();
    },
    constructionGuess: null,
    showConstructionGuess: function (guessTools) {
        var graph = KhanUtil.currentGraph;
        if (KhanUtil.constructionGuess != null) {
            KhanUtil.constructionGuess.remove();
        }
        KhanUtil.constructionGuess = graph.raphael.set();
        _.each(guessTools, function (tool) {
            if (tool.first != null) {
                KhanUtil.constructionGuess.push(graph.addMovableLineSegment({
                    coordA: tool.first.coord,
                    coordZ: tool.second.coord,
                    normalStyle: {
                        stroke: KhanUtil.BLUE,
                        'stroke-width': 2
                    },
                    extendLine: true,
                    fixed: true
                }).visibleLine);
                KhanUtil.constructionGuess.push(graph.circle(tool.first.coord, 0.1, {
                    fill: KhanUtil.BLUE,
                    stroke: null
                }));
                KhanUtil.constructionGuess.push(graph.circle(tool.second.coord, 0.1, {
                    fill: KhanUtil.BLUE,
                    stroke: null
                }));
            } else if (tool.center != null) {
                KhanUtil.constructionGuess.push(graph.circle(tool.center.coord, 0.1, {
                    fill: KhanUtil.BLUE,
                    stroke: null
                }));
                KhanUtil.constructionGuess.push(graph.circle(tool.center.coord, tool.radius, {
                    fill: 'none',
                    stroke: KhanUtil.BLUE,
                    strokeDasharray: '- '
                }));
            }
        });
    },
    eDist: function (coords1, coords2) {
        return Math.sqrt(Math.pow(coords1[0] - coords2[0], 2) + Math.pow(coords1[1] - coords2[1], 2));
    },
    lDist: function (coord, line) {
        var slope = (line.coordZ[1] - line.coordA[1]) / (line.coordZ[0] - line.coordA[0]);
        var perpSlope = slope === 0 ? 'vert' : -1 / slope;
        var coord2;
        if (perpSlope === 'vert') {
            coord2 = [
                coord[0],
                coord[1] + 1
            ];
        } else {
            coord2 = [
                coord[0] + 1,
                coord[1] + perpSlope
            ];
        }
        var intersect = findIntersection([
            coord,
            coord2
        ], [
            line.coordA,
            line.coordZ
        ]);
        return [
            KhanUtil.eDist(intersect, coord),
            intersect
        ];
    },
    distEqual: function (p1, p2, distance, precision) {
        precision = precision || 0.5;
        return Math.abs(KhanUtil.eDist(p1, p2) - distance) < precision;
    },
    angleEqual: function (line, angle, precision) {
        var ang = Math.atan2(line.second.coord[1] - line.first.coord[1], line.second.coord[0] - line.first.coord[0]);
        ang *= 180 / Math.PI;
        if (ang < 0) {
            ang += 180;
        }
        return Math.abs(angle - ang) < precision;
    },
    getToolProperties: function (construction) {
        return _.map(_.filter(construction.tools, function (tool) {
            return tool.dummy !== true;
        }), function (tool) {
            if (tool.first != null) {
                return {
                    first: {
                        coord: [
                            tool.first.coord[0],
                            tool.first.coord[1]
                        ]
                    },
                    second: {
                        coord: [
                            tool.second.coord[0],
                            tool.second.coord[1]
                        ]
                    }
                };
            } else if (tool.center != null) {
                return {
                    center: {
                        coord: [
                            tool.center.coord[0],
                            tool.center.coord[1]
                        ]
                    },
                    radius: tool.radius
                };
            }
        });
    },
    findCompass: function (guess, properties) {
        var testFunctions = [];
        if (properties.radius != null) {
            testFunctions.push(function (tool) {
                return Math.abs(tool.radius - properties.radius) < 0.5;
            });
        }
        if (properties.cx != null) {
            testFunctions.push(function (tool) {
                return Math.abs(tool.center.coord[0] - properties.cx) < 0.5;
            });
        }
        if (properties.cy != null) {
            testFunctions.push(function (tool) {
                return Math.abs(tool.center.coord[1] - properties.cy) < 0.5;
            });
        }
        if (properties.center != null) {
            testFunctions.push(function (tool) {
                return Math.abs(tool.center.coord[0] - properties.center[0]) < 0.5 && Math.abs(tool.center.coord[1] - properties.center[1]) < 0.5;
            });
        }
        return _.filter(guess, function (tool) {
            if (tool.center != null) {
                for (var i = 0; i < testFunctions.length; i++) {
                    if (!testFunctions[i](tool)) {
                        return false;
                    }
                }
                return true;
            }
        });
    },
    findInscribedPolygon: function (guess, center, radius, n) {
        var interiorAngle = 2 * Math.PI / n;
        var sideLength = 2 * radius * Math.sin(interiorAngle / 2);
        var lines = _.filter(guess, function (tool) {
            return tool.first != null && KhanUtil.distEqual(tool.first.coord, tool.second.coord, sideLength, 0.3) && KhanUtil.distEqual(tool.first.coord, center, radius, 0.3) && KhanUtil.distEqual(tool.second.coord, center, radius, 0.3);
        });
        if (lines.length < n) {
            return false;
        }
        var offsetAngle = 180 + Math.atan2(lines[0].first.coord[1], lines[0].first.coord[0]) * 180 / Math.PI;
        var angles = [];
        _.map(lines, function (tool) {
            var angle1 = Math.atan2(tool.first.coord[1], tool.first.coord[0]) * 180 / Math.PI;
            var angle2 = Math.atan2(tool.second.coord[1], tool.second.coord[0]) * 180 / Math.PI;
            angles.push((angle1 - offsetAngle + 540 + 180 / n) % 360);
            angles.push((angle2 - offsetAngle + 540 + 180 / n) % 360);
        });
        var targetAngles = {};
        for (var i = 0; i < n; i++) {
            targetAngles[(i + 0.5) * 360 / n] = 0;
        }
        var threshold = 4;
        _.map(angles, function (angle) {
            for (var i = 0; i < n; i++) {
                var targetAngle = (i + 0.5) * 360 / n;
                if (Math.abs(angle - targetAngle) < threshold) {
                    targetAngles[targetAngle]++;
                    break;
                }
            }
        });
        for (var angle in targetAngles) {
            if (targetAngles[angle] !== 2) {
                return false;
            }
        }
        return lines;
    }
});
},{"./kmatrix.js":3}],2:[function(require,module,exports){
$.extend(KhanUtil, {
    expr: function (expr, compute) {
        if (typeof expr === 'object') {
            var op = expr[0], args = expr.slice(1), table = compute ? KhanUtil.computeOperators : KhanUtil.formatOperators;
            return table[op].apply(this, args);
        } else {
            return compute ? expr : expr.toString();
        }
    },
    exprType: function (expr) {
        if (typeof expr === 'object') {
            if (expr[0] === 'color') {
                return KhanUtil.exprType(expr[2]);
            }
            return expr[0];
        } else {
            return typeof expr;
        }
    },
    exprIsNegated: function (expr) {
        switch (KhanUtil.exprType(expr)) {
        case 'color':
            return KhanUtil.exprIsNegated(expr[2]);
        case '/':
            return KhanUtil.exprIsNegated(expr[1]);
        case '+':
        case '-':
            return true;
        case 'number':
            return expr < 0;
        case 'string':
            return expr.charAt(0) === '-';
        default:
            return false;
        }
    },
    exprIsShort: function (expr) {
        switch (KhanUtil.exprType(expr)) {
        case 'color':
            return KhanUtil.exprIsShort(expr[2]);
        case '+':
        case '-':
        case '*':
        case '/':
        case 'frac':
            return false;
        case '^':
            return KhanUtil.exprType(expr[1]) !== 'number' || expr[1] < 0;
        case 'number':
        case 'sqrt':
            return true;
        default:
            return expr.length <= 1;
        }
    },
    exprParenthesize: function (expr) {
        return KhanUtil.exprIsShort(expr) ? KhanUtil.expr(expr) : '(' + KhanUtil.expr(expr) + ')';
    },
    formatOperators: {
        'color': function (color, arg) {
            return '\\color{' + color + '}{' + KhanUtil.expr(arg) + '}';
        },
        '+': function () {
            var args = [].slice.call(arguments, 0);
            var terms = $.grep(args, function (term, i) {
                return term != null;
            });
            terms = _.filter(terms, function (term) {
                return '' + KhanUtil.expr(term) !== '0';
            });
            terms = $.map(terms, function (term, i) {
                var parenthesize;
                switch (KhanUtil.exprType(term)) {
                case '+':
                    parenthesize = true;
                    break;
                case '-':
                    parenthesize = term.length > 2;
                    break;
                default:
                    parenthesize = false;
                }
                term = KhanUtil.expr(term);
                if (parenthesize) {
                    term = '(' + term + ')';
                }
                if (term.charAt(0) !== '-' || parenthesize) {
                    term = '+' + term;
                }
                return term;
            });
            var joined = terms.join('');
            if (joined.charAt(0) === '+') {
                return joined.slice(1);
            } else {
                return joined;
            }
        },
        '-': function () {
            if (arguments.length === 1) {
                return KhanUtil.expr([
                    '*',
                    -1,
                    arguments[0]
                ]);
            } else {
                var args = [].slice.call(arguments, 0);
                var terms = $.map(args, function (term, i) {
                    var negate = KhanUtil.exprIsNegated(term);
                    var parenthesize;
                    switch (KhanUtil.exprType(term)) {
                    case '+':
                    case '-':
                        parenthesize = true;
                        break;
                    default:
                        parenthesize = false;
                    }
                    term = KhanUtil.expr(term);
                    if (negate && i > 0 || parenthesize) {
                        term = '(' + term + ')';
                    }
                    return term;
                });
                var joined = terms.join('-');
                return joined;
            }
        },
        '*': function () {
            var rest = Array.prototype.slice.call(arguments, 1);
            rest.unshift('*');
            if (arguments[0] === 0) {
                return 0;
            } else if (arguments[0] === 1 && rest.length > 1) {
                return KhanUtil.expr(rest);
            } else if (arguments[0] === -1 && rest.length > 1) {
                var form = KhanUtil.expr(rest);
                if (KhanUtil.exprIsNegated(rest[1])) {
                    return '-(' + form + ')';
                } else {
                    return '-' + form;
                }
            }
            if (arguments.length > 1) {
                var args = [].slice.call(arguments, 0);
                var parenthesizeRest = KhanUtil.exprType(arguments[0]) === 'number' && KhanUtil.exprType(arguments[1]) === 'number';
                var factors = $.map(args, function (factor, i) {
                    var parenthesize;
                    switch (KhanUtil.exprType(factor)) {
                    case 'number':
                        if (i > 0) {
                            parenthesize = true;
                        }
                        break;
                    default:
                        parenthesize = !KhanUtil.exprIsShort(factor);
                        break;
                    }
                    parenthesizeRest = parenthesizeRest || parenthesize;
                    factor = KhanUtil.expr(factor);
                    if (parenthesizeRest) {
                        factor = '(' + factor + ')';
                    }
                    return factor;
                });
                return factors.join('');
            } else {
                return KhanUtil.expr(arguments[0]);
            }
        },
        'times': function (left, right) {
            var parenthesizeLeft = !KhanUtil.exprIsShort(left);
            var parenthesizeRight = !KhanUtil.exprIsShort(right);
            left = KhanUtil.expr(left);
            right = KhanUtil.expr(right);
            left = parenthesizeLeft ? '(' + left + ')' : left;
            right = parenthesizeRight ? '(' + right + ')' : right;
            return left + ' \\times ' + right;
        },
        'dot': function (left, right) {
            var parenthesizeLeft = !KhanUtil.exprIsShort(left);
            var parenthesizeRight = !KhanUtil.exprIsShort(right);
            left = KhanUtil.expr(left);
            right = KhanUtil.expr(right);
            left = parenthesizeLeft ? '(' + left + ')' : left;
            right = parenthesizeRight ? '(' + right + ')' : right;
            return left + ' \\cdot ' + right;
        },
        '/': function (num, den) {
            var parenthesizeNum = !KhanUtil.exprIsShort(num);
            var parenthesizeDen = !KhanUtil.exprIsShort(den);
            num = KhanUtil.expr(num);
            den = KhanUtil.expr(den);
            num = parenthesizeNum ? '(' + num + ')' : num;
            den = parenthesizeDen ? '(' + den + ')' : den;
            return num + '/' + den;
        },
        'frac': function (num, den) {
            return '\\dfrac{' + KhanUtil.expr(num) + '}{' + KhanUtil.expr(den) + '}';
        },
        '^': function (base, pow) {
            if (pow === 0) {
                return '';
            } else if (pow === 1) {
                return KhanUtil.expr(base);
            }
            var parenthesizeBase, trigFunction;
            switch (KhanUtil.exprType(base)) {
            case '+':
            case '-':
            case '*':
            case '/':
            case '^':
            case 'ln':
                parenthesizeBase = true;
                break;
            case 'number':
                parenthesizeBase = base < 0;
                break;
            case 'sin':
            case 'cos':
            case 'tan':
            case 'csc':
            case 'sec':
            case 'cot':
                parenthesizeBase = false;
                trigFunction = true;
                break;
            default:
                parenthesizeBase = false;
                trigFunction = false;
            }
            base = KhanUtil.expr(base);
            if (parenthesizeBase) {
                base = '(' + base + ')';
            }
            pow = KhanUtil.expr(pow);
            if (trigFunction) {
                return base.replace(/\\(\S+?)\{/, function (match, word) {
                    return '\\' + word + '^{' + pow + '} {';
                });
            } else {
                return base + '^{' + pow + '}';
            }
        },
        'sqrt': function (arg) {
            return '\\sqrt{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'sin': function (arg) {
            return '\\sin{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'cos': function (arg) {
            return '\\cos{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'tan': function (arg) {
            return '\\tan{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'sec': function (arg) {
            return '\\sec{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'csc': function (arg) {
            return '\\sec{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'cot': function (arg) {
            return '\\sec{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'ln': function (arg) {
            return '\\ln{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        '+-': function () {
            if (arguments.length === 1) {
                return '\\pm ' + KhanUtil.exprParenthesize(arguments[0]);
            } else {
                var args = [].slice.call(arguments, 0);
                return $.map(args, function (term, i) {
                    return KhanUtil.expr(term);
                }).join(' \\pm ');
            }
        }
    },
    computeOperators: {
        'color': function (color, arg) {
            return KhanUtil.expr(arg, true);
        },
        '+': function () {
            var args = [].slice.call(arguments, 0);
            var sum = 0;
            $.each(args, function (i, term) {
                sum += KhanUtil.expr(term, true);
            });
            return sum;
        },
        '-': function () {
            if (arguments.length === 1) {
                return -KhanUtil.expr(arguments[0], true);
            } else {
                var args = [].slice.call(arguments, 0);
                var sum = 0;
                $.each(args, function (i, term) {
                    sum += (i === 0 ? 1 : -1) * KhanUtil.expr(term, true);
                });
                return sum;
            }
        },
        '*': function () {
            var args = [].slice.call(arguments, 0);
            var prod = 1;
            $.each(args, function (i, term) {
                prod *= KhanUtil.expr(term, true);
            });
            return prod;
        },
        '/': function () {
            var args = [].slice.call(arguments, 0);
            var prod = 1;
            $.each(args, function (i, term) {
                var e = KhanUtil.expr(term, true);
                prod *= i === 0 ? e : 1 / e;
            });
            return prod;
        },
        '^': function (base, pow) {
            return Math.pow(KhanUtil.expr(base, true), KhanUtil.expr(pow, true));
        },
        'sqrt': function (arg) {
            return Math.sqrt(KhanUtil.expr(arg, true));
        },
        '+-': function () {
            return NaN;
        }
    },
    exprStripColor: function (expr) {
        if (typeof expr !== 'object') {
            return expr;
        } else if (expr[0] === 'color') {
            return KhanUtil.exprStripColor(expr[2]);
        } else {
            return $.map(expr, function (el, i) {
                return [i === 0 ? el : KhanUtil.exprStripColor(el)];
            });
        }
    },
    exprSimplifyAssociative: function (expr) {
        if (typeof expr !== 'object') {
            return expr;
        }
        var simplified = $.map(expr.slice(1), function (x) {
            return [KhanUtil.exprSimplifyAssociative(x)];
        });
        var flattenOneLevel = function (e) {
            switch (expr[0]) {
            case '+':
                if (e[0] === '+') {
                    return e.slice(1);
                }
                break;
            case '*':
                if (e[0] === '*') {
                    return e.slice(1);
                }
                break;
            }
            return [e];
        };
        var ret = $.map(simplified, flattenOneLevel);
        ret.unshift(expr[0]);
        return ret;
    }
});
KhanUtil.computeOperators['frac'] = KhanUtil.computeOperators['/'];
},{}],3:[function(require,module,exports){
require('./expressions.js');
var kmatrix = KhanUtil.kmatrix = {
    deepZipWith: function (depth, fn) {
        var arrays = [].slice.call(arguments, 2);
        var hasNullValue = _.any(arrays, function (array) {
            if (array === null) {
                return true;
            }
        });
        if (hasNullValue) {
            return null;
        }
        if (depth === 0) {
            return fn.apply(null, arrays);
        } else {
            return _.map(_.zip.apply(_, arrays), function (els) {
                return kmatrix.deepZipWith.apply(this, [
                    depth - 1,
                    fn
                ].concat(els));
            });
        }
    },
    matrixCopy: function (mat) {
        return $.extend(true, [], mat);
    },
    matrixMap: function (fn, mat) {
        return _.map(mat, function (row, i) {
            return _.map(row, function (elem, j) {
                return fn(elem, i, j);
            });
        });
    },
    maskMatrix: function (mat, excludeList) {
        var result = [];
        _.times(mat.r, function (i) {
            var row = [];
            _.times(mat.c, function (j) {
                if (KhanUtil.contains(excludeList, [
                        i + 1,
                        j + 1
                    ])) {
                    row.push(mat[i][j]);
                } else {
                    row.push('?');
                }
            });
            result.push(row);
        });
        return result;
    },
    printMatrix: function (fn) {
        var args = Array.prototype.slice.call(arguments);
        var mat = kmatrix.deepZipWith.apply(this, [2].concat(args));
        if (!mat) {
            return null;
        }
        var table = _.map(mat, function (row, i) {
            return row.join(' & ');
        }).join(' \\\\ ');
        var prefix = '\\left[\\begin{array}';
        var suffix = '\\end{array}\\right]';
        var alignment = '{';
        var cols = mat[0].length;
        _(cols).times(function () {
            alignment += 'r';
        });
        alignment += '}';
        return prefix + alignment + table + suffix;
    },
    printSimpleMatrix: function (mat, color) {
        return kmatrix.printMatrix(function (item) {
            if (color) {
                return KhanUtil.colorMarkup(item, color);
            }
            return item;
        }, mat);
    },
    printFractionMatrix: function (mat, color) {
        return kmatrix.printMatrix(function (item) {
            item = KhanUtil.decimalFraction(item, true);
            if (color) {
                return KhanUtil.colorMarkup(item, color);
            }
            return item;
        }, mat);
    },
    printSimpleMatrixDet: function (mat, color) {
        return kmatrix.printSimpleMatrix(mat, color).replace('left[', 'left|').replace('right]', 'right|');
    },
    printColoredDimMatrix: function (mat, colors, isRow) {
        var matrix = kmatrix.matrixMap(function (item, i, j) {
            var color = colors[isRow ? i : j];
            return KhanUtil.colorMarkup(item, color);
        }, mat);
        return kmatrix.printSimpleMatrix(matrix);
    },
    makeMultHintMatrix: function (a, b, rowColors, colColors) {
        var c = [];
        _.times(a.r, function () {
            c.push([]);
        });
        _.times(a.r, function (i) {
            var c1 = rowColors[i];
            _.times(b.c, function (j) {
                var c2 = colColors[j];
                var temp = '';
                _.times(a.c, function (k) {
                    if (k > 0) {
                        temp += '+';
                    }
                    var elem1 = KhanUtil.colorMarkup(a[i][k], c1);
                    var elem2 = KhanUtil.colorMarkup(b[k][j], c2);
                    temp += elem1 + '\\cdot' + elem2;
                });
                c[i][j] = temp;
            });
        });
        return kmatrix.makeMatrix(c);
    },
    makeMatrix: function (mat) {
        mat.r = mat.length;
        mat.c = mat[0].length;
        return mat;
    },
    cropMatrix: function (mat, rowIndex, colIndex) {
        var cropped = kmatrix.matrixCopy(mat);
        cropped.splice(rowIndex, 1);
        _.each(cropped, function (row) {
            row.splice(colIndex, 1);
        });
        return cropped;
    },
    matrix2x2DetHint: function (mat) {
        var operator = typeof mat[0][0] === 'string' ? ' \\times ' : ' \\cdot ';
        var termA = '(' + mat[0][0] + operator + mat[1][1] + ')';
        var termB = '(' + mat[0][1] + operator + mat[1][0] + ')';
        return termA + '-' + termB;
    },
    matrix3x3DetHint: function (mat, isIntermediate) {
        var tex = '';
        _.times(mat.c, function (j) {
            var hintMat = kmatrix.cropMatrix(mat, 0, j);
            var sign = j % 2 ? '-' : '+';
            sign = j === 0 ? '' : sign;
            var multiplier = mat[0][j];
            var term;
            if (isIntermediate) {
                term = kmatrix.printSimpleMatrixDet(hintMat);
            } else {
                term = kmatrix.matrix2x2DetHint(hintMat);
                term = KhanUtil.exprParenthesize(term);
            }
            tex += sign + multiplier + term;
        });
        return tex;
    },
    matrixMult: function (a, b) {
        a = kmatrix.makeMatrix(a);
        b = kmatrix.makeMatrix(b);
        var c = [];
        _.times(a.r, function () {
            c.push([]);
        });
        _.times(a.r, function (i) {
            _.times(b.c, function (j) {
                var temp = 0;
                _.times(a.c, function (k) {
                    temp += a[i][k] * b[k][j];
                });
                c[i][j] = temp;
            });
        });
        return kmatrix.makeMatrix(c);
    },
    matrixMinors: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        if (!mat.r || !mat.c) {
            return null;
        }
        var rr = kmatrix.matrixMap(function (input, row, elem) {
            return kmatrix.cropMatrix(mat, row, elem);
        }, mat);
        return rr;
    },
    matrixTranspose: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        var r = mat.c;
        var c = mat.r;
        if (!r || !c) {
            return null;
        }
        var matT = [];
        _.times(r, function (i) {
            var row = [];
            _.times(c, function (j) {
                row.push(mat[j][i]);
            });
            matT.push(row);
        });
        return kmatrix.makeMatrix(matT);
    },
    matrixDet: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        if (mat.r !== mat.c) {
            return null;
        }
        var a, b, c, d, e, f, g, h, k, det;
        if (mat.r === 2) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[1][0];
            d = mat[1][1];
            det = a * d - b * c;
        } else if (mat.r === 3) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[0][2];
            d = mat[1][0];
            e = mat[1][1];
            f = mat[1][2];
            g = mat[2][0];
            h = mat[2][1];
            k = mat[2][2];
            det = a * (e * k - f * h) - b * (k * d - f * g) + c * (d * h - e * g);
        }
        return det;
    },
    matrixAdj: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        var a, b, c, d, e, f, g, h, k;
        var adj;
        if (mat.r === 2) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[1][0];
            d = mat[1][1];
            adj = [
                [
                    d,
                    -b
                ],
                [
                    -c,
                    a
                ]
            ];
        } else if (mat.r === 3) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[0][2];
            d = mat[1][0];
            e = mat[1][1];
            f = mat[1][2];
            g = mat[2][0];
            h = mat[2][1];
            k = mat[2][2];
            var A = e * k - f * h;
            var B = -(d * k - f * g);
            var C = d * h - e * g;
            var D = -(b * k - c * h);
            var E = a * k - c * g;
            var F = -(a * h - b * g);
            var G = b * f - c * e;
            var H = -(a * f - c * d);
            var K = a * e - b * d;
            adj = [
                [
                    A,
                    D,
                    G
                ],
                [
                    B,
                    E,
                    H
                ],
                [
                    C,
                    F,
                    K
                ]
            ];
        }
        if (adj) {
            adj = kmatrix.makeMatrix(adj);
        }
        return adj;
    },
    matrixInverse: function (mat, precision) {
        var det = kmatrix.matrixDet(mat);
        if (!det) {
            return null;
        }
        var adj = kmatrix.matrixAdj(mat);
        if (!adj) {
            return null;
        }
        var inv = kmatrix.deepZipWith(2, function (val) {
            val = val / det;
            if (precision) {
                val = KhanUtil.roundTo(precision, val);
            }
            return val;
        }, adj);
        inv = kmatrix.makeMatrix(inv);
        return inv;
    },
    matrixPad: function (mat, rows, cols, padVal) {
        if (!mat) {
            return null;
        }
        mat = kmatrix.makeMatrix(mat);
        var matP = kmatrix.matrixCopy(mat);
        var finalCols = Math.max(cols, mat.c);
        if (padVal === undefined) {
            padVal = '';
        }
        var dcols = cols - matP.c;
        if (dcols > 0) {
            _.times(matP.r, function (i) {
                _.times(dcols, function () {
                    matP[i].push(padVal);
                });
            });
        }
        var drows = rows - matP.r;
        if (drows > 0) {
            _.times(drows, function () {
                var row = [];
                _.times(finalCols, function () {
                    row.push(padVal);
                });
                matP.push(row);
            });
        }
        return kmatrix.makeMatrix(matP);
    },
    arrayToColumn: function (arr) {
        var col = [];
        _.each(arr, function (e) {
            col.push([e]);
        });
        return kmatrix.makeMatrix(col);
    },
    columnToArray: function (col) {
        var arr = [];
        _.each(col, function (e) {
            arr.push(e[0]);
        });
        return arr;
    }
};
_.each(kmatrix, function (func, name) {
    KhanUtil[name] = func;
});
module.exports = kmatrix;
},{"./expressions.js":2}]},{},[1]);
