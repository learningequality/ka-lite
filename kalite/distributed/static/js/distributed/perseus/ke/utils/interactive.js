(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var table = '00000000 77073096 EE0E612C 990951BA 076DC419 706AF48F E963A535 ' + '9E6495A3 0EDB8832 79DCB8A4 E0D5E91E 97D2D988 09B64C2B 7EB17CBD ' + 'E7B82D07 90BF1D91 1DB71064 6AB020F2 F3B97148 84BE41DE 1ADAD47D ' + '6DDDE4EB F4D4B551 83D385C7 136C9856 646BA8C0 FD62F97A 8A65C9EC ' + '14015C4F 63066CD9 FA0F3D63 8D080DF5 3B6E20C8 4C69105E D56041E4 ' + 'A2677172 3C03E4D1 4B04D447 D20D85FD A50AB56B 35B5A8FA 42B2986C ' + 'DBBBC9D6 ACBCF940 32D86CE3 45DF5C75 DCD60DCF ABD13D59 26D930AC ' + '51DE003A C8D75180 BFD06116 21B4F4B5 56B3C423 CFBA9599 B8BDA50F ' + '2802B89E 5F058808 C60CD9B2 B10BE924 2F6F7C87 58684C11 C1611DAB ' + 'B6662D3D 76DC4190 01DB7106 98D220BC EFD5102A 71B18589 06B6B51F ' + '9FBFE4A5 E8B8D433 7807C9A2 0F00F934 9609A88E E10E9818 7F6A0DBB ' + '086D3D2D 91646C97 E6635C01 6B6B51F4 1C6C6162 856530D8 F262004E ' + '6C0695ED 1B01A57B 8208F4C1 F50FC457 65B0D9C6 12B7E950 8BBEB8EA ' + 'FCB9887C 62DD1DDF 15DA2D49 8CD37CF3 FBD44C65 4DB26158 3AB551CE ' + 'A3BC0074 D4BB30E2 4ADFA541 3DD895D7 A4D1C46D D3D6F4FB 4369E96A ' + '346ED9FC AD678846 DA60B8D0 44042D73 33031DE5 AA0A4C5F DD0D7CC9 ' + '5005713C 270241AA BE0B1010 C90C2086 5768B525 206F85B3 B966D409 ' + 'CE61E49F 5EDEF90E 29D9C998 B0D09822 C7D7A8B4 59B33D17 2EB40D81 ' + 'B7BD5C3B C0BA6CAD EDB88320 9ABFB3B6 03B6E20C 74B1D29A EAD54739 ' + '9DD277AF 04DB2615 73DC1683 E3630B12 94643B84 0D6D6A3E 7A6A5AA8 ' + 'E40ECF0B 9309FF9D 0A00AE27 7D079EB1 F00F9344 8708A3D2 1E01F268 ' + '6906C2FE F762575D 806567CB 196C3671 6E6B06E7 FED41B76 89D32BE0 ' + '10DA7A5A 67DD4ACC F9B9DF6F 8EBEEFF9 17B7BE43 60B08ED5 D6D6A3E8 ' + 'A1D1937E 38D8C2C4 4FDFF252 D1BB67F1 A6BC5767 3FB506DD 48B2364B ' + 'D80D2BDA AF0A1B4C 36034AF6 41047A60 DF60EFC3 A867DF55 316E8EEF ' + '4669BE79 CB61B38C BC66831A 256FD2A0 5268E236 CC0C7795 BB0B4703 ' + '220216B9 5505262F C5BA3BBE B2BD0B28 2BB45A92 5CB36A04 C2D7FFA7 ' + 'B5D0CF31 2CD99E8B 5BDEAE1D 9B64C2B0 EC63F226 756AA39C 026D930A ' + '9C0906A9 EB0E363F 72076785 05005713 95BF4A82 E2B87A14 7BB12BAE ' + '0CB61B38 92D28E9B E5D5BE0D 7CDCEFB7 0BDBDF21 86D3D2D4 F1D4E242 ' + '68DDB3F8 1FDA836E 81BE16CD F6B9265B 6FB077E1 18B74777 88085AE6 ' + 'FF0F6A70 66063BCA 11010B5C 8F659EFF F862AE69 616BFFD3 166CCF45 ' + 'A00AE278 D70DD2EE 4E048354 3903B3C2 A7672661 D06016F7 4969474D ' + '3E6E77DB AED16A4A D9D65ADC 40DF0B66 37D83BF0 A9BCAE53 DEBB9EC5 ' + '47B2CF7F 30B5FFE9 BDBDF21C CABAC28A 53B39330 24B4A3A6 BAD03605 ' + 'CDD70693 54DE5729 23D967BF B3667A2E C4614AB8 5D681B02 2A6F2B94 ' + 'B40BBE37 C30C8EA1 5A05DF1B 2D02EF8D';
var crc32 = function (str, crc) {
    if (crc == null) {
        crc = 0;
    }
    var n = 0;
    var x = 0;
    crc = crc ^ -1;
    for (var i = 0, iTop = str.length; i < iTop; i++) {
        n = (crc ^ str.charCodeAt(i)) & 255;
        x = '0x' + table.substr(n * 9, 8);
        crc = crc >>> 8 ^ x;
    }
    return Math.abs(crc ^ -1);
};
module.exports = crc32;
},{}],2:[function(require,module,exports){
var kpoint = require('./kpoint.js');
var kvector = require('./kvector.js');
require('./tex.js');
require('./tmpl.js');
var Graphie = KhanUtil.Graphie = function () {
};
function cartToPolar(coord, angleInRadians) {
    var r = Math.sqrt(Math.pow(coord[0], 2) + Math.pow(coord[1], 2));
    var theta = Math.atan2(coord[1], coord[0]);
    if (theta < 0) {
        theta += 2 * Math.PI;
    }
    if (!angleInRadians) {
        theta = theta * 180 / Math.PI;
    }
    return [
        r,
        theta
    ];
}
function polar(r, th) {
    if (typeof r === 'number') {
        r = [
            r,
            r
        ];
    }
    th = th * Math.PI / 180;
    return [
        r[0] * Math.cos(th),
        r[1] * Math.sin(th)
    ];
}
var intervalIDs = [];
function cleanupIntervals() {
    _.each(intervalIDs, function (intervalID) {
        window.clearInterval(intervalID);
    });
    intervalIDs.length = 0;
}
$.extend(KhanUtil, {
    unscaledSvgPath: function (points) {
        if (points[0] === true) {
            return '';
        }
        return $.map(points, function (point, i) {
            if (point === true) {
                return 'z';
            }
            return (i === 0 ? 'M' : 'L') + point[0] + ' ' + point[1];
        }).join('');
    },
    getDistance: function (point1, point2) {
        return kpoint.distanceToPoint(point1, point2);
    },
    coordDiff: function (startCoord, endCoord) {
        return _.map(endCoord, function (val, i) {
            return endCoord[i] - startCoord[i];
        });
    },
    snapCoord: function (coord, snap) {
        return _.map(coord, function (val, i) {
            return KhanUtil.roundToNearest(snap[i], val);
        });
    },
    findAngle: function (point1, point2, vertex) {
        if (vertex === undefined) {
            var x = point1[0] - point2[0];
            var y = point1[1] - point2[1];
            if (!x && !y) {
                return 0;
            }
            return (180 + Math.atan2(-y, -x) * 180 / Math.PI + 360) % 360;
        } else {
            return KhanUtil.findAngle(point1, vertex) - KhanUtil.findAngle(point2, vertex);
        }
    },
    graphs: {}
});
_.extend(Graphie.prototype, {
    cartToPolar: cartToPolar,
    polar: polar
});
var labelDirections = {
    'center': [
        -0.5,
        -0.5
    ],
    'above': [
        -0.5,
        -1
    ],
    'above right': [
        0,
        -1
    ],
    'right': [
        0,
        -0.5
    ],
    'below right': [
        0,
        0
    ],
    'below': [
        -0.5,
        0
    ],
    'below left': [
        -1,
        0
    ],
    'left': [
        -1,
        -0.5
    ],
    'above left': [
        -1,
        -1
    ]
};
KhanUtil.createGraphie = function (el) {
    var xScale = 40, yScale = 40, xRange, yRange;
    $(el).css('position', 'relative');
    var raphael = Raphael(el);
    $(el).children('div').css('position', 'absolute');
    var currentStyle = {
        'stroke-width': 2,
        'fill': 'none'
    };
    var scaleVector = function (point) {
        if (typeof point === 'number') {
            return scaleVector([
                point,
                point
            ]);
        }
        var x = point[0], y = point[1];
        return [
            x * xScale,
            y * yScale
        ];
    };
    var scalePoint = function scalePoint(point) {
        if (typeof point === 'number') {
            return scalePoint([
                point,
                point
            ]);
        }
        var x = point[0], y = point[1];
        return [
            (x - xRange[0]) * xScale,
            (yRange[1] - y) * yScale
        ];
    };
    var unscalePoint = function (point) {
        if (typeof point === 'number') {
            return unscalePoint([
                point,
                point
            ]);
        }
        var x = point[0], y = point[1];
        return [
            x / xScale + xRange[0],
            yRange[1] - y / yScale
        ];
    };
    var unscaleVector = function (point) {
        if (typeof point === 'number') {
            return unscaleVector([
                point,
                point
            ]);
        }
        return [
            point[0] / xScale,
            point[1] / yScale
        ];
    };
    var setLabelMargins = function (span, size) {
        var $span = $(span);
        var direction = $span.data('labelDirection');
        $span.css('visibility', '');
        if (typeof direction === 'number') {
            var x = Math.cos(direction);
            var y = Math.sin(direction);
            var scale = Math.min(size[0] / 2 / Math.abs(x), size[1] / 2 / Math.abs(y));
            $span.css({
                marginLeft: -size[0] / 2 + x * scale,
                marginTop: -size[1] / 2 - y * scale
            });
        } else {
            var multipliers = labelDirections[direction || 'center'];
            $span.css({
                marginLeft: Math.round(size[0] * multipliers[0]),
                marginTop: Math.round(size[1] * multipliers[1])
            });
        }
    };
    var svgPath = function (points, alreadyScaled) {
        return $.map(points, function (point, i) {
            if (point === true) {
                return 'z';
            } else {
                var scaled = alreadyScaled ? point : scalePoint(point);
                return (i === 0 ? 'M' : 'L') + KhanUtil.bound(scaled[0]) + ' ' + KhanUtil.bound(scaled[1]);
            }
        }).join('');
    };
    var svgParabolaPath = function (a, b, c) {
        var computeParabola = function (x) {
            return (a * x + b) * x + c;
        };
        if (a === 0) {
            var points = _.map(xRange, function (x) {
                return [
                    x,
                    computeParabola(x)
                ];
            });
            return svgPath(points);
        }
        var xVertex = -b / (2 * a);
        var distToEdge = Math.max(Math.abs(xVertex - xRange[0]), Math.abs(xVertex - xRange[1]));
        var xPoint = xVertex + distToEdge;
        var vertex = [
            xVertex,
            computeParabola(xVertex)
        ];
        var point = [
            xPoint,
            computeParabola(xPoint)
        ];
        var control = [
            vertex[0],
            vertex[1] - (point[1] - vertex[1])
        ];
        var dx = Math.abs(vertex[0] - point[0]);
        var left = [
            vertex[0] - dx,
            point[1]
        ];
        var right = [
            vertex[0] + dx,
            point[1]
        ];
        var points = _.map([
            left,
            control,
            right
        ], scalePoint);
        var values = _.map(_.flatten(points), KhanUtil.bound);
        return 'M' + values[0] + ',' + values[1] + ' Q' + values[2] + ',' + values[3] + ' ' + values[4] + ',' + values[5];
    };
    var svgSinusoidPath = function (a, b, c, d) {
        var quarterPeriod = Math.abs(Math.PI / (2 * b));
        var computeSine = function (x) {
            return a * Math.sin(b * x - c) + d;
        };
        var computeDerivative = function (x) {
            return a * b * Math.cos(c - b * x);
        };
        var coordsForOffset = function (initial, i) {
            var x0 = initial + quarterPeriod * i;
            var x1 = x0 + quarterPeriod;
            var xCoords = [
                x0,
                x0 * 2 / 3 + x1 * 1 / 3,
                x0 * 1 / 3 + x1 * 2 / 3,
                x1
            ];
            var yCoords = [
                computeSine(x0),
                computeSine(x0) + computeDerivative(x0) * (x1 - x0) / 3,
                computeSine(x1) - computeDerivative(x1) * (x1 - x0) / 3,
                computeSine(x1)
            ];
            return _.map(_.zip(xCoords, yCoords), scalePoint);
        };
        var extent = xRange[1] - xRange[0];
        var numQuarterPeriods = Math.ceil(extent / quarterPeriod) + 1;
        var initial = c / b;
        var distToEdge = initial - xRange[0];
        initial -= quarterPeriod * Math.ceil(distToEdge / quarterPeriod);
        var coords = coordsForOffset(initial, 0);
        var path = 'M' + coords[0][0] + ',' + coords[0][1] + ' C' + coords[1][0] + ',' + coords[1][1] + ' ' + coords[2][0] + ',' + coords[2][1] + ' ' + coords[3][0] + ',' + coords[3][1];
        for (var i = 1; i < numQuarterPeriods; i++) {
            coords = coordsForOffset(initial, i);
            path += ' C' + coords[1][0] + ',' + coords[1][1] + ' ' + coords[2][0] + ',' + coords[2][1] + ' ' + coords[3][0] + ',' + coords[3][1];
        }
        return path;
    };
    $.extend(KhanUtil, { svgPath: svgPath });
    var processAttributes = function (attrs) {
        var transformers = {
            scale: function (scale) {
                if (typeof scale === 'number') {
                    scale = [
                        scale,
                        scale
                    ];
                }
                xScale = scale[0];
                yScale = scale[1];
                raphael.setSize((xRange[1] - xRange[0]) * xScale, (yRange[1] - yRange[0]) * yScale);
            },
            clipRect: function (pair) {
                var point = pair[0], size = pair[1];
                point[1] += size[1];
                return { 'clip-rect': scalePoint(point).concat(scaleVector(size)).join(' ') };
            },
            strokeWidth: function (val) {
                return { 'stroke-width': parseFloat(val) };
            },
            rx: function (val) {
                return {
                    rx: scaleVector([
                        val,
                        0
                    ])[0]
                };
            },
            ry: function (val) {
                return {
                    ry: scaleVector([
                        0,
                        val
                    ])[1]
                };
            },
            r: function (val) {
                var scaled = scaleVector([
                    val,
                    val
                ]);
                return {
                    rx: scaled[0],
                    ry: scaled[1]
                };
            }
        };
        var processed = {};
        $.each(attrs || {}, function (key, value) {
            var transformer = transformers[key];
            if (typeof transformer === 'function') {
                $.extend(processed, transformer(value));
            } else {
                var dasherized = key.replace(/([A-Z]+)([A-Z][a-z])/g, '$1-$2').replace(/([a-z\d])([A-Z])/g, '$1-$2').toLowerCase();
                processed[dasherized] = value;
            }
        });
        return processed;
    };
    var addArrowheads = function arrows(path) {
        var type = path.constructor.prototype;
        if (type === Raphael.el) {
            if (path.type === 'path' && typeof path.arrowheadsDrawn === 'undefined') {
                var w = path.attr('stroke-width'), s = 0.6 + 0.4 * w;
                var l = path.getTotalLength();
                var set = raphael.set();
                var head = raphael.path('M-3 4 C-2.75 2.5 0 0.25 0.75 0C0 -0.25 -2.75 -2.5 -3 -4');
                var end = path.getPointAtLength(l - 0.4);
                var almostTheEnd = path.getPointAtLength(l - 0.75 * s);
                var angle = Math.atan2(end.y - almostTheEnd.y, end.x - almostTheEnd.x) * 180 / Math.PI;
                var attrs = path.attr();
                delete attrs.path;
                var subpath = path.getSubpath(0, l - 0.75 * s);
                subpath = raphael.path(subpath).attr(attrs);
                subpath.arrowheadsDrawn = true;
                path.remove();
                head.rotate(angle, 0.75, 0).scale(s, s, 0.75, 0).translate(almostTheEnd.x, almostTheEnd.y).attr(attrs).attr({
                    'stroke-linejoin': 'round',
                    'stroke-linecap': 'round'
                });
                head.arrowheadsDrawn = true;
                set.push(subpath);
                set.push(head);
                return set;
            }
        } else if (type === Raphael.st) {
            for (var i = 0, l = path.items.length; i < l; i++) {
                arrows(path.items[i]);
            }
        }
        return path;
    };
    var drawingTools = {
        circle: function (center, radius) {
            return raphael.ellipse.apply(raphael, scalePoint(center).concat(scaleVector([
                radius,
                radius
            ])));
        },
        rect: function (x, y, width, height) {
            var corner = scalePoint([
                x,
                y + height
            ]);
            var dims = scaleVector([
                width,
                height
            ]);
            return raphael.rect.apply(raphael, corner.concat(dims));
        },
        ellipse: function (center, radii) {
            return raphael.ellipse.apply(raphael, scalePoint(center).concat(scaleVector(radii)));
        },
        fixedEllipse: function (center, radii, maxScale) {
            var scaledPoint = scalePoint(center);
            var scaledRadii = scaleVector(radii);
            var padding = 2;
            var width = 2 * scaledRadii[0] * maxScale + padding;
            var height = 2 * scaledRadii[1] * maxScale + padding;
            var left = scaledPoint[0] - width / 2;
            var top = scaledPoint[1] - height / 2;
            var wrapper = document.createElement('div');
            $(wrapper).css({
                position: 'absolute',
                width: width + 'px',
                height: height + 'px',
                left: left + 'px',
                top: top + 'px'
            });
            var localRaphael = Raphael(wrapper, width, height);
            var visibleShape = localRaphael.ellipse(width / 2, height / 2, scaledRadii[0], scaledRadii[1]);
            return {
                wrapper: wrapper,
                visibleShape: visibleShape
            };
        },
        arc: function (center, radius, startAngle, endAngle, sector) {
            startAngle = (startAngle % 360 + 360) % 360;
            endAngle = (endAngle % 360 + 360) % 360;
            var cent = scalePoint(center);
            var radii = scaleVector(radius);
            var startVector = polar(radius, startAngle);
            var endVector = polar(radius, endAngle);
            var startPoint = scalePoint([
                center[0] + startVector[0],
                center[1] + startVector[1]
            ]);
            var endPoint = scalePoint([
                center[0] + endVector[0],
                center[1] + endVector[1]
            ]);
            var largeAngle = ((endAngle - startAngle) % 360 + 360) % 360 > 180;
            return raphael.path('M' + startPoint.join(' ') + 'A' + radii.join(' ') + ' 0 ' + (largeAngle ? 1 : 0) + ' 0 ' + endPoint.join(' ') + (sector ? 'L' + cent.join(' ') + 'z' : ''));
        },
        path: function (points) {
            var p = raphael.path(svgPath(points));
            p.graphiePath = points;
            return p;
        },
        fixedPath: function (points, center, createPath) {
            points = _.map(points, scalePoint);
            center = center ? scalePoint(center) : null;
            createPath = createPath || svgPath;
            var pathLeft = _.min(_.pluck(points, 0));
            var pathRight = _.max(_.pluck(points, 0));
            var pathTop = _.min(_.pluck(points, 1));
            var pathBottom = _.max(_.pluck(points, 1));
            var padding = [
                4,
                4
            ];
            var extraOffset = [
                pathLeft,
                pathTop
            ];
            points = _.map(points, function (point) {
                return kvector.add(kvector.subtract(point, extraOffset), kvector.scale(padding, 0.5));
            });
            var width = pathRight - pathLeft + padding[0];
            var height = pathBottom - pathTop + padding[1];
            var left = extraOffset[0] - padding[0] / 2;
            var top = extraOffset[1] - padding[1] / 2;
            var wrapper = document.createElement('div');
            $(wrapper).css({
                position: 'absolute',
                width: width + 'px',
                height: height + 'px',
                left: left + 'px',
                top: top + 'px',
                transformOrigin: center ? width / 2 + center[0] + 'px ' + (height / 2 + center[1]) + 'px' : null
            });
            var localRaphael = Raphael(wrapper, width, height);
            var visibleShape = localRaphael.path(createPath(points));
            return {
                wrapper: wrapper,
                visibleShape: visibleShape
            };
        },
        scaledPath: function (points) {
            var p = raphael.path(svgPath(points, true));
            p.graphiePath = points;
            return p;
        },
        line: function (start, end) {
            return this.path([
                start,
                end
            ]);
        },
        parabola: function (a, b, c) {
            return raphael.path(svgParabolaPath(a, b, c));
        },
        fixedLine: function (start, end, thickness) {
            var padding = [
                thickness,
                thickness
            ];
            start = scalePoint(start);
            end = scalePoint(end);
            var extraOffset = [
                Math.min(start[0], end[0]),
                Math.min(start[1], end[1])
            ];
            start = kvector.add(kvector.subtract(start, extraOffset), kvector.scale(padding, 0.5));
            end = kvector.add(kvector.subtract(end, extraOffset), kvector.scale(padding, 0.5));
            var left = extraOffset[0] - padding[0] / 2;
            var top = extraOffset[1] - padding[1] / 2;
            var width = Math.abs(start[0] - end[0]) + padding[0];
            var height = Math.abs(start[1] - end[1]) + padding[1];
            var wrapper = document.createElement('div');
            $(wrapper).css({
                position: 'absolute',
                width: width + 'px',
                height: height + 'px',
                left: left + 'px',
                top: top + 'px',
                transformOrigin: start[0] + 'px ' + start[1] + 'px'
            });
            var localRaphael = Raphael(wrapper, width, height);
            var path = 'M' + start[0] + ' ' + start[1] + ' ' + 'L' + end[0] + ' ' + end[1];
            var visibleShape = localRaphael.path(path);
            visibleShape.graphiePath = [
                start,
                end
            ];
            return {
                wrapper: wrapper,
                visibleShape: visibleShape
            };
        },
        sinusoid: function (a, b, c, d) {
            return raphael.path(svgSinusoidPath(a, b, c, d));
        },
        grid: function (xr, yr) {
            var step = currentStyle.step || [
                1,
                1
            ];
            var set = raphael.set();
            var x = step[0] * Math.ceil(xr[0] / step[0]);
            for (; x <= xr[1]; x += step[0]) {
                set.push(this.line([
                    x,
                    yr[0]
                ], [
                    x,
                    yr[1]
                ]));
            }
            var y = step[1] * Math.ceil(yr[0] / step[1]);
            for (; y <= yr[1]; y += step[1]) {
                set.push(this.line([
                    xr[0],
                    y
                ], [
                    xr[1],
                    y
                ]));
            }
            return set;
        },
        label: function (point, text, direction, latex) {
            latex = typeof latex === 'undefined' || latex;
            var $span = $('<span>').addClass('graphie-label');
            if (!latex) {
                $span.html(text);
            }
            var pad = currentStyle['label-distance'];
            $span.css($.extend({}, currentStyle, {
                position: 'absolute',
                padding: (pad != null ? pad : 7) + 'px'
            })).data('labelDirection', direction).appendTo(el);
            $span.setPosition = function (point) {
                var scaledPoint = scalePoint(point);
                $span.css({
                    left: scaledPoint[0],
                    top: scaledPoint[1]
                });
            };
            $span.setPosition(point);
            var span = $span[0];
            $span.processMath = function (math, force) {
                KhanUtil.processMath(span, math, force, function () {
                    var width = span.scrollWidth;
                    var height = span.scrollHeight;
                    setLabelMargins(span, [
                        width,
                        height
                    ]);
                });
            };
            if (latex) {
                $span.processMath(text, false);
            } else {
                var width = span.scrollWidth;
                var height = span.scrollHeight;
                setLabelMargins(span, [
                    width,
                    height
                ]);
            }
            return $span;
        },
        plotParametric: function (fn, range, shade, fn2) {
            fn2 = fn2 || function (t) {
                return [
                    t,
                    0
                ];
            };
            currentStyle.strokeLinejoin || (currentStyle.strokeLinejoin = 'round');
            currentStyle.strokeLinecap || (currentStyle.strokeLinecap = 'round');
            var min = range[0], max = range[1];
            var step = (max - min) / (currentStyle['plot-points'] || 800);
            if (step === 0) {
                step = 1;
            }
            var paths = raphael.set();
            var points = [];
            var lastDiff = KhanUtil.coordDiff(fn(min), fn2(min));
            var lastFlip = min;
            for (var t = min; t <= max; t += step) {
                var top = fn(t);
                var bottom = fn2(t);
                var diff = KhanUtil.coordDiff(top, bottom);
                if (diff[1] < 0 !== lastDiff[1] < 0 && Math.abs(diff[1] - lastDiff[1]) > 2 * yScale || Math.abs(diff[1]) > 10000000 || isNaN(diff[1])) {
                    if (shade) {
                        points.push(top);
                        for (var u = t - step; u >= lastFlip; u -= step) {
                            points.push(fn2(u));
                        }
                        lastFlip = t;
                    }
                    paths.push(this.path(points));
                    points = [];
                    if (shade) {
                        points.push(top);
                    }
                } else {
                    points.push(top);
                }
                lastDiff = diff;
            }
            if (shade) {
                for (var u = max - step; u >= lastFlip; u -= step) {
                    points.push(fn2(u));
                }
            }
            paths.push(this.path(points));
            return paths;
        },
        plotPolar: function (fn, range) {
            var min = range[0], max = range[1];
            currentStyle['plot-points'] || (currentStyle['plot-points'] = 2 * (max - min) * xScale);
            return this.plotParametric(function (th) {
                return polar(fn(th), th * 180 / Math.PI);
            }, range);
        },
        plot: function (fn, range, swapAxes, shade, fn2) {
            var min = range[0], max = range[1];
            currentStyle['plot-points'] || (currentStyle['plot-points'] = 2 * (max - min) * xScale);
            if (swapAxes) {
                if (fn2) {
                    throw new Error('Can\'t shade area between functions with swapped axes.');
                }
                return this.plotParametric(function (y) {
                    return [
                        fn(y),
                        y
                    ];
                }, range, shade);
            } else {
                if (fn2) {
                    if (shade) {
                        return this.plotParametric(function (x) {
                            return [
                                x,
                                fn(x)
                            ];
                        }, range, shade, function (x) {
                            return [
                                x,
                                fn2(x)
                            ];
                        });
                    } else {
                        throw new Error('fn2 should only be set when \'shade\' is True.');
                    }
                }
                return this.plotParametric(function (x) {
                    return [
                        x,
                        fn(x)
                    ];
                }, range, shade);
            }
        },
        plotPiecewise: function (fnArray, rangeArray) {
            var paths = raphael.set();
            var self = this;
            _.times(fnArray.length, function (i) {
                var fn = fnArray[i];
                var range = rangeArray[i];
                var fnPaths = self.plotParametric(function (x) {
                    return [
                        x,
                        fn(x)
                    ];
                }, range);
                _.each(fnPaths, function (fnPath) {
                    paths.push(fnPath);
                });
            });
            return paths;
        },
        plotEndpointCircles: function (endpointArray) {
            var circles = raphael.set();
            var self = this;
            _.each(endpointArray, function (coord, i) {
                circles.push(self.circle(coord, 0.15));
            });
            return circles;
        },
        plotAsymptotes: function (fn, range) {
            var min = range[0], max = range[1];
            var step = (max - min) / (currentStyle['plot-points'] || 800);
            var asymptotes = raphael.set(), lastVal = fn(min);
            for (var t = min; t <= max; t += step) {
                var funcVal = fn(t);
                if (funcVal < 0 !== lastVal < 0 && Math.abs(funcVal - lastVal) > 2 * yScale) {
                    asymptotes.push(this.line([
                        t,
                        yScale
                    ], [
                        t,
                        -yScale
                    ]));
                }
                lastVal = funcVal;
            }
            return asymptotes;
        }
    };
    var graphie = new Graphie();
    _.extend(graphie, {
        raphael: raphael,
        init: function (options) {
            var scale = options.scale || [
                40,
                40
            ];
            scale = typeof scale === 'number' ? [
                scale,
                scale
            ] : scale;
            xScale = scale[0];
            yScale = scale[1];
            if (options.range == null) {
                return Khan.error('range should be specified in graph init');
            }
            xRange = options.range[0];
            yRange = options.range[1];
            var w = (xRange[1] - xRange[0]) * xScale, h = (yRange[1] - yRange[0]) * yScale;
            raphael.setSize(w, h);
            $(el).css({
                'width': w,
                'height': h
            });
            this.range = options.range;
            this.scale = scale;
            this.dimensions = [
                w,
                h
            ];
            this.xpixels = w;
            this.ypixels = h;
            return this;
        },
        setInterval: function () {
            var intervalID = Function.prototype.apply.call(window.setInterval, window, arguments);
            intervalIDs.push(intervalID);
            return intervalID;
        },
        style: function (attrs, fn) {
            var processed = processAttributes(attrs);
            if (typeof fn === 'function') {
                var oldStyle = currentStyle;
                currentStyle = $.extend({}, currentStyle, processed);
                var result = fn.call(graphie);
                currentStyle = oldStyle;
                return result;
            } else {
                $.extend(currentStyle, processed);
            }
        },
        scalePoint: scalePoint,
        scaleVector: scaleVector,
        unscalePoint: unscalePoint,
        unscaleVector: unscaleVector,
        svgPath: svgPath,
        svgParabolaPath: svgParabolaPath,
        svgSinusoidPath: svgSinusoidPath
    });
    $.each(drawingTools, function (name) {
        graphie[name] = function () {
            var last = arguments[arguments.length - 1];
            var oldStyle = currentStyle;
            var result;
            if (typeof last === 'object' && !_.isArray(last)) {
                currentStyle = $.extend({}, currentStyle, processAttributes(last));
                var rest = [].slice.call(arguments, 0, arguments.length - 1);
                result = drawingTools[name].apply(drawingTools, rest);
            } else {
                currentStyle = $.extend({}, currentStyle);
                result = drawingTools[name].apply(drawingTools, arguments);
            }
            var type = result.constructor.prototype;
            if (type === Raphael.el || type === Raphael.st) {
                result.attr(currentStyle);
                if (currentStyle.arrows) {
                    result = addArrowheads(result);
                }
            } else if (result instanceof $) {
                result.css(currentStyle);
            }
            currentStyle = oldStyle;
            return result;
        };
    });
    graphie.graphInit = function (options) {
        options = options || {};
        $.each(options, function (prop, val) {
            if (!prop.match(/.*Opacity$/) && prop !== 'range' && typeof val === 'number') {
                options[prop] = [
                    val,
                    val
                ];
            }
            if (prop === 'range' || prop === 'gridRange') {
                if (val.constructor === Array) {
                    if (val[0].constructor !== Array) {
                        options[prop] = [
                            [
                                -val[0],
                                val[0]
                            ],
                            [
                                -val[1],
                                val[1]
                            ]
                        ];
                    }
                } else if (typeof val === 'number') {
                    options[prop] = [
                        [
                            -val,
                            val
                        ],
                        [
                            -val,
                            val
                        ]
                    ];
                }
            }
        });
        var range = options.range || [
                [
                    -10,
                    10
                ],
                [
                    -10,
                    10
                ]
            ], gridRange = options.gridRange || options.range, scale = options.scale || [
                20,
                20
            ], grid = options.grid != null ? options.grid : true, gridOpacity = options.gridOpacity || 0.1, gridStep = options.gridStep || [
                1,
                1
            ], axes = options.axes != null ? options.axes : true, axisArrows = options.axisArrows || '', axisOpacity = options.axisOpacity || 1, axisCenter = options.axisCenter || [
                Math.min(Math.max(range[0][0], 0), range[0][1]),
                Math.min(Math.max(range[1][0], 0), range[1][1])
            ], axisLabels = options.axisLabels != null ? options.axisLabels : false, ticks = options.ticks != null ? options.ticks : true, tickStep = options.tickStep || [
                2,
                2
            ], tickLen = options.tickLen || [
                5,
                5
            ], tickOpacity = options.tickOpacity || 1, labels = options.labels || options.labelStep || false, labelStep = options.labelStep || [
                1,
                1
            ], labelOpacity = options.labelOpacity || 1, unityLabels = options.unityLabels || false, labelFormat = options.labelFormat || function (a) {
                return a;
            }, xLabelFormat = options.xLabelFormat || labelFormat, yLabelFormat = options.yLabelFormat || labelFormat, smartLabelPositioning = options.smartLabelPositioning != null ? options.smartLabelPositioning : true, realRange = [
                [
                    range[0][0] - (range[0][0] > 0 ? 1 : 0),
                    range[0][1] + (range[0][1] < 0 ? 1 : 0)
                ],
                [
                    range[1][0] - (range[1][0] > 0 ? 1 : 0),
                    range[1][1] + (range[1][1] < 0 ? 1 : 0)
                ]
            ];
        if (!_.isArray(unityLabels)) {
            unityLabels = [
                unityLabels,
                unityLabels
            ];
        }
        if (smartLabelPositioning) {
            var minusIgnorer = function (lf) {
                return function (a) {
                    return (lf(a) + '').replace(/-(\d)/g, '\\llap{-}$1');
                };
            };
            xLabelFormat = minusIgnorer(xLabelFormat);
            yLabelFormat = minusIgnorer(yLabelFormat);
        }
        this.init({
            range: realRange,
            scale: scale
        });
        if (grid) {
            this.grid(gridRange[0], gridRange[1], {
                stroke: '#000000',
                opacity: gridOpacity,
                step: gridStep
            });
        }
        if (axes) {
            if (axisArrows === '<->' || axisArrows === true) {
                this.style({
                    stroke: '#000000',
                    opacity: axisOpacity,
                    strokeWidth: 2,
                    arrows: '->'
                }, function () {
                    if (range[1][0] < 0 && range[1][1] > 0) {
                        this.path([
                            axisCenter,
                            [
                                gridRange[0][0],
                                axisCenter[1]
                            ]
                        ]);
                        this.path([
                            axisCenter,
                            [
                                gridRange[0][1],
                                axisCenter[1]
                            ]
                        ]);
                    }
                    if (range[0][0] < 0 && range[0][1] > 0) {
                        this.path([
                            axisCenter,
                            [
                                axisCenter[0],
                                gridRange[1][0]
                            ]
                        ]);
                        this.path([
                            axisCenter,
                            [
                                axisCenter[0],
                                gridRange[1][1]
                            ]
                        ]);
                    }
                });
            } else if (axisArrows === '->' || axisArrows === '') {
                this.style({
                    stroke: '#000000',
                    opacity: axisOpacity,
                    strokeWidth: 2,
                    arrows: axisArrows
                }, function () {
                    this.path([
                        [
                            gridRange[0][0],
                            axisCenter[1]
                        ],
                        [
                            gridRange[0][1],
                            axisCenter[1]
                        ]
                    ]);
                    this.path([
                        [
                            axisCenter[0],
                            gridRange[1][0]
                        ],
                        [
                            axisCenter[0],
                            gridRange[1][1]
                        ]
                    ]);
                });
            }
            if (axisLabels && axisLabels.length === 2) {
                this.label([
                    gridRange[0][1],
                    axisCenter[1]
                ], axisLabels[0], 'right');
                this.label([
                    axisCenter[0],
                    gridRange[1][1]
                ], axisLabels[1], 'above');
            }
        }
        if (ticks) {
            this.style({
                stroke: '#000000',
                opacity: tickOpacity,
                strokeWidth: 1
            }, function () {
                var step = gridStep[0] * tickStep[0], len = tickLen[0] / scale[1], start = gridRange[0][0], stop = gridRange[0][1];
                if (range[1][0] < 0 && range[1][1] > 0) {
                    for (var x = step + axisCenter[0]; x <= stop; x += step) {
                        if (x < stop || !axisArrows) {
                            this.line([
                                x,
                                -len + axisCenter[1]
                            ], [
                                x,
                                len + axisCenter[1]
                            ]);
                        }
                    }
                    for (var x = -step + axisCenter[0]; x >= start; x -= step) {
                        if (x > start || !axisArrows) {
                            this.line([
                                x,
                                -len + axisCenter[1]
                            ], [
                                x,
                                len + axisCenter[1]
                            ]);
                        }
                    }
                }
                step = gridStep[1] * tickStep[1];
                len = tickLen[1] / scale[0];
                start = gridRange[1][0];
                stop = gridRange[1][1];
                if (range[0][0] < 0 && range[0][1] > 0) {
                    for (var y = step + axisCenter[1]; y <= stop; y += step) {
                        if (y < stop || !axisArrows) {
                            this.line([
                                -len + axisCenter[0],
                                y
                            ], [
                                len + axisCenter[0],
                                y
                            ]);
                        }
                    }
                    for (var y = -step + axisCenter[1]; y >= start; y -= step) {
                        if (y > start || !axisArrows) {
                            this.line([
                                -len + axisCenter[0],
                                y
                            ], [
                                len + axisCenter[0],
                                y
                            ]);
                        }
                    }
                }
            });
        }
        if (labels) {
            this.style({
                stroke: '#000000',
                opacity: labelOpacity
            }, function () {
                var step = gridStep[0] * tickStep[0] * labelStep[0], start = gridRange[0][0], stop = gridRange[0][1], xAxisPosition = axisCenter[0] < 0 ? 'above' : 'below', yAxisPosition = axisCenter[0] < 0 ? 'right' : 'left', xShowZero = axisCenter[0] === 0 && axisCenter[1] !== 0, yShowZero = axisCenter[0] !== 0 && axisCenter[1] === 0, axisOffCenter = axisCenter[0] !== 0 || axisCenter[1] !== 0, showUnityX = unityLabels[0] || axisOffCenter, showUnityY = unityLabels[1] || axisOffCenter;
                for (var x = (xShowZero ? 0 : step) + axisCenter[0]; x <= stop; x += step) {
                    if (x < stop || !axisArrows) {
                        this.label([
                            x,
                            axisCenter[1]
                        ], xLabelFormat(x), xAxisPosition);
                    }
                }
                for (var x = -step * (showUnityX ? 1 : 2) + axisCenter[0]; x >= start; x -= step) {
                    if (x > start || !axisArrows) {
                        this.label([
                            x,
                            axisCenter[1]
                        ], xLabelFormat(x), xAxisPosition);
                    }
                }
                step = gridStep[1] * tickStep[1] * labelStep[1];
                start = gridRange[1][0];
                stop = gridRange[1][1];
                for (var y = (yShowZero ? 0 : step) + axisCenter[1]; y <= stop; y += step) {
                    if (y < stop || !axisArrows) {
                        this.label([
                            axisCenter[0],
                            y
                        ], yLabelFormat(y), yAxisPosition);
                    }
                }
                for (var y = -step * (showUnityY ? 1 : 2) + axisCenter[1]; y >= start; y -= step) {
                    if (y > start || !axisArrows) {
                        this.label([
                            axisCenter[0],
                            y
                        ], yLabelFormat(y), yAxisPosition);
                    }
                }
            });
        }
    };
    return graphie;
};
$.fn.graphie = function (problem) {
    if (Khan.query.nographie != null) {
        return;
    }
    return this.find('.graphie, script[type=\'text/graphie\']').addBack().filter('.graphie, script[type=\'text/graphie\']').each(function () {
        var code = $(this).text(), graphie;
        if ($(this).data('graphie') != null) {
            return;
        }
        $(this).empty();
        if ($(this).data('update')) {
            var id = $(this).data('update');
            $(this).remove();
            var area = $('#problemarea').add(problem);
            graphie = area.find('#' + id + '.graphie').data('graphie');
        } else {
            var el = this;
            if ($(this).filter('script')[0] != null) {
                el = $('<div>').addClass('graphie').attr('id', $(this).attr('id')).insertAfter(this)[0];
                $(this).remove();
            }
            graphie = KhanUtil.createGraphie(el);
            $(el).data('graphie', graphie);
            var id = $(el).attr('id');
            if (id) {
                KhanUtil.graphs[id] = graphie;
            }
        }
        if (typeof graphie.graph === 'undefined') {
            graphie.graph = {};
        }
        code = '(function() {' + code + '\n})()';
        KhanUtil.currentGraph = graphie;
        $.tmpl.getVAR(code, graphie);
    }).end();
};
$.fn.graphieCleanup = function (problem) {
    cleanupIntervals();
};
},{"./kpoint.js":6,"./kvector.js":7,"./tex.js":9,"./tmpl.js":10}],3:[function(require,module,exports){
require('../third_party/jquery.mobile.vmouse.js');
require('./graphie.js');
var kvector = require('./kvector.js');
var kpoint = require('./kpoint.js');
var kline = require('./kline.js');
var WrappedEllipse = require('./wrapped-ellipse.js');
var WrappedLine = require('./wrapped-line.js');
var WrappedPath = require('./wrapped-path.js');
function sum(array) {
    return _.reduce(array, function (memo, arg) {
        return memo + arg;
    }, 0);
}
function clockwise(points) {
    var segments = _.zip(points, points.slice(1).concat(points.slice(0, 1)));
    var areas = _.map(segments, function (segment) {
        var p1 = segment[0], p2 = segment[1];
        return (p2[0] - p1[0]) * (p2[1] + p1[1]);
    });
    return sum(areas) > 0;
}
function addPoints() {
    var points = _.toArray(arguments);
    var zipped = _.zip.apply(_, points);
    return _.map(zipped, sum);
}
function reverseVector(vector) {
    return _.map(vector, function (coord) {
        return coord * -1;
    });
}
function scaledDistanceFromAngle(angle) {
    var a = 3.51470560176242 * 20;
    var b = 0.5687298702748785 * 20;
    var c = -0.037587715462826674;
    return (a - b) * Math.exp(c * angle) + b;
}
function scaledPolarRad(radius, radians) {
    return [
        radius * Math.cos(radians),
        radius * Math.sin(radians) * -1
    ];
}
function scaledPolarDeg(radius, degrees) {
    var radians = degrees * Math.PI / 180;
    return scaledPolarRad(radius, radians);
}
$.extend(KhanUtil, {
    FILL_OPACITY: 0.3,
    dragging: false,
    createSorter: function () {
        var sorter = {};
        var list;
        sorter.hasAttempted = false;
        sorter.init = function (element) {
            list = $('[id=' + element + ']').last();
            var container = list.wrap('<div>').parent();
            var placeholder = $('<li>');
            placeholder.addClass('placeholder');
            container.addClass('sortable ui-helper-clearfix');
            list.find('li').each(function (tileNum, tile) {
                $(tile).bind('vmousedown', function (event) {
                    if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                        event.preventDefault();
                        $(tile).addClass('dragging');
                        var tileIndex = $(this).index();
                        placeholder.insertAfter(tile);
                        placeholder.width($(tile).width());
                        $(this).css('z-index', 100);
                        var offset = $(this).offset();
                        var click = {
                            left: event.pageX - offset.left - 3,
                            top: event.pageY - offset.top - 3
                        };
                        $(tile).css({ position: 'absolute' });
                        $(tile).offset({
                            left: offset.left,
                            top: offset.top
                        });
                        $(document).bind('vmousemove.tile vmouseup.tile', function (event) {
                            event.preventDefault();
                            if (event.type === 'vmousemove') {
                                sorter.hasAttempted = true;
                                $(tile).offset({
                                    left: event.pageX - click.left,
                                    top: event.pageY - click.top
                                });
                                var leftEdge = list.offset().left;
                                var midWidth = $(tile).offset().left - leftEdge;
                                var index = 0;
                                var sumWidth = 0;
                                list.find('li').each(function () {
                                    if (this === placeholder[0] || this === tile) {
                                        return;
                                    }
                                    if (midWidth > sumWidth + $(this).outerWidth(true) / 2) {
                                        index += 1;
                                    }
                                    sumWidth += $(this).outerWidth(true);
                                });
                                if (index !== tileIndex) {
                                    tileIndex = index;
                                    if (index === 0) {
                                        placeholder.prependTo(list);
                                        $(tile).prependTo(list);
                                    } else {
                                        placeholder.detach();
                                        $(tile).detach();
                                        var preceeding = list.find('li')[index - 1];
                                        placeholder.insertAfter(preceeding);
                                        $(tile).insertAfter(preceeding);
                                    }
                                }
                            } else if (event.type === 'vmouseup') {
                                $(document).unbind('.tile');
                                var position = $(tile).offset();
                                $(position).animate(placeholder.offset(), {
                                    duration: 150,
                                    step: function (now, fx) {
                                        position[fx.prop] = now;
                                        $(tile).offset(position);
                                    },
                                    complete: function () {
                                        $(tile).css('z-index', 0);
                                        placeholder.detach();
                                        $(tile).css({ position: 'static' });
                                        $(tile).removeClass('dragging');
                                    }
                                });
                            }
                        });
                    }
                });
            });
        };
        sorter.getContent = function () {
            var content = [];
            list.find('li').each(function (tileNum, tile) {
                content.push($.trim($(tile).find('.sort-key').text()));
            });
            return content;
        };
        sorter.setContent = function (content) {
            var tiles = [];
            $.each(content, function (n, sortKey) {
                var tile = list.find('li .sort-key').filter(function () {
                    return $(this).text() === sortKey;
                }).closest('li').get(0);
                $(tile).detach();
                tiles.push(tile);
            });
            list.append(tiles);
        };
        return sorter;
    },
    bogusShape: {
        animate: function () {
        },
        attr: function () {
        },
        remove: function () {
        }
    }
});
$.extend(KhanUtil.Graphie.prototype, {
    initAutoscaledGraph: function (range, options) {
        var graph = this;
        options = $.extend({
            xpixels: 500,
            ypixels: 500,
            xdivisions: 20,
            ydivisions: 20,
            labels: true,
            unityLabels: true,
            range: range === undefined ? [
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
    addMouseLayer: function (options) {
        var graph = this;
        options = _.extend({ allowScratchpad: false }, options);
        var mouselayerZIndex = 2;
        graph.mouselayer = Raphael(graph.raphael.canvas.parentNode, graph.xpixels, graph.ypixels);
        $(graph.mouselayer.canvas).css('z-index', mouselayerZIndex);
        if (options.onClick || options.onMouseDown || options.onMouseMove || options.onMouseOver || options.onMouseOut) {
            var canvasClickTarget = graph.mouselayer.rect(0, 0, graph.xpixels, graph.ypixels).attr({
                fill: '#000',
                opacity: 0
            });
            var isClickingCanvas = false;
            $(graph.mouselayer.canvas).on('vmousedown', function (e) {
                if (e.target === canvasClickTarget[0]) {
                    if (options.onMouseDown) {
                        options.onMouseDown(graph.getMouseCoord(e));
                    }
                    isClickingCanvas = true;
                    if (options.onMouseMove) {
                        $(document).bind('vmousemove.mouseLayer', function (e) {
                            if (isClickingCanvas) {
                                e.preventDefault();
                                options.onMouseMove(graph.getMouseCoord(e));
                            }
                        });
                    }
                    $(document).bind('vmouseup.mouseLayer', function (e) {
                        $(document).unbind('.mouseLayer');
                        if (isClickingCanvas && options.onClick) {
                            options.onClick(graph.getMouseCoord(e));
                        }
                        isClickingCanvas = false;
                    });
                }
            });
            if (options.onMouseOver) {
                $(graph.mouselayer.canvas).on('vmouseover', function (e) {
                    options.onMouseOver(graph.getMouseCoord(e));
                });
            }
            if (options.onMouseOut) {
                $(graph.mouselayer.canvas).on('vmouseout', function (e) {
                    options.onMouseOut(graph.getMouseCoord(e));
                });
            }
        }
        if (!options.allowScratchpad) {
            Khan.scratchpad.disable();
        }
        graph._mouselayerWrapper = document.createElement('div');
        $(graph._mouselayerWrapper).css({
            position: 'absolute',
            left: 0,
            top: 0,
            zIndex: mouselayerZIndex
        });
        graph._visiblelayerWrapper = document.createElement('div');
        $(graph._visiblelayerWrapper).css({
            position: 'absolute',
            left: 0,
            top: 0
        });
        var el = graph.raphael.canvas.parentNode;
        el.appendChild(graph._visiblelayerWrapper);
        el.appendChild(graph._mouselayerWrapper);
        graph.addToMouseLayerWrapper = function (el) {
            this._mouselayerWrapper.appendChild(el);
        };
        graph.addToVisibleLayerWrapper = function (el) {
            this._visiblelayerWrapper.appendChild(el);
        };
    },
    getMousePx: function (event) {
        var graphie = this;
        var mouseX = event.pageX - $(graphie.raphael.canvas.parentNode).offset().left;
        var mouseY = event.pageY - $(graphie.raphael.canvas.parentNode).offset().top;
        return [
            mouseX,
            mouseY
        ];
    },
    getMouseCoord: function (event) {
        return this.unscalePoint(this.getMousePx(event));
    },
    drawArcs: function (point1, vertex, point3, numArcs) {
        var startAngle = KhanUtil.findAngle(point1, vertex);
        var endAngle = KhanUtil.findAngle(point3, vertex);
        if (((endAngle - startAngle) % 360 + 360) % 360 > 180) {
            var temp = startAngle;
            startAngle = endAngle;
            endAngle = temp;
        }
        var radius = 0.3;
        if (((endAngle - startAngle) % 360 + 360) % 360 < 75) {
            radius = -0.6 / 90 * (((endAngle - startAngle) % 360 + 360) % 360) + 0.8;
        }
        var arcset = [];
        for (var arc = 0; arc < numArcs; ++arc) {
            arcset.push(this.arc(vertex, radius + 0.15 * arc, startAngle, endAngle));
        }
        return arcset;
    },
    labelAngle: function (options) {
        var graphie = this;
        _.defaults(options, {
            point1: [
                0,
                0
            ],
            vertex: [
                0,
                0
            ],
            point3: [
                0,
                0
            ],
            label: null,
            numArcs: 1,
            showRightAngleMarker: true,
            pushOut: 0,
            clockwise: false,
            style: {}
        });
        var text = options.text === undefined ? '' : options.text;
        var vertex = options.vertex;
        var sVertex = graphie.scalePoint(vertex);
        var p1, p3;
        if (options.clockwise) {
            p1 = options.point1;
            p3 = options.point3;
        } else {
            p1 = options.point3;
            p3 = options.point1;
        }
        var startAngle = KhanUtil.findAngle(p1, vertex);
        var endAngle = KhanUtil.findAngle(p3, vertex);
        var angle = (endAngle + 360 - startAngle) % 360;
        var halfAngle = (startAngle + angle / 2) % 360;
        var sPadding = 5 * options.pushOut;
        var sRadius = sPadding + scaledDistanceFromAngle(angle);
        var temp = [];
        if (Math.abs(angle - 90) < 1e-9 && options.showRightAngleMarker) {
            var v1 = addPoints(sVertex, scaledPolarDeg(sRadius, startAngle));
            var v2 = addPoints(sVertex, scaledPolarDeg(sRadius, endAngle));
            sRadius *= Math.SQRT2;
            var v3 = addPoints(sVertex, scaledPolarDeg(sRadius, halfAngle));
            _.each([
                v1,
                v2
            ], function (v) {
                temp.push(graphie.scaledPath([
                    v,
                    v3
                ], options.style));
            });
        } else {
            _.times(options.numArcs, function (i) {
                temp.push(graphie.arc(vertex, graphie.unscaleVector(sRadius), startAngle, endAngle, options.style));
                sRadius += 3;
            });
        }
        if (text) {
            var match = text.match(/\$deg(\d)?/);
            if (match) {
                var precision = match[1] || 1;
                text = text.replace(match[0], KhanUtil.toFixedApprox(angle, precision) + '^{\\circ}');
            }
            var sOffset = scaledPolarDeg(sRadius + 15, halfAngle);
            var sPosition = addPoints(sVertex, sOffset);
            var position = graphie.unscalePoint(sPosition);
            if (options.label) {
                options.label.setPosition(position);
                options.label.processMath(text, true);
            } else {
                graphie.label(position, text, 'center', options.style);
            }
        }
        return temp;
    },
    labelSide: function (options) {
        var graphie = this;
        _.defaults(options, {
            point1: [
                0,
                0
            ],
            point2: [
                0,
                0
            ],
            label: null,
            text: '',
            numTicks: 0,
            numArrows: 0,
            clockwise: false,
            style: {}
        });
        var p1, p2;
        if (options.clockwise) {
            p1 = options.point1;
            p2 = options.point2;
        } else {
            p1 = options.point2;
            p2 = options.point1;
        }
        var midpoint = [
            (p1[0] + p2[0]) / 2,
            (p1[1] + p2[1]) / 2
        ];
        var sMidpoint = graphie.scalePoint(midpoint);
        var parallelAngle = Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);
        var perpendicularAngle = parallelAngle + Math.PI / 2;
        var temp = [];
        var sCumulativeOffset = 0;
        if (options.numTicks) {
            var n = options.numTicks;
            var sSpacing = 5;
            var sHeight = 5;
            var style = _.extend({}, options.style, { strokeWidth: 2 });
            _.times(n, function (i) {
                var sOffset = sSpacing * (i - (n - 1) / 2);
                var sOffsetVector = scaledPolarRad(sOffset, parallelAngle);
                var sHeightVector = scaledPolarRad(sHeight, perpendicularAngle);
                var sPath = [
                    addPoints(sMidpoint, sOffsetVector, sHeightVector),
                    addPoints(sMidpoint, sOffsetVector, reverseVector(sHeightVector))
                ];
                temp.push(graphie.scaledPath(sPath, style));
            });
            sCumulativeOffset += sSpacing * (n - 1) + 15;
        }
        if (options.numArrows) {
            var n = options.numArrows;
            var start = [
                p1,
                p2
            ].sort(function (a, b) {
                if (a[1] === b[1]) {
                    return a[0] - b[0];
                } else {
                    return a[1] - b[1];
                }
            })[0];
            var sStart = graphie.scalePoint(start);
            var style = _.extend({}, options.style, {
                arrows: '->',
                strokeWidth: 2
            });
            var sSpacing = 5;
            _.times(n, function (i) {
                var sOffset = sCumulativeOffset + sSpacing * i;
                var sOffsetVector = scaledPolarRad(sOffset, parallelAngle);
                if (start !== p1) {
                    sOffsetVector = reverseVector(sOffsetVector);
                }
                var sEnd = addPoints(sMidpoint, sOffsetVector);
                temp.push(graphie.scaledPath([
                    sStart,
                    sEnd
                ], style));
            });
        }
        var text = options.text;
        if (text) {
            var match = text.match(/\$len(\d)?/);
            if (match) {
                var distance = KhanUtil.getDistance(p1, p2);
                var precision = match[1] || 1;
                text = text.replace(match[0], KhanUtil.toFixedApprox(distance, precision));
            }
            var sOffset = 20;
            var sOffsetVector = scaledPolarRad(sOffset, perpendicularAngle);
            var sPosition = addPoints(sMidpoint, sOffsetVector);
            var position = graphie.unscalePoint(sPosition);
            if (options.label) {
                options.label.setPosition(position);
                options.label.processMath(text, true);
            } else {
                graphie.label(position, text, 'center', options.style);
            }
        }
        return temp;
    },
    labelVertex: function (options) {
        var graphie = this;
        _.defaults(options, {
            point1: null,
            vertex: [
                0,
                0
            ],
            point3: null,
            label: null,
            text: '',
            clockwise: false,
            style: {}
        });
        if (!options.text) {
            return;
        }
        var vertex = options.vertex;
        var sVertex = graphie.scalePoint(vertex);
        var p1, p3;
        if (options.clockwise) {
            p1 = options.point1;
            p3 = options.point3;
        } else {
            p1 = options.point3;
            p3 = options.point1;
        }
        var angle = 135;
        var halfAngle;
        if (p1 && p3) {
            var startAngle = KhanUtil.findAngle(p1, vertex);
            var endAngle = KhanUtil.findAngle(p3, vertex);
            angle = (endAngle + 360 - startAngle) % 360;
            halfAngle = (startAngle + angle / 2 + 180) % 360;
        } else if (p1) {
            var parallelAngle = KhanUtil.findAngle(vertex, p1);
            halfAngle = parallelAngle + 90;
        } else if (p3) {
            var parallelAngle = KhanUtil.findAngle(p3, vertex);
            halfAngle = parallelAngle + 90;
        } else {
            halfAngle = 135;
        }
        var sRadius = 10 + scaledDistanceFromAngle(360 - angle);
        var sOffsetVector = scaledPolarDeg(sRadius, halfAngle);
        var sPosition = addPoints(sVertex, sOffsetVector);
        var position = graphie.unscalePoint(sPosition);
        if (options.label) {
            options.label.setPosition(position);
            options.label.processMath(options.text, true);
        } else {
            graphie.label(position, options.text, 'center', options.style);
        }
    },
    addMovablePoint: function (options) {
        var movablePoint = $.extend(true, {
            graph: this,
            coord: [
                0,
                0
            ],
            snapX: 0,
            snapY: 0,
            pointSize: 4,
            highlight: false,
            dragging: false,
            visible: true,
            bounded: true,
            constraints: {
                fixed: false,
                constrainX: false,
                constrainY: false,
                fixedAngle: {},
                fixedDistance: {}
            },
            lineStarts: [],
            lineEnds: [],
            polygonVertices: [],
            normalStyle: {},
            highlightStyle: {
                fill: KhanUtil.INTERACTING,
                stroke: KhanUtil.INTERACTING
            },
            labelStyle: { color: KhanUtil.INTERACTIVE },
            vertexLabel: '',
            mouseTarget: null
        }, options);
        var normalColor = movablePoint.constraints.fixed ? KhanUtil.DYNAMIC : KhanUtil.INTERACTIVE;
        movablePoint.normalStyle = _.extend({}, {
            'fill': normalColor,
            'stroke': normalColor
        }, options.normalStyle);
        if (options.coordX !== undefined) {
            movablePoint.coord[0] = options.coordX;
        }
        if (options.coordY !== undefined) {
            movablePoint.coord[1] = options.coordY;
        }
        var graph = movablePoint.graph;
        var applySnapAndConstraints = function (coord) {
            if (movablePoint.visible && movablePoint.bounded && !movablePoint.constraints.fixed) {
                coord = graph.constrainToBounds(coord, 10);
            }
            var coordX = coord[0];
            var coordY = coord[1];
            if (movablePoint.snapX !== 0) {
                coordX = Math.round(coordX / movablePoint.snapX) * movablePoint.snapX;
            }
            if (movablePoint.snapY !== 0) {
                coordY = Math.round(coordY / movablePoint.snapY) * movablePoint.snapY;
            }
            if (movablePoint.constraints.fixedDistance.snapPoints) {
                var mouse = graph.scalePoint(coord);
                var mouseX = mouse[0];
                var mouseY = mouse[1];
                var snapRadians = 2 * Math.PI / movablePoint.constraints.fixedDistance.snapPoints;
                var radius = movablePoint.constraints.fixedDistance.dist;
                var centerCoord = movablePoint.constraints.fixedDistance.point;
                var centerX = (centerCoord[0] - graph.range[0][0]) * graph.scale[0];
                var centerY = (-centerCoord[1] + graph.range[1][1]) * graph.scale[1];
                var mouseXrel = mouseX - centerX;
                var mouseYrel = -mouseY + centerY;
                var radians = Math.atan(mouseYrel / mouseXrel);
                var outsideArcTanRange = mouseXrel < 0;
                if (outsideArcTanRange) {
                    radians += Math.PI;
                }
                radians = Math.round(radians / snapRadians) * snapRadians;
                mouseXrel = radius * Math.cos(radians);
                mouseYrel = radius * Math.sin(radians);
                mouseX = mouseXrel + centerX;
                mouseY = -mouseYrel + centerY;
                coordX = KhanUtil.roundTo(5, mouseX / graph.scale[0] + graph.range[0][0]);
                coordY = KhanUtil.roundTo(5, graph.range[1][1] - mouseY / graph.scale[1]);
            }
            var result = movablePoint.applyConstraint([
                coordX,
                coordY
            ]);
            return result;
        };
        movablePoint.applyConstraint = function (coord, extraConstraints, override) {
            var newCoord = coord.slice();
            var constraints = {};
            if (override) {
                $.extend(constraints, {
                    fixed: false,
                    constrainX: false,
                    constrainY: false,
                    fixedAngle: {},
                    fixedDistance: {}
                }, extraConstraints);
            } else {
                $.extend(constraints, this.constraints, extraConstraints);
            }
            if (constraints.constrainX) {
                newCoord = [
                    this.coord[0],
                    coord[1]
                ];
            } else if (constraints.constrainY) {
                newCoord = [
                    coord[0],
                    this.coord[1]
                ];
            } else if (typeof constraints.fixedAngle.angle === 'number' && typeof constraints.fixedDistance.dist === 'number') {
                var vertex = constraints.fixedAngle.vertex.coord || constraints.fixedAngle.vertex;
                var ref = constraints.fixedAngle.ref.coord || constraints.fixedAngle.ref;
                var distPoint = constraints.fixedDistance.point.coord || constraints.fixedDistance.point;
                var constrainedAngle = (constraints.fixedAngle.angle + KhanUtil.findAngle(ref, vertex)) * Math.PI / 180;
                var length = constraints.fixedDistance.dist;
                newCoord[0] = length * Math.cos(constrainedAngle) + distPoint[0];
                newCoord[1] = length * Math.sin(constrainedAngle) + distPoint[1];
            } else if (typeof constraints.fixedAngle.angle === 'number') {
                var vertex = constraints.fixedAngle.vertex.coord || constraints.fixedAngle.vertex;
                var ref = constraints.fixedAngle.ref.coord || constraints.fixedAngle.ref;
                var constrainedAngle = (constraints.fixedAngle.angle + KhanUtil.findAngle(ref, vertex)) * Math.PI / 180;
                var angle = KhanUtil.findAngle(coord, vertex) * Math.PI / 180;
                var distance = KhanUtil.getDistance(coord, vertex);
                var length = distance * Math.cos(constrainedAngle - angle);
                length = length < 1 ? 1 : length;
                newCoord[0] = length * Math.cos(constrainedAngle) + vertex[0];
                newCoord[1] = length * Math.sin(constrainedAngle) + vertex[1];
            } else if (typeof constraints.fixedDistance.dist === 'number') {
                var distPoint = constraints.fixedDistance.point.coord || constraints.fixedDistance.point;
                var angle = KhanUtil.findAngle(coord, distPoint);
                var length = constraints.fixedDistance.dist;
                angle = angle * Math.PI / 180;
                newCoord[0] = length * Math.cos(angle) + distPoint[0];
                newCoord[1] = length * Math.sin(angle) + distPoint[1];
            } else if (constraints.fixed) {
                newCoord = movablePoint.coord;
            }
            return newCoord;
        };
        movablePoint.coord = applySnapAndConstraints(movablePoint.coord);
        var highlightScale = 2;
        if (movablePoint.visible) {
            graph.style(movablePoint.normalStyle, function () {
                var radii = [
                    movablePoint.pointSize / graph.scale[0],
                    movablePoint.pointSize / graph.scale[1]
                ];
                var options = { maxScale: highlightScale };
                movablePoint.visibleShape = new WrappedEllipse(graph, movablePoint.coord, radii, options);
                movablePoint.visibleShape.attr(_.omit(movablePoint.normalStyle, 'scale'));
                movablePoint.visibleShape.toFront();
            });
        }
        movablePoint.normalStyle.scale = 1;
        movablePoint.highlightStyle.scale = highlightScale;
        if (movablePoint.vertexLabel) {
            movablePoint.labeledVertex = this.label([
                0,
                0
            ], '', 'center', movablePoint.labelStyle);
        }
        movablePoint.drawLabel = function () {
            if (movablePoint.vertexLabel) {
                movablePoint.graph.labelVertex({
                    vertex: movablePoint.coord,
                    label: movablePoint.labeledVertex,
                    text: movablePoint.vertexLabel,
                    style: movablePoint.labelStyle
                });
            }
        };
        movablePoint.drawLabel();
        movablePoint.grab = function () {
            $(document).bind('vmousemove.point vmouseup.point', function (event) {
                event.preventDefault();
                movablePoint.dragging = true;
                KhanUtil.dragging = true;
                var coord = graph.getMouseCoord(event);
                coord = applySnapAndConstraints(coord);
                var coordX = coord[0];
                var coordY = coord[1];
                var mouseX;
                var mouseY;
                if (event.type === 'vmousemove') {
                    var doMove = true;
                    if (_.isFunction(movablePoint.onMove)) {
                        var result = movablePoint.onMove(coordX, coordY);
                        if (result === false) {
                            doMove = false;
                        }
                        if (_.isArray(result)) {
                            coordX = result[0];
                            coordY = result[1];
                        }
                    }
                    mouseX = (coordX - graph.range[0][0]) * graph.scale[0];
                    mouseY = (-coordY + graph.range[1][1]) * graph.scale[1];
                    if (doMove) {
                        var point = graph.unscalePoint([
                            mouseX,
                            mouseY
                        ]);
                        movablePoint.visibleShape.moveTo(point);
                        movablePoint.mouseTarget.moveTo(point);
                        movablePoint.coord = [
                            coordX,
                            coordY
                        ];
                        movablePoint.updateLineEnds();
                        $(movablePoint).trigger('move');
                    }
                    movablePoint.drawLabel();
                } else if (event.type === 'vmouseup') {
                    $(document).unbind('.point');
                    movablePoint.dragging = false;
                    KhanUtil.dragging = false;
                    if (_.isFunction(movablePoint.onMoveEnd)) {
                        var result = movablePoint.onMoveEnd(coordX, coordY);
                        if (_.isArray(result)) {
                            coordX = result[0];
                            coordY = result[1];
                            mouseX = (coordX - graph.range[0][0]) * graph.scale[0];
                            mouseY = (-coordY + graph.range[1][1]) * graph.scale[1];
                            var point = graph.unscalePoint([
                                mouseX,
                                mouseY
                            ]);
                            movablePoint.visibleShape.moveTo(point);
                            movablePoint.mouseTarget.moveTo(point);
                            movablePoint.coord = [
                                coordX,
                                coordY
                            ];
                        }
                    }
                    if (!movablePoint.highlight) {
                        movablePoint.visibleShape.animate(movablePoint.normalStyle, 50);
                        if (movablePoint.onUnhighlight) {
                            movablePoint.onUnhighlight();
                        }
                    }
                }
            });
        };
        if (movablePoint.visible && !movablePoint.constraints.fixed) {
            if (!movablePoint.mouseTarget) {
                var radii = graph.unscaleVector(15);
                var options = { mouselayer: true };
                movablePoint.mouseTarget = new WrappedEllipse(graph, movablePoint.coord, radii, options);
                movablePoint.mouseTarget.attr({
                    fill: '#000',
                    opacity: 0
                });
            }
            var $mouseTarget = $(movablePoint.mouseTarget.getMouseTarget());
            $mouseTarget.css('cursor', 'move');
            $mouseTarget.bind('vmousedown vmouseover vmouseout', function (event) {
                if (event.type === 'vmouseover') {
                    movablePoint.highlight = true;
                    if (!KhanUtil.dragging) {
                        movablePoint.visibleShape.animate(movablePoint.highlightStyle, 50);
                        if (movablePoint.onHighlight) {
                            movablePoint.onHighlight();
                        }
                    }
                } else if (event.type === 'vmouseout') {
                    movablePoint.highlight = false;
                    if (!movablePoint.dragging && !KhanUtil.dragging) {
                        movablePoint.visibleShape.animate(movablePoint.normalStyle, 50);
                        if (movablePoint.onUnhighlight) {
                            movablePoint.onUnhighlight();
                        }
                    }
                } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                    event.preventDefault();
                    movablePoint.grab();
                }
            });
        }
        movablePoint.moveTo = function (coordX, coordY, updateLines) {
            var distance = KhanUtil.getDistance(this.graph.scalePoint([
                coordX,
                coordY
            ]), this.graph.scalePoint(this.coord));
            var time = distance * 5;
            var cb = updateLines && function (coord) {
                movablePoint.coord = coord;
                movablePoint.updateLineEnds();
            };
            this.visibleShape.animateTo([
                coordX,
                coordY
            ], time, cb);
            this.mouseTarget.animateTo([
                coordX,
                coordY
            ], time, cb);
            this.coord = [
                coordX,
                coordY
            ];
            if (_.isFunction(this.onMove)) {
                this.onMove(coordX, coordY);
            }
        };
        movablePoint.updateLineEnds = function () {
            $(this.lineStarts).each(function () {
                this.coordA = movablePoint.coord;
                this.transform();
            });
            $(this.lineEnds).each(function () {
                this.coordZ = movablePoint.coord;
                this.transform();
            });
            $(this.polygonVertices).each(function () {
                this.transform();
            });
        };
        movablePoint.setCoord = function (coord) {
            if (this.visible) {
                this.visibleShape.moveTo(coord);
                if (this.mouseTarget != null) {
                    this.mouseTarget.moveTo(coord);
                }
            }
            this.coord = coord.slice();
        };
        movablePoint.setCoordConstrained = function (coord) {
            this.setCoord(applySnapAndConstraints(coord));
        };
        movablePoint.toBack = function () {
            if (this.visible) {
                if (this.mouseTarget != null) {
                    this.mouseTarget.toBack();
                }
                this.visibleShape.toBack();
            }
        };
        movablePoint.toFront = function () {
            if (this.visible) {
                if (this.mouseTarget != null) {
                    this.mouseTarget.toFront();
                }
                this.visibleShape.toFront();
            }
        };
        movablePoint.remove = function () {
            if (this.visibleShape) {
                this.visibleShape.remove();
            }
            if (this.mouseTarget) {
                this.mouseTarget.remove();
            }
            if (this.labeledVertex) {
                this.labeledVertex.remove();
            }
        };
        return movablePoint;
    },
    addInteractiveFn: function (fn, options) {
        var graph = this;
        options = $.extend({
            graph: graph,
            snap: 0,
            range: [
                graph.range[0][0],
                graph.range[0][1]
            ]
        }, options);
        var interactiveFn = { highlight: false };
        graph.style({ stroke: KhanUtil.BLUE }, function () {
            interactiveFn.visibleShape = graph.plot(fn, options.range, options.swapAxes);
        });
        graph.style({
            fill: KhanUtil.BLUE,
            stroke: KhanUtil.BLUE
        }, function () {
            interactiveFn.cursorPoint = graph.ellipse([
                0,
                fn(0)
            ], [
                4 / graph.scale[0],
                4 / graph.scale[1]
            ]);
        });
        interactiveFn.cursorPoint.attr('opacity', 0);
        var mouseAreaWidth = 30;
        var points = [];
        var step = (options.range[1] - options.range[0]) / 100;
        var addScaledPoint = function (x, y) {
            if (options.swapAxes) {
                points.push([
                    (y - graph.range[0][0]) * graph.scale[0],
                    (graph.range[1][1] - x) * graph.scale[1]
                ]);
            } else {
                points.push([
                    (x - graph.range[0][0]) * graph.scale[0],
                    (graph.range[1][1] - y) * graph.scale[1]
                ]);
            }
        };
        for (var x = options.range[0]; x <= options.range[1]; x += step) {
            var ddx = (fn(x - 0.001) - fn(x + 0.001)) / 0.002;
            var x1 = x;
            var y1 = fn(x) + mouseAreaWidth / (2 * graph.scale[1]);
            if (ddx !== 0) {
                var normalslope = -1 / (ddx * (graph.scale[1] / graph.scale[0])) / (graph.scale[1] / graph.scale[0]);
                if (ddx < 0) {
                    x1 = x - Math.cos(-Math.atan(normalslope * (graph.scale[1] / graph.scale[0]))) * mouseAreaWidth / (2 * graph.scale[0]);
                    y1 = normalslope * (x - x1) + fn(x);
                } else if (ddx > 0) {
                    x1 = x + Math.cos(-Math.atan(normalslope * (graph.scale[1] / graph.scale[0]))) * mouseAreaWidth / (2 * graph.scale[0]);
                    y1 = normalslope * (x - x1) + fn(x);
                }
            }
            addScaledPoint(x1, y1);
        }
        for (var x = options.range[1]; x >= options.range[0]; x -= step) {
            var ddx = (fn(x - 0.001) - fn(x + 0.001)) / 0.002;
            var x1 = x;
            var y1 = fn(x) - mouseAreaWidth / (2 * graph.scale[1]);
            if (ddx !== 0) {
                var normalslope = -1 / (ddx * (graph.scale[1] / graph.scale[0])) / (graph.scale[1] / graph.scale[0]);
                if (ddx < 0) {
                    x1 = x + Math.cos(-Math.atan(normalslope * (graph.scale[1] / graph.scale[0]))) * mouseAreaWidth / (2 * graph.scale[0]);
                    y1 = normalslope * (x - x1) + fn(x);
                } else if (ddx > 0) {
                    x1 = x - Math.cos(-Math.atan(normalslope * (graph.scale[1] / graph.scale[0]))) * mouseAreaWidth / (2 * graph.scale[0]);
                    y1 = normalslope * (x - x1) + fn(x);
                }
            }
            addScaledPoint(x1, y1);
        }
        interactiveFn.mouseTarget = graph.mouselayer.path(KhanUtil.unscaledSvgPath(points));
        interactiveFn.mouseTarget.attr({
            fill: '#000',
            'opacity': 0
        });
        $(interactiveFn.mouseTarget[0]).bind('vmouseover vmouseout vmousemove', function (event) {
            event.preventDefault();
            var mouseX = event.pageX - $(graph.raphael.canvas.parentNode).offset().left;
            var mouseY = event.pageY - $(graph.raphael.canvas.parentNode).offset().top;
            mouseX = Math.max(10, Math.min(graph.xpixels - 10, mouseX));
            mouseY = Math.max(10, Math.min(graph.ypixels - 10, mouseY));
            if (options.snap) {
                mouseX = Math.round(mouseX / (graph.scale[0] * options.snap)) * (graph.scale[0] * options.snap);
            }
            var coordX = mouseX / graph.scale[0] + graph.range[0][0];
            var coordY = graph.range[1][1] - mouseY / graph.scale[1];
            var findDistance = function (coordX, coordY) {
                var closestX = 0;
                var minDist = Math.sqrt(coordX * coordX + coordY * coordY);
                for (var x = options.range[0]; x < options.range[1]; x += (options.range[1] - options.range[0]) / graph.xpixels) {
                    if (Math.sqrt((x - coordX) * (x - coordX) + (fn(x) - coordY) * (fn(x) - coordY)) < minDist) {
                        closestX = x;
                        minDist = Math.sqrt((x - coordX) * (x - coordX) + (fn(x) - coordY) * (fn(x) - coordY));
                    }
                }
                return closestX;
            };
            if (options.swapAxes) {
                var closestX = findDistance(coordY, coordX);
                coordX = fn(closestX);
                coordY = closestX;
            } else {
                var closestX = findDistance(coordX, coordY);
                coordX = closestX;
                coordY = fn(closestX);
            }
            interactiveFn.cursorPoint.attr('cx', (graph.range[0][1] + coordX) * graph.scale[0]);
            interactiveFn.cursorPoint.attr('cy', (graph.range[1][1] - coordY) * graph.scale[1]);
            if (_.isFunction(interactiveFn.onMove)) {
                interactiveFn.onMove(coordX, coordY);
            }
            if (event.type === 'vmouseover') {
                interactiveFn.cursorPoint.animate({ opacity: 1 }, 50);
                interactiveFn.highlight = true;
            } else if (event.type === 'vmouseout') {
                interactiveFn.highlight = false;
                interactiveFn.cursorPoint.animate({ opacity: 0 }, 50);
                if (_.isFunction(interactiveFn.onLeave)) {
                    interactiveFn.onLeave(coordX, coordY);
                }
            }
        });
        interactiveFn.mouseTarget.toBack();
        return interactiveFn;
    },
    addMovableLineSegment: function (options) {
        var lineSegment = $.extend({
            graph: this,
            coordA: [
                0,
                0
            ],
            coordZ: [
                1,
                1
            ],
            snapX: 0,
            snapY: 0,
            fixed: false,
            ticks: 0,
            normalStyle: {},
            highlightStyle: {
                'stroke': KhanUtil.INTERACTING,
                'stroke-width': 6
            },
            labelStyle: {
                'stroke': KhanUtil.INTERACTIVE,
                'color': KhanUtil.INTERACTIVE
            },
            highlight: false,
            dragging: false,
            tick: [],
            extendLine: false,
            extendRay: false,
            constraints: {
                fixed: false,
                constrainX: false,
                constrainY: false
            },
            sideLabel: '',
            vertexLabels: [],
            numArrows: 0,
            numTicks: 0,
            movePointsWithLine: false
        }, options);
        var normalColor = lineSegment.fixed ? KhanUtil.DYNAMIC : KhanUtil.INTERACTIVE;
        lineSegment.normalStyle = _.extend({}, {
            'stroke-width': 2,
            'stroke': normalColor
        }, options.normalStyle);
        lineSegment.arrowStyle = _.extend({}, lineSegment.normalStyle, { 'color': lineSegment.normalStyle.stroke });
        if (options.pointA !== undefined) {
            lineSegment.coordA = options.pointA.coord;
            lineSegment.pointA.lineStarts.push(lineSegment);
        } else if (options.coordA !== undefined) {
            lineSegment.coordA = options.coordA.slice();
        }
        if (options.pointZ !== undefined) {
            lineSegment.coordZ = options.pointZ.coord;
            lineSegment.pointZ.lineEnds.push(lineSegment);
        } else if (options.coordA !== undefined) {
            lineSegment.coordA = lineSegment.coordA.slice();
        }
        var graph = lineSegment.graph;
        graph.style(lineSegment.normalStyle);
        for (var i = 0; i < lineSegment.ticks; ++i) {
            lineSegment.tick[i] = KhanUtil.bogusShape;
        }
        var path = KhanUtil.unscaledSvgPath([
            [
                0,
                0
            ],
            [
                1,
                0
            ]
        ]);
        for (var i = 0; i < lineSegment.ticks; ++i) {
            var tickoffset = 0.5 - (lineSegment.ticks - 1 + i * 2) / graph.scale[0];
            path += KhanUtil.unscaledSvgPath([
                [
                    tickoffset,
                    -7
                ],
                [
                    tickoffset,
                    7
                ]
            ]);
        }
        var options = { thickness: Math.max(lineSegment.normalStyle['stroke-width'], lineSegment.highlightStyle['stroke-width']) };
        lineSegment.visibleLine = new WrappedLine(graph, [
            0,
            0
        ], [
            1,
            0
        ], options);
        lineSegment.visibleLine.attr(lineSegment.normalStyle);
        if (!lineSegment.fixed) {
            var options = {
                thickness: 30,
                mouselayer: true
            };
            lineSegment.mouseTarget = new WrappedLine(graph, [
                0,
                0
            ], [
                1,
                0
            ], options);
            lineSegment.mouseTarget.attr({
                fill: '#000',
                'opacity': 0
            });
        }
        lineSegment.transform = function (syncToPoints) {
            if (syncToPoints) {
                if (typeof this.pointA === 'object') {
                    this.coordA = this.pointA.coord;
                }
                if (typeof this.pointZ === 'object') {
                    this.coordZ = this.pointZ.coord;
                }
            }
            var getScaledAngle = function (line) {
                var scaledA = line.graph.scalePoint(line.coordA);
                var scaledZ = line.graph.scalePoint(line.coordZ);
                return kvector.polarDegFromCart(kvector.subtract(scaledZ, scaledA))[1];
            };
            var getClipPoint = function (graph, coord, angle) {
                var graph = lineSegment.graph;
                var xExtent = graph.range[0][1] - graph.range[0][0];
                var yExtent = graph.range[1][1] - graph.range[1][0];
                var distance = xExtent + yExtent;
                var angleVec = graph.unscaleVector(kvector.cartFromPolarDeg([
                    1,
                    angle
                ]));
                var distVec = kvector.scale(kvector.normalize(angleVec), distance);
                var farCoord = kvector.add(coord, distVec);
                var scaledAngle = kvector.polarDegFromCart(angleVec)[1];
                var clipPoint = graph.constrainToBoundsOnAngle(farCoord, 4, scaledAngle * Math.PI / 180);
                return clipPoint;
            };
            var angle = getScaledAngle(this);
            var start = this.coordA;
            var end = this.coordZ;
            if (this.extendLine) {
                start = getClipPoint(graph, start, 360 - angle);
                end = getClipPoint(graph, end, (540 - angle) % 360);
            } else if (this.extendRay) {
                end = getClipPoint(graph, start, 360 - angle);
            }
            var elements = [this.visibleLine];
            if (!this.fixed) {
                elements.push(this.mouseTarget);
            }
            _.each(elements, function (element) {
                element.moveTo(start, end);
            });
            var createArrow = function (graph, style) {
                var center = [
                    0.75,
                    0
                ];
                var points = [
                    [
                        -3,
                        4
                    ],
                    [
                        -2.75,
                        2.5
                    ],
                    [
                        0,
                        0.25
                    ],
                    center,
                    [
                        0,
                        -0.25
                    ],
                    [
                        -2.75,
                        -2.5
                    ],
                    [
                        -3,
                        -4
                    ]
                ];
                var scale = 1.4;
                points = _.map(points, function (point) {
                    var pv = kvector.subtract(point, center);
                    var pvScaled = kvector.scale(pv, scale);
                    return kvector.add(center, pvScaled);
                });
                var createCubicPath = function (points) {
                    var path = 'M' + points[0][0] + ' ' + points[0][1];
                    for (var i = 1; i < points.length; i += 3) {
                        path += 'C' + points[i][0] + ' ' + points[i][1] + ' ' + points[i + 1][0] + ' ' + points[i + 1][1] + ' ' + points[i + 2][0] + ' ' + points[i + 2][1];
                    }
                    return path;
                };
                var unscaledPoints = _.map(points, graph.unscalePoint);
                var options = {
                    center: graph.unscalePoint(center),
                    createPath: createCubicPath
                };
                var arrowHead = new WrappedPath(graph, unscaledPoints, options);
                arrowHead.attr(_.extend({
                    'stroke-linejoin': 'round',
                    'stroke-linecap': 'round',
                    'stroke-dasharray': ''
                }, style));
                arrowHead.toCoordAtAngle = function (coord, angle) {
                    var clipPoint = graph.scalePoint(getClipPoint(graph, coord, angle));
                    var do3dTransform = KhanUtil.getCanUse3dTransform();
                    arrowHead.transform('translateX(' + (clipPoint[0] + scale * center[0]) + 'px) ' + 'translateY(' + (clipPoint[1] + scale * center[1]) + 'px) ' + (do3dTransform ? 'translateZ(0) ' : '') + 'rotate(' + (360 - KhanUtil.bound(angle)) + 'deg)');
                };
                return arrowHead;
            };
            if (this._arrows == null) {
                this._arrows = [];
                if (this.extendLine) {
                    this._arrows.push(createArrow(graph, this.normalStyle));
                    this._arrows.push(createArrow(graph, this.normalStyle));
                } else if (this.extendRay) {
                    this._arrows.push(createArrow(graph, this.normalStyle));
                }
            }
            var coordForArrow = [
                this.coordA,
                this.coordZ
            ];
            var angleForArrow = [
                360 - angle,
                (540 - angle) % 360
            ];
            _.each(this._arrows, function (arrow, i) {
                arrow.toCoordAtAngle(coordForArrow[i], angleForArrow[i]);
            });
            _.invoke(this.temp, 'remove');
            this.temp = [];
            var isClockwise = this.coordA[0] < this.coordZ[0] || this.coordA[0] === this.coordZ[0] && this.coordA[1] > this.coordZ[1];
            if (this.sideLabel) {
                this.temp.push(this.graph.labelSide({
                    point1: this.coordA,
                    point2: this.coordZ,
                    label: this.labeledSide,
                    text: this.sideLabel,
                    numArrows: this.numArrows,
                    numTicks: this.numTicks,
                    clockwise: isClockwise,
                    style: this.labelStyle
                }));
            }
            if (this.vertexLabels.length) {
                this.graph.labelVertex({
                    vertex: this.coordA,
                    point3: this.coordZ,
                    label: this.labeledVertices[0],
                    text: this.vertexLabels[0],
                    clockwise: isClockwise,
                    style: this.labelStyle
                });
                this.graph.labelVertex({
                    point1: this.coordA,
                    vertex: this.coordZ,
                    label: this.labeledVertices[1],
                    text: this.vertexLabels[1],
                    clockwise: isClockwise,
                    style: this.labelStyle
                });
            }
            this.temp = _.flatten(this.temp);
        };
        lineSegment.toBack = function () {
            if (!lineSegment.fixed) {
                lineSegment.mouseTarget.toBack();
            }
            lineSegment.visibleLine.toBack();
        };
        lineSegment.toFront = function () {
            if (!lineSegment.fixed) {
                lineSegment.mouseTarget.toFront();
            }
            lineSegment.visibleLine.toFront();
        };
        lineSegment.remove = function () {
            if (!lineSegment.fixed) {
                lineSegment.mouseTarget.remove();
            }
            lineSegment.visibleLine.remove();
            if (lineSegment.labeledSide) {
                lineSegment.labeledSide.remove();
            }
            if (lineSegment.labeledVertices) {
                _.invoke(lineSegment.labeledVertices, 'remove');
            }
            if (lineSegment._arrows) {
                _.invoke(lineSegment._arrows, 'remove');
            }
            if (lineSegment.temp.length) {
                _.invoke(lineSegment.temp, 'remove');
            }
        };
        lineSegment.hide = function () {
            lineSegment.visibleLine.hide();
            if (lineSegment.temp.length) {
                _.invoke(lineSegment.temp, 'hide');
            }
            if (lineSegment._arrows) {
                _.invoke(lineSegment._arrows, 'hide');
            }
        };
        lineSegment.show = function () {
            lineSegment.visibleLine.show();
            if (lineSegment.temp.length) {
                _.invoke(lineSegment.temp, 'show');
            }
            if (lineSegment._arrows) {
                _.invoke(lineSegment._arrows, 'show');
            }
        };
        if (lineSegment.sideLabel) {
            lineSegment.labeledSide = this.label([
                0,
                0
            ], '', 'center', lineSegment.labelStyle);
        }
        if (lineSegment.vertexLabels.length) {
            lineSegment.labeledVertices = _.map(lineSegment.vertexLabels, function (label) {
                return this.label([
                    0,
                    0
                ], '', 'center', lineSegment.labelStyle);
            }, this);
        }
        if (!lineSegment.fixed && !lineSegment.constraints.fixed) {
            var $mouseTarget = $(lineSegment.mouseTarget.getMouseTarget());
            $mouseTarget.css('cursor', 'move');
            $mouseTarget.bind('vmousedown vmouseover vmouseout', function (event) {
                if (event.type === 'vmouseover') {
                    if (!KhanUtil.dragging) {
                        lineSegment.highlight = true;
                        lineSegment.visibleLine.animate(lineSegment.highlightStyle, 50);
                        lineSegment.arrowStyle = _.extend({}, lineSegment.arrowStyle, {
                            'color': lineSegment.highlightStyle.stroke,
                            'stroke': lineSegment.highlightStyle.stroke
                        });
                        lineSegment.transform();
                    }
                } else if (event.type === 'vmouseout') {
                    lineSegment.highlight = false;
                    if (!lineSegment.dragging) {
                        lineSegment.visibleLine.animate(lineSegment.normalStyle, 50);
                        lineSegment.arrowStyle = _.extend({}, lineSegment.arrowStyle, {
                            'color': lineSegment.normalStyle.stroke,
                            'stroke': lineSegment.normalStyle.stroke
                        });
                        lineSegment.transform();
                    }
                } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                    event.preventDefault();
                    var coordX = (event.pageX - $(graph.raphael.canvas.parentNode).offset().left) / graph.scale[0] + graph.range[0][0];
                    var coordY = graph.range[1][1] - (event.pageY - $(graph.raphael.canvas.parentNode).offset().top) / graph.scale[1];
                    if (lineSegment.snapX > 0) {
                        coordX = Math.round(coordX / lineSegment.snapX) * lineSegment.snapX;
                    }
                    if (lineSegment.snapY > 0) {
                        coordY = Math.round(coordY / lineSegment.snapY) * lineSegment.snapY;
                    }
                    var mouseOffsetA = [
                        lineSegment.coordA[0] - coordX,
                        lineSegment.coordA[1] - coordY
                    ];
                    var mouseOffsetZ = [
                        lineSegment.coordZ[0] - coordX,
                        lineSegment.coordZ[1] - coordY
                    ];
                    var offsetLeft = -Math.min(graph.scaleVector(mouseOffsetA)[0], graph.scaleVector(mouseOffsetZ)[0]);
                    var offsetRight = Math.max(graph.scaleVector(mouseOffsetA)[0], graph.scaleVector(mouseOffsetZ)[0]);
                    var offsetTop = Math.max(graph.scaleVector(mouseOffsetA)[1], graph.scaleVector(mouseOffsetZ)[1]);
                    var offsetBottom = -Math.min(graph.scaleVector(mouseOffsetA)[1], graph.scaleVector(mouseOffsetZ)[1]);
                    $(document).bind('vmousemove.lineSegment vmouseup.lineSegment', function (event) {
                        event.preventDefault();
                        lineSegment.dragging = true;
                        KhanUtil.dragging = true;
                        var mouseX = event.pageX - $(graph.raphael.canvas.parentNode).offset().left;
                        var mouseY = event.pageY - $(graph.raphael.canvas.parentNode).offset().top;
                        mouseX = Math.max(offsetLeft + 10, Math.min(graph.xpixels - 10 - offsetRight, mouseX));
                        mouseY = Math.max(offsetTop + 10, Math.min(graph.ypixels - 10 - offsetBottom, mouseY));
                        var coordX = mouseX / graph.scale[0] + graph.range[0][0];
                        var coordY = graph.range[1][1] - mouseY / graph.scale[1];
                        if (lineSegment.snapX > 0) {
                            coordX = Math.round(coordX / lineSegment.snapX) * lineSegment.snapX;
                        }
                        if (lineSegment.snapY > 0) {
                            coordY = Math.round(coordY / lineSegment.snapY) * lineSegment.snapY;
                        }
                        if (event.type === 'vmousemove') {
                            if (lineSegment.constraints.constrainX) {
                                coordX = lineSegment.coordA[0] - mouseOffsetA[0];
                            }
                            if (lineSegment.constraints.constrainY) {
                                coordY = lineSegment.coordA[1] - mouseOffsetA[1];
                            }
                            var dX = coordX + mouseOffsetA[0] - lineSegment.coordA[0];
                            var dY = coordY + mouseOffsetA[1] - lineSegment.coordA[1];
                            lineSegment.coordA = [
                                coordX + mouseOffsetA[0],
                                coordY + mouseOffsetA[1]
                            ];
                            lineSegment.coordZ = [
                                coordX + mouseOffsetZ[0],
                                coordY + mouseOffsetZ[1]
                            ];
                            lineSegment.transform();
                            if (lineSegment.movePointsWithLine) {
                                if (typeof lineSegment.pointA === 'object') {
                                    lineSegment.pointA.setCoord([
                                        lineSegment.pointA.coord[0] + dX,
                                        lineSegment.pointA.coord[1] + dY
                                    ]);
                                }
                                if (typeof lineSegment.pointZ === 'object') {
                                    lineSegment.pointZ.setCoord([
                                        lineSegment.pointZ.coord[0] + dX,
                                        lineSegment.pointZ.coord[1] + dY
                                    ]);
                                }
                            }
                            if (_.isFunction(lineSegment.onMove)) {
                                lineSegment.onMove(dX, dY);
                            }
                        } else if (event.type === 'vmouseup') {
                            $(document).unbind('.lineSegment');
                            lineSegment.dragging = false;
                            KhanUtil.dragging = false;
                            if (!lineSegment.highlight) {
                                lineSegment.visibleLine.animate(lineSegment.normalStyle, 50);
                                lineSegment.arrowStyle = _.extend({}, lineSegment.arrowStyle, {
                                    'color': lineSegment.normalStyle.stroke,
                                    'stroke': lineSegment.normalStyle.stroke
                                });
                                lineSegment.transform();
                            }
                            if (_.isFunction(lineSegment.onMoveEnd)) {
                                lineSegment.onMoveEnd();
                            }
                        }
                        $(lineSegment).trigger('move');
                    });
                }
            });
        }
        if (lineSegment.pointA !== undefined) {
            lineSegment.pointA.toFront();
        }
        if (lineSegment.pointZ !== undefined) {
            lineSegment.pointZ.toFront();
        }
        lineSegment.transform();
        return lineSegment;
    },
    addMovablePolygon: function (options) {
        var graphie = this;
        var polygon = $.extend({
            snapX: 0,
            snapY: 0,
            fixed: false,
            constrainToGraph: true,
            normalStyle: {},
            highlightStyle: {
                'stroke': KhanUtil.INTERACTING,
                'stroke-width': 2,
                'fill': KhanUtil.INTERACTING,
                'fill-opacity': 0.05
            },
            pointHighlightStyle: {
                'fill': KhanUtil.INTERACTING,
                'stroke': KhanUtil.INTERACTING
            },
            labelStyle: {
                'stroke': KhanUtil.DYNAMIC,
                'stroke-width': 1,
                'color': KhanUtil.DYNAMIC
            },
            angleLabels: [],
            showRightAngleMarkers: [],
            sideLabels: [],
            vertexLabels: [],
            numArcs: [],
            numArrows: [],
            numTicks: [],
            updateOnPointMove: true,
            closed: true
        }, _.omit(options, 'points'));
        var normalColor = polygon.fixed ? KhanUtil.DYNAMIC : KhanUtil.INTERACTIVE;
        polygon.normalStyle = _.extend({
            'stroke-width': 2,
            'fill-opacity': 0,
            'fill': normalColor,
            'stroke': normalColor
        }, options.normalStyle);
        polygon.points = options.points;
        var isPoint = function (coordOrPoint) {
            return !_.isArray(coordOrPoint);
        };
        polygon.update = function () {
            var n = polygon.points.length;
            polygon.coords = _.map(polygon.points, function (coordOrPoint, i) {
                if (isPoint(coordOrPoint)) {
                    return coordOrPoint.coord;
                } else {
                    return coordOrPoint;
                }
            });
            polygon.left = _.min(_.pluck(polygon.coords, 0));
            polygon.right = _.max(_.pluck(polygon.coords, 0));
            polygon.top = _.max(_.pluck(polygon.coords, 1));
            polygon.bottom = _.min(_.pluck(polygon.coords, 1));
            var scaledCoords = _.map(polygon.coords, function (coord) {
                return graphie.scalePoint(coord);
            });
            if (polygon.closed) {
                scaledCoords.push(true);
            } else {
                scaledCoords = scaledCoords.concat(_.clone(scaledCoords).reverse());
            }
            polygon.path = KhanUtil.unscaledSvgPath(scaledCoords);
            _.invoke(polygon.temp, 'remove');
            polygon.temp = [];
            var isClockwise = clockwise(polygon.coords);
            if (polygon.angleLabels.length || polygon.showRightAngleMarkers.length) {
                _.each(polygon.labeledAngles, function (label, i) {
                    polygon.temp.push(graphie.labelAngle({
                        point1: polygon.coords[(i - 1 + n) % n],
                        vertex: polygon.coords[i],
                        point3: polygon.coords[(i + 1) % n],
                        label: label,
                        text: polygon.angleLabels[i],
                        showRightAngleMarker: polygon.showRightAngleMarkers[i],
                        numArcs: polygon.numArcs[i],
                        clockwise: isClockwise,
                        style: polygon.labelStyle
                    }));
                });
            }
            if (polygon.sideLabels.length) {
                _.each(polygon.labeledSides, function (label, i) {
                    polygon.temp.push(graphie.labelSide({
                        point1: polygon.coords[i],
                        point2: polygon.coords[(i + 1) % n],
                        label: label,
                        text: polygon.sideLabels[i],
                        numArrows: polygon.numArrows[i],
                        numTicks: polygon.numTicks[i],
                        clockwise: isClockwise,
                        style: polygon.labelStyle
                    }));
                });
            }
            if (polygon.vertexLabels.length) {
                _.each(polygon.labeledVertices, function (label, i) {
                    graphie.labelVertex({
                        point1: polygon.coords[(i - 1 + n) % n],
                        vertex: polygon.coords[i],
                        point3: polygon.coords[(i + 1) % n],
                        label: label,
                        text: polygon.vertexLabels[i],
                        clockwise: isClockwise,
                        style: polygon.labelStyle
                    });
                });
            }
            polygon.temp = _.flatten(polygon.temp);
        };
        polygon.transform = function () {
            polygon.update();
            polygon.visibleShape.attr({ path: polygon.path });
            if (!polygon.fixed) {
                polygon.mouseTarget.attr({ path: polygon.path });
            }
        };
        polygon.remove = function () {
            polygon.visibleShape.remove();
            if (!polygon.fixed) {
                polygon.mouseTarget.remove();
            }
            if (polygon.labeledAngles) {
                _.invoke(polygon.labeledAngles, 'remove');
            }
            if (polygon.labeledSides) {
                _.invoke(polygon.labeledSides, 'remove');
            }
            if (polygon.labeledVertices) {
                _.invoke(polygon.labeledVertices, 'remove');
            }
            if (polygon.temp.length) {
                _.invoke(polygon.temp, 'remove');
            }
        };
        polygon.toBack = function () {
            if (!polygon.fixed) {
                polygon.mouseTarget.toBack();
            }
            polygon.visibleShape.toBack();
        };
        polygon.toFront = function () {
            if (!polygon.fixed) {
                polygon.mouseTarget.toFront();
            }
            polygon.visibleShape.toFront();
        };
        if (polygon.updateOnPointMove) {
            _.each(_.filter(polygon.points, isPoint), function (coordOrPoint) {
                coordOrPoint.polygonVertices.push(polygon);
            });
        }
        polygon.coords = new Array(polygon.points.length);
        if (polygon.angleLabels.length) {
            polygon.labeledAngles = _.times(Math.max(polygon.angleLabels.length, polygon.showRightAngleMarkers.length), function () {
                return this.label([
                    0,
                    0
                ], '', 'center', polygon.labelStyle);
            }, this);
        }
        if (polygon.sideLabels.length) {
            polygon.labeledSides = _.map(polygon.sideLabels, function (label) {
                return this.label([
                    0,
                    0
                ], '', 'center', polygon.labelStyle);
            }, this);
        }
        if (polygon.vertexLabels.length) {
            polygon.labeledVertices = _.map(polygon.vertexLabels, function (label) {
                return this.label([
                    0,
                    0
                ], '', 'center', polygon.labelStyle);
            }, this);
        }
        polygon.update();
        polygon.visibleShape = graphie.raphael.path(polygon.path);
        polygon.visibleShape.attr(polygon.normalStyle);
        if (!polygon.fixed) {
            polygon.mouseTarget = graphie.mouselayer.path(polygon.path);
            polygon.mouseTarget.attr({
                fill: '#000',
                opacity: 0,
                cursor: 'move'
            });
            $(polygon.mouseTarget[0]).bind('vmousedown vmouseover vmouseout', function (event) {
                if (event.type === 'vmouseover') {
                    if (!KhanUtil.dragging || polygon.dragging) {
                        polygon.highlight = true;
                        polygon.visibleShape.animate(polygon.highlightStyle, 50);
                        _.each(_.filter(polygon.points, isPoint), function (point) {
                            point.visibleShape.animate(polygon.pointHighlightStyle, 50);
                        });
                    }
                } else if (event.type === 'vmouseout') {
                    polygon.highlight = false;
                    if (!polygon.dragging) {
                        polygon.visibleShape.animate(polygon.normalStyle, 50);
                        var points = _.filter(polygon.points, isPoint);
                        if (!_.any(_.pluck(points, 'dragging'))) {
                            _.each(points, function (point) {
                                point.visibleShape.animate(point.normalStyle, 50);
                            });
                        }
                    }
                } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                    event.preventDefault();
                    _.each(_.filter(polygon.points, isPoint), function (point) {
                        point.dragging = true;
                    });
                    var startX = (event.pageX - $(graphie.raphael.canvas.parentNode).offset().left) / graphie.scale[0] + graphie.range[0][0];
                    var startY = graphie.range[1][1] - (event.pageY - $(graphie.raphael.canvas.parentNode).offset().top) / graphie.scale[1];
                    if (polygon.snapX > 0) {
                        startX = Math.round(startX / polygon.snapX) * polygon.snapX;
                    }
                    if (polygon.snapY > 0) {
                        startY = Math.round(startY / polygon.snapY) * polygon.snapY;
                    }
                    var lastX = startX;
                    var lastY = startY;
                    var polygonCoords = polygon.coords.slice();
                    var offsetLeft = (startX - polygon.left) * graphie.scale[0];
                    var offsetRight = (polygon.right - startX) * graphie.scale[0];
                    var offsetTop = (polygon.top - startY) * graphie.scale[1];
                    var offsetBottom = (startY - polygon.bottom) * graphie.scale[1];
                    $(document).bind('vmousemove.polygon vmouseup.polygon', function (event) {
                        event.preventDefault();
                        polygon.dragging = true;
                        KhanUtil.dragging = true;
                        var mouseX = event.pageX - $(graphie.raphael.canvas.parentNode).offset().left;
                        var mouseY = event.pageY - $(graphie.raphael.canvas.parentNode).offset().top;
                        if (polygon.constrainToGraph) {
                            mouseX = Math.max(offsetLeft + 10, Math.min(graphie.xpixels - 10 - offsetRight, mouseX));
                            mouseY = Math.max(offsetTop + 10, Math.min(graphie.ypixels - 10 - offsetBottom, mouseY));
                        }
                        var currentX = mouseX / graphie.scale[0] + graphie.range[0][0];
                        var currentY = graphie.range[1][1] - mouseY / graphie.scale[1];
                        if (polygon.snapX > 0) {
                            currentX = Math.round(currentX / polygon.snapX) * polygon.snapX;
                        }
                        if (polygon.snapY > 0) {
                            currentY = Math.round(currentY / polygon.snapY) * polygon.snapY;
                        }
                        if (event.type === 'vmousemove') {
                            var dX = currentX - startX;
                            var dY = currentY - startY;
                            var doMove = true;
                            if (_.isFunction(polygon.onMove)) {
                                var onMoveResult = polygon.onMove(dX, dY);
                                if (onMoveResult === false) {
                                    doMove = false;
                                } else if (_.isArray(onMoveResult)) {
                                    dX = onMoveResult[0];
                                    dY = onMoveResult[1];
                                    currentX = startX + dX;
                                    currentY = startY + dY;
                                }
                            }
                            var increment = function (i) {
                                return [
                                    polygonCoords[i][0] + dX,
                                    polygonCoords[i][1] + dY
                                ];
                            };
                            if (doMove) {
                                _.each(polygon.points, function (coordOrPoint, i) {
                                    if (isPoint(coordOrPoint)) {
                                        coordOrPoint.setCoord(increment(i));
                                    } else {
                                        polygon.points[i] = increment(i);
                                    }
                                });
                                polygon.transform();
                                $(polygon).trigger('move');
                                lastX = currentX;
                                lastY = currentY;
                            }
                        } else if (event.type === 'vmouseup') {
                            $(document).unbind('.polygon');
                            var points = _.filter(polygon.points, isPoint);
                            _.each(points, function (point) {
                                point.dragging = false;
                            });
                            polygon.dragging = false;
                            KhanUtil.dragging = false;
                            if (!polygon.highlight) {
                                polygon.visibleShape.animate(polygon.normalStyle, 50);
                                _.each(points, function (point) {
                                    point.visibleShape.animate(point.normalStyle, 50);
                                });
                            }
                            if (_.isFunction(polygon.onMoveEnd)) {
                                polygon.onMoveEnd(lastX - startX, lastY - startY);
                            }
                        }
                    });
                }
            });
        }
        _.invoke(_.filter(polygon.points, isPoint), 'toFront');
        return polygon;
    },
    constrainToBounds: function (point, padding) {
        var lower = this.unscalePoint([
            padding,
            this.ypixels - padding
        ]);
        var upper = this.unscalePoint([
            this.xpixels - padding,
            padding
        ]);
        var coordX = Math.max(lower[0], Math.min(upper[0], point[0]));
        var coordY = Math.max(lower[1], Math.min(upper[1], point[1]));
        return [
            coordX,
            coordY
        ];
    },
    constrainToBoundsOnAngle: function (point, padding, angle) {
        var lower = this.unscalePoint([
            padding,
            this.ypixels - padding
        ]);
        var upper = this.unscalePoint([
            this.xpixels - padding,
            padding
        ]);
        var result = point.slice();
        if (result[0] < lower[0]) {
            result = [
                lower[0],
                result[1] + (lower[0] - result[0]) * Math.tan(angle)
            ];
        } else if (result[0] > upper[0]) {
            result = [
                upper[0],
                result[1] - (result[0] - upper[0]) * Math.tan(angle)
            ];
        }
        if (result[1] < lower[1]) {
            result = [
                result[0] + (lower[1] - result[1]) / Math.tan(angle),
                lower[1]
            ];
        } else if (result[1] > upper[1]) {
            result = [
                result[0] - (result[1] - upper[1]) / Math.tan(angle),
                upper[1]
            ];
        }
        return result;
    },
    addMovableAngle: function (options) {
        return new MovableAngle(this, options);
    },
    addArrowWidget: function (options) {
        var arrowWidget = $.extend({
            graph: this,
            direction: 'up',
            coord: [
                0,
                0
            ],
            onClick: function () {
            }
        }, options);
        var graph = arrowWidget.graph;
        if (arrowWidget.direction === 'up') {
            arrowWidget.visibleShape = graph.path([
                [
                    arrowWidget.coord[0],
                    arrowWidget.coord[1] - 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0] - 4 / graph.scale[0],
                    arrowWidget.coord[1] - 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0],
                    arrowWidget.coord[1] + 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0] + 4 / graph.scale[0],
                    arrowWidget.coord[1] - 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0],
                    arrowWidget.coord[1] - 4 / graph.scale[1]
                ]
            ], {
                stroke: '',
                fill: KhanUtil.INTERACTIVE
            });
        } else if (arrowWidget.direction === 'down') {
            arrowWidget.visibleShape = graph.path([
                [
                    arrowWidget.coord[0],
                    arrowWidget.coord[1] + 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0] - 4 / graph.scale[0],
                    arrowWidget.coord[1] + 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0],
                    arrowWidget.coord[1] - 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0] + 4 / graph.scale[0],
                    arrowWidget.coord[1] + 4 / graph.scale[1]
                ],
                [
                    arrowWidget.coord[0],
                    arrowWidget.coord[1] + 4 / graph.scale[1]
                ]
            ], {
                stroke: '',
                fill: KhanUtil.INTERACTIVE
            });
        }
        _.defer(function () {
            arrowWidget.visibleShape.attr({
                stroke: '',
                fill: KhanUtil.INTERACTIVE
            });
        });
        arrowWidget.mouseTarget = graph.mouselayer.circle(graph.scalePoint(arrowWidget.coord)[0], graph.scalePoint(arrowWidget.coord)[1], 15);
        arrowWidget.mouseTarget.attr({
            fill: '#000',
            'opacity': 0
        });
        $(arrowWidget.mouseTarget[0]).css('cursor', 'pointer');
        $(arrowWidget.mouseTarget[0]).bind('vmousedown vmouseover vmouseout', function (event) {
            if (event.type === 'vmouseover') {
                arrowWidget.visibleShape.animate({
                    scale: 2,
                    fill: KhanUtil.INTERACTING
                }, 20);
            } else if (event.type === 'vmouseout') {
                arrowWidget.visibleShape.animate({
                    scale: 1,
                    fill: KhanUtil.INTERACTING
                }, 20);
            } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                if (!arrowWidget.hidden) {
                    arrowWidget.onClick();
                }
                return false;
            }
        });
        arrowWidget.hide = function () {
            arrowWidget.visibleShape.hide();
            arrowWidget.hidden = true;
            $(arrowWidget.mouseTarget[0]).css('cursor', 'default');
        };
        arrowWidget.show = function () {
            arrowWidget.visibleShape.show();
            arrowWidget.hidden = false;
            $(arrowWidget.mouseTarget[0]).css('cursor', 'pointer');
        };
        return arrowWidget;
    },
    addRectGraph: function (options) {
        var rect = $.extend(true, {
            x: 0,
            y: 0,
            width: 1,
            height: 1,
            normalStyle: {
                points: {
                    stroke: KhanUtil.INTERACTIVE,
                    fill: KhanUtil.INTERACTIVE,
                    opacity: 1
                },
                edges: {
                    stroke: KhanUtil.INTERACTIVE,
                    opacity: 1,
                    'stroke-width': 1
                },
                area: {
                    fill: KhanUtil.INTERACTIVE,
                    'fill-opacity': 0.1,
                    'stroke-width': 0
                }
            },
            hoverStyle: {
                points: {
                    color: KhanUtil.INTERACTING,
                    opacity: 1,
                    width: 2
                },
                edges: {
                    stroke: KhanUtil.INTERACTING,
                    opacity: 1,
                    'stroke-width': 1
                },
                area: {
                    fill: KhanUtil.INTERACTING,
                    'fill-opacity': 0.2,
                    'stroke-width': 0
                }
            },
            fixed: {
                edges: [
                    false,
                    false,
                    false,
                    false
                ],
                points: [
                    false,
                    false,
                    false,
                    false
                ]
            },
            constraints: {
                constrainX: false,
                constrainY: false,
                xmin: null,
                xmax: null,
                ymin: null,
                ymax: null
            },
            snapX: 0,
            snapY: 0,
            onMove: function () {
            }
        }, options);
        rect = $.extend({
            initialized: function () {
                return rect.points && rect.points.length;
            },
            x2: function () {
                return this.x + this.width;
            },
            y2: function () {
                return this.y + this.height;
            },
            getX: function () {
                if (rect.initialized()) {
                    return rect.points[0].coord[0];
                }
                return rect.x;
            },
            getY: function () {
                if (rect.initialized()) {
                    return rect.points[0].coord[1];
                }
                return rect.y;
            },
            getX2: function () {
                return rect.getX() + rect.getWidth();
            },
            getY2: function () {
                return rect.getY() + rect.getHeight();
            },
            getXLims: function () {
                var x = rect.getX();
                return [
                    x,
                    x + rect.getWidth()
                ];
            },
            getYLims: function () {
                var y = rect.getY();
                return [
                    y,
                    y + rect.getHeight()
                ];
            },
            getWidth: function () {
                if (rect.initialized()) {
                    var x0 = rect.points[1].coord[0];
                    var x1 = rect.points[2].coord[0];
                    return x1 - x0;
                }
                return rect.width;
            },
            getHeight: function () {
                if (rect.initialized()) {
                    var y0 = rect.points[0].coord[1];
                    var y1 = rect.points[1].coord[1];
                    return y1 - y0;
                }
                return rect.height;
            },
            getCoord: function () {
                return [
                    rect.getX(),
                    rect.getY()
                ];
            },
            getRaphaelParamsArr: function () {
                var width = rect.getWidth();
                var height = rect.getHeight();
                var x = rect.getX();
                var y = rect.getY();
                var point = graphie.scalePoint([
                    x,
                    y + height
                ]);
                var dims = graphie.scaleVector([
                    width,
                    height
                ]);
                return point.concat(dims);
            },
            getRaphaelParams: function () {
                var arr = rect.getRaphaelParamsArr();
                return {
                    x: arr[0],
                    y: arr[1],
                    width: arr[2],
                    height: arr[3]
                };
            }
        }, rect);
        var graphie = this;
        rect.fillArea = graphie.rect().attr(rect.normalStyle.area);
        rect.mouseTarget = graphie.mouselayer.rect().attr({
            fill: '#000',
            opacity: 0,
            'fill-opacity': 0
        });
        rect.render = function () {
            rect.fillArea.attr(rect.getRaphaelParams());
            rect.mouseTarget.attr(rect.getRaphaelParams());
        };
        rect.render();
        rect.points = [];
        var coords = [
            [
                rect.x,
                rect.y
            ],
            [
                rect.x,
                rect.y2()
            ],
            [
                rect.x2(),
                rect.y2()
            ],
            [
                rect.x2(),
                rect.y
            ]
        ];
        var sames = [
            [
                1,
                3
            ],
            [
                0,
                2
            ],
            [
                3,
                1
            ],
            [
                2,
                0
            ]
        ];
        var moveLimits = [
            [
                1,
                1
            ],
            [
                1,
                0
            ],
            [
                0,
                0
            ],
            [
                0,
                1
            ]
        ];
        function adjustNeighboringPoints(x, y, sameX, sameY) {
            rect.points[sameX].setCoord([
                x,
                rect.points[sameX].coord[1]
            ]);
            rect.points[sameY].setCoord([
                rect.points[sameY].coord[0],
                y
            ]);
            rect.points[sameX].updateLineEnds();
            rect.points[sameY].updateLineEnds();
        }
        function coordInBounds(limit, newVal, checkIsGreater) {
            return checkIsGreater ? newVal < limit : newVal > limit;
        }
        function moveIsInBounds(index, newX, newY) {
            var xlims = rect.getXLims();
            var ylims = rect.getYLims();
            var i = moveLimits[index];
            var xInBounds = coordInBounds(xlims[i[0]], newX, i[0] === 1);
            var yInBounds = coordInBounds(ylims[i[1]], newY, i[1] === 1);
            return xInBounds && yInBounds;
        }
        _.times(4, function (i) {
            var sameX = sames[i][0];
            var sameY = sames[i][1];
            var coord = coords[i];
            var point = graphie.addMovablePoint({
                graph: graphie,
                coord: coord,
                normalStyle: rect.normalStyle.points,
                hoverStyle: rect.hoverStyle.points,
                snapX: rect.snapX,
                snapY: rect.snapY,
                visible: !rect.fixed.points[i],
                constraints: { fixed: rect.fixed.points[i] },
                onMove: function (x, y) {
                    if (!moveIsInBounds(i, x, y)) {
                        return false;
                    }
                    adjustNeighboringPoints(x, y, sameX, sameY);
                    rect.render();
                }
            });
            rect.points.push(point);
        });
        rect.edges = [];
        rect.moveEdge = function (dx, dy, edgeIndex) {
            var a = rect.edges[edgeIndex].pointA;
            var z = rect.edges[edgeIndex].pointZ;
            a.setCoord([
                a.coord[0] + dx,
                a.coord[1] + dy
            ]);
            z.setCoord([
                z.coord[0] + dx,
                z.coord[1] + dy
            ]);
            a.updateLineEnds();
            z.updateLineEnds();
        };
        _.times(4, function (i) {
            var pointA = rect.points[i];
            var pointZ = rect.points[(i + 1) % 4];
            var constrainX = i % 2;
            var constrainY = (i + 1) % 2;
            var edge = graphie.addMovableLineSegment({
                graph: graphie,
                pointA: pointA,
                pointZ: pointZ,
                normalStyle: rect.normalStyle.edges,
                hoverStyle: rect.hoverStyle.edges,
                snapX: rect.snapX,
                snapY: rect.snapY,
                fixed: rect.fixed.edges[i],
                constraints: {
                    constrainX: constrainX,
                    constrainY: constrainY
                },
                onMove: function (dx, dy) {
                    rect.moveEdge(dx, dy, i);
                    rect.render();
                }
            });
            rect.edges.push(edge);
        });
        var elems = [
            rect.fillArea,
            rect.mouseTarget
        ];
        rect.elems = elems.concat(rect.edges).concat(rect.points);
        function constrainTranslation(dx, dy) {
            var xC = rect.constraints.constrainX;
            var xLT = rect.getX() + dx < rect.constraints.xmin;
            var xGT = rect.getX2() + dx > rect.constraints.xmax;
            var yC = rect.constraints.constrainY;
            var yLT = rect.getY() + dy < rect.constraints.ymin;
            var yGT = rect.getY2() + dy > rect.constraints.ymax;
            dx = xC || xLT || xGT ? 0 : dx;
            dy = yC || yLT || yGT ? 0 : dy;
            return [
                dx,
                dy
            ];
        }
        rect.translate = function (dx, dy) {
            if (rect.constraints.constrainX && rect.constraints.constrainY) {
                return;
            }
            var d = constrainTranslation(dx, dy);
            dx = d[0];
            dy = d[1];
            _.each(rect.points, function (point, i) {
                var x = point.coord[0] + dx;
                var y = point.coord[1] + dy;
                point.setCoord([
                    x,
                    y
                ]);
                point.updateLineEnds();
            });
            rect.render();
            rect.onMove(dx, dy);
        };
        rect.moveTo = function (x, y) {
            var dx = x - rect.getX();
            var dy = y - rect.getY();
            rect.translate(dx, dy);
        };
        rect.snap = function () {
            var dx;
            var dy;
            _.each(rect.points, function (point, i) {
                var x0 = point.coord[0];
                var y0 = point.coord[1];
                var x1 = x0;
                var y1 = y0;
                if (rect.snapX) {
                    x1 = KhanUtil.roundToNearest(rect.snapX, x0);
                }
                if (rect.snapY) {
                    y1 = KhanUtil.roundToNearest(rect.snapY, y0);
                }
                if (!dx || !dy) {
                    dx = x1 - x0;
                    dy = y1 - y0;
                }
                point.setCoord([
                    x1,
                    y1
                ]);
                point.updateLineEnds();
            });
            rect.render();
            rect.onMove(dx, dy);
        };
        rect.toFront = function () {
            _.each(rect.elems, function (elem) {
                elem.toFront();
            });
        };
        rect.hide = function (speed) {
            if (rect.hidden) {
                return;
            }
            speed = speed || 100;
            rect.fillArea.animate({ 'fill-opacity': 0 }, speed);
            $(rect.mouseTarget[0]).css('display', 'none');
            rect.hidden = true;
        };
        rect.show = function (speed) {
            if (!rect.hidden) {
                return;
            }
            speed = speed || 100;
            rect.fillArea.animate(rect.normalStyle.area, speed);
            $(rect.mouseTarget[0]).css('display', 'block');
            rect.hidden = false;
        };
        rect.enableHoverStyle = function () {
            rect.highlight = true;
            if (!KhanUtil.dragging) {
                rect.fillArea.animate(rect.hoverStyle.area, 100);
            }
        };
        rect.enableNormalStyle = function () {
            rect.highlight = false;
            if (!rect.dragging) {
                rect.fillArea.animate(rect.normalStyle.area, 100);
            }
        };
        var bindTranslation = function () {
            $(rect.mouseTarget[0]).css('cursor', 'move');
            $(rect.mouseTarget[0]).on('vmouseover vmouseout vmousedown', function (event) {
                if (event.type === 'vmouseover') {
                    rect.enableHoverStyle();
                } else if (event.type === 'vmouseout') {
                    rect.enableNormalStyle();
                } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                    event.preventDefault();
                    rect.toFront();
                    rect.prevCoord = graphie.getMouseCoord(event);
                    rect.enableHoverStyle();
                    $(document).on('vmousemove vmouseup', function (event) {
                        event.preventDefault();
                        rect.dragging = true;
                        KhanUtil.dragging = true;
                        if (event.type === 'vmousemove') {
                            var currCoord = graphie.getMouseCoord(event);
                            if (rect.prevCoord && rect.prevCoord.length === 2) {
                                var diff = KhanUtil.coordDiff(rect.prevCoord, currCoord);
                                rect.translate(diff[0], diff[1]);
                            }
                            rect.prevCoord = currCoord;
                        } else if (event.type === 'vmouseup') {
                            $(document).off('vmousemove vmouseup');
                            rect.dragging = false;
                            KhanUtil.dragging = false;
                            var currCoord = graphie.getMouseCoord(event);
                            if (currCoord[0] < rect.getX() || currCoord[0] > rect.getX2() || currCoord[1] < rect.getY() || currCoord[1] > rect.getY2()) {
                                rect.enableNormalStyle();
                            }
                            rect.snap();
                        }
                    });
                }
            });
        };
        bindTranslation();
        return rect;
    },
    addCircleGraph: function (options) {
        var graphie = this;
        var circle = $.extend({
            center: [
                0,
                0
            ],
            radius: 2,
            snapX: 0.5,
            snapY: 0.5,
            snapRadius: 0.5,
            minRadius: 1,
            centerConstraints: {},
            centerNormalStyle: {},
            centerHighlightStyle: {
                stroke: KhanUtil.INTERACTING,
                fill: KhanUtil.INTERACTING
            },
            circleNormalStyle: {
                stroke: KhanUtil.INTERACTIVE,
                'fill-opacity': 0
            },
            circleHighlightStyle: {
                stroke: KhanUtil.INTERACTING,
                fill: KhanUtil.INTERACTING,
                'fill-opacity': 0.05
            }
        }, options);
        var normalColor = circle.centerConstraints.fixed ? KhanUtil.DYNAMIC : KhanUtil.INTERACTIVE;
        var centerNormalStyle = options ? options.centerNormalStyle : null;
        circle.centerNormalStyle = _.extend({}, {
            'fill': normalColor,
            'stroke': normalColor
        }, centerNormalStyle);
        circle.centerPoint = graphie.addMovablePoint({
            graph: graphie,
            coord: circle.center,
            normalStyle: circle.centerNormalStyle,
            snapX: circle.snapX,
            snapY: circle.snapY,
            constraints: circle.centerConstraints
        });
        circle.circ = graphie.circle(circle.center, circle.radius, circle.circleNormalStyle);
        circle.perim = graphie.mouselayer.circle(graphie.scalePoint(circle.center)[0], graphie.scalePoint(circle.center)[1], graphie.scaleVector(circle.radius)[0]).attr({
            'stroke-width': 20,
            'opacity': 0.002
        });
        if (!circle.centerConstraints.fixed) {
            $(circle.centerPoint.mouseTarget.getMouseTarget()).on('vmouseover vmouseout', function (event) {
                if (circle.centerPoint.highlight || circle.centerPoint.dragging) {
                    circle.circ.animate(circle.circleHighlightStyle, 50);
                } else {
                    circle.circ.animate(circle.circleNormalStyle, 50);
                }
            });
        }
        circle.toFront = function () {
            circle.circ.toFront();
            circle.perim.toFront();
            circle.centerPoint.visibleShape.toFront();
            if (!circle.centerConstraints.fixed) {
                circle.centerPoint.mouseTarget.toFront();
            }
        };
        circle.centerPoint.onMove = function (x, y) {
            circle.toFront();
            circle.circ.attr({
                cx: graphie.scalePoint(x)[0],
                cy: graphie.scalePoint(y)[1]
            });
            circle.perim.attr({
                cx: graphie.scalePoint(x)[0],
                cy: graphie.scalePoint(y)[1]
            });
            if (circle.onMove) {
                circle.onMove(x, y);
            }
        };
        $(circle.centerPoint).on('move', function () {
            circle.center = this.coord;
            $(circle).trigger('move');
        });
        circle.setCenter = function (x, y) {
            circle.centerPoint.setCoord([
                x,
                y
            ]);
            circle.centerPoint.onMove(x, y);
            circle.center = [
                x,
                y
            ];
        };
        circle.setRadius = function (r) {
            circle.radius = r;
            circle.perim.attr({ r: graphie.scaleVector(r)[0] });
            circle.circ.attr({
                rx: graphie.scaleVector(r)[0],
                ry: graphie.scaleVector(r)[1]
            });
        };
        circle.remove = function () {
            circle.centerPoint.remove();
            circle.circ.remove();
            circle.perim.remove();
        };
        $(circle.perim[0]).css('cursor', 'move');
        $(circle.perim[0]).on('vmouseover vmouseout vmousedown', function (event) {
            if (event.type === 'vmouseover') {
                circle.highlight = true;
                if (!KhanUtil.dragging) {
                    circle.circ.animate(circle.circleHighlightStyle, 50);
                    circle.centerPoint.visibleShape.animate(circle.centerHighlightStyle, 50);
                }
            } else if (event.type === 'vmouseout') {
                circle.highlight = false;
                if (!circle.dragging && !circle.centerPoint.dragging) {
                    circle.circ.animate(circle.circleNormalStyle, 50);
                    circle.centerPoint.visibleShape.animate(circle.centerNormalStyle, 50);
                }
            } else if (event.type === 'vmousedown' && (event.which === 1 || event.which === 0)) {
                event.preventDefault();
                circle.toFront();
                var startRadius = circle.radius;
                $(document).on('vmousemove vmouseup', function (event) {
                    event.preventDefault();
                    circle.dragging = true;
                    KhanUtil.dragging = true;
                    if (event.type === 'vmousemove') {
                        var coord = graphie.constrainToBounds(graphie.getMouseCoord(event), 10);
                        var radius = KhanUtil.getDistance(circle.centerPoint.coord, coord);
                        radius = Math.max(circle.minRadius, Math.round(radius / circle.snapRadius) * circle.snapRadius);
                        var oldRadius = circle.radius;
                        var doResize = true;
                        if (circle.onResize) {
                            var onResizeResult = circle.onResize(radius, oldRadius);
                            if (_.isNumber(onResizeResult)) {
                                radius = onResizeResult;
                            } else if (onResizeResult === false) {
                                doResize = false;
                            }
                        }
                        if (doResize) {
                            circle.setRadius(radius);
                            $(circle).trigger('move');
                        }
                    } else if (event.type === 'vmouseup') {
                        $(document).off('vmousemove vmouseup');
                        circle.dragging = false;
                        KhanUtil.dragging = false;
                        if (circle.onResizeEnd) {
                            circle.onResizeEnd(circle.radius, startRadius);
                        }
                    }
                });
            }
        });
        return circle;
    },
    interactiveEllipse: function (options) {
        var graphie = this;
        var ellipse = $.extend({
            center: [
                0,
                0
            ],
            radius: 2,
            xRadius: 2,
            yRadius: 2,
            ellipseNormalStyle: {
                stroke: KhanUtil.BLUE,
                'fill-opacity': 0
            },
            ellipseBoundaryHideStyle: {
                'fill-opacity': 0,
                'stroke-width': 0
            },
            ellipseBoundaryShowStyle: {
                'fill-opacity': 1,
                fill: KhanUtil.BLUE
            },
            onMove: function (coordX, coordY) {
            },
            onLeave: function (coordX, coordY) {
            }
        }, options);
        ellipse.circ = graphie.ellipse(ellipse.center, [
            ellipse.xRadius,
            ellipse.yRadius
        ], ellipse.ellipseNormalStyle);
        ellipse.perim = graphie.mouselayer.ellipse(graphie.scalePoint(ellipse.center)[0], graphie.scalePoint(ellipse.center)[1], graphie.scaleVector(ellipse.xRadius)[0], graphie.scaleVector(ellipse.yRadius)[0]).attr({
            'stroke-width': 30,
            'opacity': 0.002
        });
        ellipse.boundaryPoint = graphie.circle(ellipse.center, 0.4, ellipse.ellipseBoundaryHideStyle);
        ellipse.remove = function () {
            ellipse.circ.remove();
            ellipse.perim.remove();
        };
        ellipse.showPoint = function (event) {
            var coord = graphie.constrainToBounds(graphie.getMouseCoord(event), 10);
            var dx = ellipse.yRadius * (ellipse.center[0] - coord[0]);
            var dy = ellipse.xRadius * (ellipse.center[1] - coord[1]);
            var angle = Math.atan2(dy, dx);
            coord[0] = ellipse.center[0] - ellipse.xRadius * Math.cos(angle);
            coord[1] = ellipse.center[1] - ellipse.yRadius * Math.sin(angle);
            var scaledPoint = graphie.scalePoint(coord);
            ellipse.boundaryPoint.attr({ cx: scaledPoint[0] });
            ellipse.boundaryPoint.attr({ cy: scaledPoint[1] });
            ellipse.boundaryPoint.animate(ellipse.ellipseBoundaryShowStyle, 50);
            ellipse.onMove(coord[0], coord[1]);
        };
        $(ellipse.perim[0]).on('vmouseover vmouseout vmousemove', function (event) {
            if (event.type === 'vmouseover') {
                ellipse.showPoint(event);
            } else if (event.type === 'vmouseout') {
                ellipse.boundaryPoint.animate(ellipse.ellipseBoundaryHideStyle, 50);
                ellipse.onLeave();
            } else if (event.type === 'vmousemove') {
                ellipse.showPoint(event);
            }
        });
        return ellipse;
    },
    addRotateHandle: function () {
        var drawRotateHandle = function (graphie, center, radius, halfWidth, lengthAngle, angle, interacting) {
            var getRotateHandlePoint = function (offset, distanceFromArrowMidline) {
                var distFromRotationCenter = radius + distanceFromArrowMidline;
                var vec = KhanUtil.kvector.cartFromPolarDeg([
                    distFromRotationCenter,
                    angle + offset
                ]);
                var absolute = KhanUtil.kvector.add(center, vec);
                var pixels = graphie.scalePoint(absolute);
                return pixels[0] + ',' + pixels[1];
            };
            var innerR = graphie.scaleVector(radius - halfWidth);
            var outerR = graphie.scaleVector(radius + halfWidth);
            return graphie.raphael.path(' M' + getRotateHandlePoint(lengthAngle, -halfWidth) + ' L' + getRotateHandlePoint(lengthAngle, -3 * halfWidth) + ' L' + getRotateHandlePoint(2 * lengthAngle, 0) + ' L' + getRotateHandlePoint(lengthAngle, 3 * halfWidth) + ' L' + getRotateHandlePoint(lengthAngle, halfWidth) + ' A' + outerR[0] + ',' + outerR[1] + ',0,0,1,' + getRotateHandlePoint(-lengthAngle, halfWidth) + ' L' + getRotateHandlePoint(-lengthAngle, 3 * halfWidth) + ' L' + getRotateHandlePoint(-2 * lengthAngle, 0) + ' L' + getRotateHandlePoint(-lengthAngle, -3 * halfWidth) + ' L' + getRotateHandlePoint(-lengthAngle, -halfWidth) + ' A' + innerR[0] + ',' + innerR[1] + ',0,0,0,' + getRotateHandlePoint(lengthAngle, -halfWidth) + ' Z').attr({
                stroke: null,
                fill: interacting ? KhanUtil.INTERACTING : KhanUtil.INTERACTIVE
            });
        };
        return function (options) {
            var graph = this;
            var rotatePoint = options.center;
            var radius = options.radius;
            var lengthAngle = options.lengthAngle || 30;
            var hideArrow = options.hideArrow || false;
            var mouseTarget = options.mouseTarget;
            var id = _.uniqueId('rotateHandle');
            if (_.isArray(rotatePoint)) {
                rotatePoint = { coord: rotatePoint };
            }
            var rotateHandle = graph.addMovablePoint({
                coord: KhanUtil.kpoint.addVector(rotatePoint.coord, KhanUtil.kvector.cartFromPolarDeg(radius, options.angleDeg || 0)),
                constraints: {
                    fixedDistance: {
                        dist: radius,
                        point: rotatePoint
                    }
                },
                mouseTarget: mouseTarget
            });
            rotatePoint.toFront();
            var rotatePointPrevCoord = rotatePoint.coord;
            var rotateHandlePrevCoord = rotateHandle.coord;
            var rotateHandleStartCoord = rotateHandlePrevCoord;
            var isRotating = false;
            var isHovering = false;
            var drawnRotateHandle;
            var redrawRotateHandle = function (handleCoord) {
                if (hideArrow) {
                    return;
                }
                var handleVec = KhanUtil.kvector.subtract(handleCoord, rotatePoint.coord);
                var handlePolar = KhanUtil.kvector.polarDegFromCart(handleVec);
                var angle = handlePolar[1];
                if (drawnRotateHandle) {
                    drawnRotateHandle.remove();
                }
                drawnRotateHandle = drawRotateHandle(graph, rotatePoint.coord, options.radius, isRotating || isHovering ? options.hoverWidth / 2 : options.width / 2, lengthAngle, angle, isRotating || isHovering);
            };
            $(rotatePoint).on('move.' + id, function () {
                var delta = KhanUtil.kvector.subtract(rotatePoint.coord, rotatePointPrevCoord);
                rotateHandle.setCoord(KhanUtil.kvector.add(rotateHandle.coord, delta));
                redrawRotateHandle(rotateHandle.coord);
                rotatePointPrevCoord = rotatePoint.coord;
                rotateHandle.constraints.fixedDistance.point = rotatePoint;
                rotateHandlePrevCoord = rotateHandle.coord;
            });
            rotateHandle.onMove = function (x, y) {
                if (!isRotating) {
                    rotateHandleStartCoord = rotateHandlePrevCoord;
                    isRotating = true;
                }
                var coord = [
                    x,
                    y
                ];
                if (options.onMove) {
                    var oldPolar = KhanUtil.kvector.polarDegFromCart(KhanUtil.kvector.subtract(rotateHandlePrevCoord, rotatePoint.coord));
                    var newPolar = KhanUtil.kvector.polarDegFromCart(KhanUtil.kvector.subtract(coord, rotatePoint.coord));
                    var oldAngle = oldPolar[1];
                    var newAngle = newPolar[1];
                    var result = options.onMove(newAngle, oldAngle);
                    if (result != null && result !== true) {
                        if (result === false) {
                            result = oldAngle;
                        }
                        coord = KhanUtil.kvector.add(rotatePoint.coord, KhanUtil.kvector.cartFromPolarDeg([
                            oldPolar[0],
                            result
                        ]));
                    }
                }
                redrawRotateHandle(coord);
                rotateHandlePrevCoord = coord;
                return coord;
            };
            rotateHandle.onMoveEnd = function () {
                isRotating = false;
                redrawRotateHandle(rotateHandle.coord);
                if (options.onMoveEnd) {
                    var oldPolar = KhanUtil.kvector.polarDegFromCart(KhanUtil.kvector.subtract(rotateHandleStartCoord, rotatePoint.coord));
                    var newPolar = KhanUtil.kvector.polarDegFromCart(KhanUtil.kvector.subtract(rotateHandle.coord, rotatePoint.coord));
                    options.onMoveEnd(newPolar[1], oldPolar[1]);
                }
            };
            rotateHandle.visibleShape.remove();
            if (!mouseTarget) {
                rotateHandle.mouseTarget.attr({ scale: 2 });
            }
            var $mouseTarget = $(rotateHandle.mouseTarget.getMouseTarget());
            $mouseTarget.bind('vmouseover', function (e) {
                isHovering = true;
                redrawRotateHandle(rotateHandle.coord);
            });
            $mouseTarget.bind('vmouseout', function (e) {
                isHovering = false;
                redrawRotateHandle(rotateHandle.coord);
            });
            redrawRotateHandle(rotateHandle.coord);
            var oldRemove = rotateHandle.remove;
            rotateHandle.remove = function () {
                oldRemove.call(rotateHandle);
                if (drawnRotateHandle) {
                    drawnRotateHandle.remove();
                }
                $(rotatePoint).off('move.' + id);
            };
            rotateHandle.update = function () {
                redrawRotateHandle(rotateHandle.coord);
            };
            return rotateHandle;
        };
    }(),
    addReflectButton: function () {
        var drawButton = function (graphie, buttonCoord, lineCoords, size, distanceFromCenter, leftStyle, rightStyle) {
            if (kpoint.equal(lineCoords[0], lineCoords[1])) {
                lineCoords = [
                    lineCoords[0],
                    kpoint.addVector(lineCoords[0], [
                        1,
                        1
                    ])
                ];
            }
            var lineDirection = kvector.normalize(kvector.subtract(lineCoords[1], lineCoords[0]));
            var lineVec = kvector.scale(lineDirection, size / 2);
            var centerVec = kvector.scale(lineDirection, distanceFromCenter);
            var leftCenterVec = kvector.rotateDeg(centerVec, 90);
            var rightCenterVec = kvector.rotateDeg(centerVec, -90);
            var negLineVec = kvector.negate(lineVec);
            var leftVec = kvector.rotateDeg(lineVec, 90);
            var rightVec = kvector.rotateDeg(lineVec, -90);
            var leftCenter = kpoint.addVectors(buttonCoord, leftCenterVec);
            var rightCenter = kpoint.addVectors(buttonCoord, rightCenterVec);
            var leftCoord1 = kpoint.addVectors(buttonCoord, leftCenterVec, lineVec, leftVec);
            var leftCoord2 = kpoint.addVectors(buttonCoord, leftCenterVec, negLineVec, leftVec);
            var rightCoord1 = kpoint.addVectors(buttonCoord, rightCenterVec, lineVec, rightVec);
            var rightCoord2 = kpoint.addVectors(buttonCoord, rightCenterVec, negLineVec, rightVec);
            var leftButton = graphie.path([
                leftCenter,
                leftCoord1,
                leftCoord2,
                true
            ], leftStyle);
            var rightButton = graphie.path([
                rightCenter,
                rightCoord1,
                rightCoord2,
                true
            ], rightStyle);
            return {
                remove: function () {
                    leftButton.remove();
                    rightButton.remove();
                }
            };
        };
        return function (options) {
            var graphie = this;
            var line = options.line;
            var button = graphie.addMovablePoint({
                constraints: options.constraints,
                coord: kline.midpoint([
                    line.pointA.coord,
                    line.pointZ.coord
                ]),
                snapX: graphie.snap[0],
                snapY: graphie.snap[1],
                onMove: function (x, y) {
                    return false;
                },
                onMoveEnd: function (x, y) {
                    if (options.onMoveEnd) {
                        options.onMoveEnd.call(this, x, y);
                    }
                }
            });
            var isHovering = false;
            var isFlipped = false;
            var currentlyDrawnButton;
            var isHighlight = function () {
                return isHovering;
            };
            var styles = _.map([
                0,
                1
            ], function (isHighlight) {
                var baseStyle = isHighlight ? options.highlightStyle : options.normalStyle;
                return _.map([
                    0,
                    1
                ], function (opacity) {
                    return _.defaults({ 'fill-opacity': opacity }, baseStyle);
                });
            });
            var getStyle = function (isRight) {
                if (isFlipped) {
                    isRight = !isRight;
                }
                return styles[+isHighlight()][+isRight];
            };
            var redraw = function (coord, lineCoords) {
                if (currentlyDrawnButton) {
                    currentlyDrawnButton.remove();
                }
                currentlyDrawnButton = drawButton(graphie, coord, lineCoords, isHighlight() ? options.size * 1.5 : options.size, isHighlight() ? options.size * 0.125 : 0.25, getStyle(0), getStyle(1));
            };
            var update = function (coordA, coordZ) {
                coordA = coordA || line.pointA.coord;
                coordZ = coordZ || line.pointZ.coord;
                var buttonCoord = kline.midpoint([
                    coordA,
                    coordZ
                ]);
                button.setCoord(buttonCoord);
                redraw(buttonCoord, [
                    coordA,
                    coordZ
                ]);
            };
            $(line).on('move', _.bind(update, button, null, null));
            var $mouseTarget = $(button.mouseTarget.getMouseTarget());
            $mouseTarget.on('vclick', function () {
                var result = options.onClick();
                if (result !== false) {
                    isFlipped = !isFlipped;
                    redraw(button.coord, [
                        line.pointA.coord,
                        line.pointZ.coord
                    ]);
                }
            });
            line.pointA.toFront();
            line.pointZ.toFront();
            button.visibleShape.remove();
            var pointScale = graphie.scaleVector(options.size)[0] / 20;
            button.mouseTarget.attr({ scale: 1.5 * pointScale });
            $mouseTarget.css('cursor', 'pointer');
            $mouseTarget.bind('vmouseover', function (e) {
                isHovering = true;
                redraw(button.coord, [
                    line.pointA.coord,
                    line.pointZ.coord
                ]);
            });
            $mouseTarget.bind('vmouseout', function (e) {
                isHovering = false;
                redraw(button.coord, [
                    line.pointA.coord,
                    line.pointZ.coord
                ]);
            });
            var oldButtonRemove = button.remove;
            button.remove = function () {
                currentlyDrawnButton.remove();
                oldButtonRemove.call(button);
            };
            button.update = update;
            button.isFlipped = function () {
                return isFlipped;
            };
            update();
            return button;
        };
    }(),
    protractor: function (center) {
        return new Protractor(this, center);
    },
    ruler: function (options) {
        return new Ruler(this, options || {});
    },
    addPoints: addPoints
});
function Protractor(graph, center) {
    this.set = graph.raphael.set();
    this.cx = center[0];
    this.cy = center[1];
    var pro = this;
    var r = graph.unscaleVector(180.5)[0];
    var imgPos = graph.scalePoint([
        this.cx - r,
        this.cy + r - graph.unscaleVector(10.5)[1]
    ]);
    this.set.push(graph.mouselayer.image('https://ka-perseus-graphie.s3.amazonaws.com/e9d032f2ab8b95979f674fbfa67056442ba1ff6a.png', imgPos[0], imgPos[1], 360, 180));
    var arrowHelper = function (angle, pixelsFromEdge) {
        var scaledRadius = graph.scaleVector(r);
        scaledRadius[0] -= 16;
        scaledRadius[1] -= 16;
        var scaledCenter = graph.scalePoint(center);
        var x = Math.sin((angle + 90) * Math.PI / 180) * (scaledRadius[0] + pixelsFromEdge) + scaledCenter[0];
        var y = Math.cos((angle + 90) * Math.PI / 180) * (scaledRadius[1] + pixelsFromEdge) + scaledCenter[1];
        return x + ',' + y;
    };
    var arrow = graph.raphael.path(' M' + arrowHelper(180, 6) + ' L' + arrowHelper(180, 2) + ' L' + arrowHelper(183, 10) + ' L' + arrowHelper(180, 18) + ' L' + arrowHelper(180, 14) + ' A' + (graph.scaleVector(r)[0] + 10) + ',' + (graph.scaleVector(r)[1] + 10) + ',0,0,1,' + arrowHelper(170, 14) + ' L' + arrowHelper(170, 18) + ' L' + arrowHelper(167, 10) + ' L' + arrowHelper(170, 2) + ' L' + arrowHelper(170, 6) + ' A' + (graph.scaleVector(r)[0] + 10) + ',' + (graph.scaleVector(r)[1] + 10) + ',0,0,0,' + arrowHelper(180, 6) + ' Z').attr({
        'stroke': null,
        'fill': KhanUtil.INTERACTIVE
    });
    this.set.push(arrow);
    this.centerPoint = graph.addMovablePoint({
        coord: center,
        visible: false
    });
    this.rotateHandle = graph.addMovablePoint({
        coord: [
            Math.sin(275 * Math.PI / 180) * (r + 0.5) + this.cx,
            Math.cos(275 * Math.PI / 180) * (r + 0.5) + this.cy
        ],
        onMove: function (x, y) {
            var angle = Math.atan2(pro.centerPoint.coord[1] - y, pro.centerPoint.coord[0] - x) * 180 / Math.PI;
            pro.rotate(-angle - 5, true);
        }
    });
    this.rotateHandle.constraints.fixedDistance.dist = r + 0.5;
    this.rotateHandle.constraints.fixedDistance.point = this.centerPoint;
    this.rotateHandle.visibleShape.remove();
    this.rotateHandle.mouseTarget.attr({ scale: 2 });
    var isDragging = false;
    var isHovering = false;
    var isHighlight = function () {
        return isHovering || isDragging;
    };
    var self = this;
    var $mouseTarget = $(self.rotateHandle.mouseTarget.getMouseTarget());
    $mouseTarget.bind('vmousedown', function (event) {
        isDragging = true;
        arrow.animate({
            scale: 1.5,
            fill: KhanUtil.INTERACTING
        }, 50);
        $(document).bind('vmouseup.rotateHandle', function (event) {
            isDragging = false;
            if (!isHighlight()) {
                arrow.animate({
                    scale: 1,
                    fill: KhanUtil.INTERACTIVE
                }, 50);
            }
            $(document).unbind('vmouseup.rotateHandle');
        });
    });
    $mouseTarget.bind('vmouseover', function (event) {
        isHovering = true;
        arrow.animate({
            scale: 1.5,
            fill: KhanUtil.INTERACTING
        }, 50);
    });
    $mouseTarget.bind('vmouseout', function (event) {
        isHovering = false;
        if (!isHighlight()) {
            arrow.animate({
                scale: 1,
                fill: KhanUtil.INTERACTIVE
            }, 50);
        }
    });
    var setNodes = $.map(this.set, function (el) {
        return el.node;
    });
    this.makeTranslatable = function makeTranslatable() {
        $(setNodes).css('cursor', 'move');
        $(setNodes).bind('vmousedown', function (event) {
            event.preventDefault();
            var startx = event.pageX - $(graph.raphael.canvas.parentNode).offset().left;
            var starty = event.pageY - $(graph.raphael.canvas.parentNode).offset().top;
            $(document).bind('vmousemove.protractor', function (event) {
                var mouseX = event.pageX - $(graph.raphael.canvas.parentNode).offset().left;
                var mouseY = event.pageY - $(graph.raphael.canvas.parentNode).offset().top;
                mouseX = Math.max(10, Math.min(graph.xpixels - 10, mouseX));
                mouseY = Math.max(10, Math.min(graph.ypixels - 10, mouseY));
                var dx = mouseX - startx;
                var dy = mouseY - starty;
                $.each(pro.set.items, function () {
                    this.translate(dx, dy);
                });
                pro.centerPoint.setCoord([
                    pro.centerPoint.coord[0] + dx / graph.scale[0],
                    pro.centerPoint.coord[1] - dy / graph.scale[1]
                ]);
                pro.rotateHandle.setCoord([
                    pro.rotateHandle.coord[0] + dx / graph.scale[0],
                    pro.rotateHandle.coord[1] - dy / graph.scale[1]
                ]);
                startx = mouseX;
                starty = mouseY;
            });
            $(document).one('vmouseup', function (event) {
                $(document).unbind('vmousemove.protractor');
            });
        });
    };
    this.rotation = 0;
    this.rotate = function (offset, absolute) {
        var center = graph.scalePoint(this.centerPoint.coord);
        if (absolute) {
            this.rotation = 0;
        }
        this.set.rotate(this.rotation + offset, center[0], center[1]);
        this.rotation = this.rotation + offset;
        return this;
    };
    this.moveTo = function moveTo(x, y) {
        var start = graph.scalePoint(pro.centerPoint.coord);
        var end = graph.scalePoint([
            x,
            y
        ]);
        var time = KhanUtil.getDistance(start, end) * 2;
        $({
            x: start[0],
            y: start[1]
        }).animate({
            x: end[0],
            y: end[1]
        }, {
            duration: time,
            step: function (now, fx) {
                var dx = 0;
                var dy = 0;
                if (fx.prop === 'x') {
                    dx = now - graph.scalePoint(pro.centerPoint.coord)[0];
                } else if (fx.prop === 'y') {
                    dy = now - graph.scalePoint(pro.centerPoint.coord)[1];
                }
                $.each(pro.set.items, function () {
                    this.translate(dx, dy);
                });
                pro.centerPoint.setCoord([
                    pro.centerPoint.coord[0] + dx / graph.scale[0],
                    pro.centerPoint.coord[1] - dy / graph.scale[1]
                ]);
                pro.rotateHandle.setCoord([
                    pro.rotateHandle.coord[0] + dx / graph.scale[0],
                    pro.rotateHandle.coord[1] - dy / graph.scale[1]
                ]);
            }
        });
    };
    this.rotateTo = function rotateTo(angle) {
        if (Math.abs(this.rotation - angle) > 180) {
            this.rotation += 360;
        }
        var time = Math.abs(this.rotation - angle) * 5;
        $({ 0: this.rotation }).animate({ 0: angle }, {
            duration: time,
            step: function (now, fx) {
                pro.rotate(now, true);
                pro.rotateHandle.setCoord([
                    Math.sin((now + 275) * Math.PI / 180) * (r + 0.5) + pro.centerPoint.coord[0],
                    Math.cos((now + 275) * Math.PI / 180) * (r + 0.5) + pro.centerPoint.coord[1]
                ]);
            }
        });
    };
    this.remove = function () {
        this.set.remove();
    };
    this.makeTranslatable();
    return this;
}
function Ruler(graphie, options) {
    _.defaults(options, {
        center: [
            0,
            0
        ],
        pixelsPerUnit: 40,
        ticksPerUnit: 10,
        units: 10,
        label: '',
        style: {
            fill: null,
            stroke: KhanUtil.GRAY
        }
    });
    var light = _.extend({}, options.style, { strokeWidth: 1 });
    var bold = _.extend({}, options.style, { strokeWidth: 2 });
    var width = options.units * options.pixelsPerUnit;
    var height = 50;
    var leftBottom = graphie.unscalePoint(kvector.subtract(graphie.scalePoint(options.center), kvector.scale([
        width,
        -height
    ], 0.5)));
    var graphieUnitsPerUnit = options.pixelsPerUnit / graphie.scale[0];
    var graphieUnitsHeight = height / graphie.scale[0];
    var rightTop = kvector.add(leftBottom, [
        options.units * graphieUnitsPerUnit,
        graphieUnitsHeight
    ]);
    var tickHeight = 1;
    var tickHeightMap;
    if (options.ticksPerUnit === 10) {
        tickHeightMap = {
            10: tickHeight,
            5: tickHeight * 0.55,
            1: tickHeight * 0.35
        };
    } else {
        var sizes = [
            1,
            0.6,
            0.45,
            0.3
        ];
        tickHeightMap = {};
        for (var i = options.ticksPerUnit; i >= 1; i /= 2) {
            tickHeightMap[i] = tickHeight * (sizes.shift() || 0.2);
        }
    }
    var tickFrequencies = _.keys(tickHeightMap).sort(function (a, b) {
        return b - a;
    });
    function getTickHeight(i) {
        for (var k = 0; k < tickFrequencies.length; k++) {
            var key = tickFrequencies[k];
            if (i % key === 0) {
                return tickHeightMap[key];
            }
        }
    }
    var left = leftBottom[0];
    var bottom = leftBottom[1];
    var right = rightTop[0];
    var top = rightTop[1];
    var numTicks = options.units * options.ticksPerUnit + 1;
    var set = graphie.raphael.set();
    var px = 1 / graphie.scale[0];
    set.push(graphie.line([
        left - px,
        bottom
    ], [
        right + px,
        bottom
    ], bold));
    set.push(graphie.line([
        left - px,
        top
    ], [
        right + px,
        top
    ], bold));
    _.times(numTicks, function (i) {
        var n = i / options.ticksPerUnit;
        var x = left + n * graphieUnitsPerUnit;
        var height = getTickHeight(i) * graphieUnitsHeight;
        var style = i === 0 || i === numTicks - 1 ? bold : light;
        set.push(graphie.line([
            x,
            bottom
        ], [
            x,
            bottom + height
        ], style));
        if (n % 1 === 0) {
            var coord = graphie.scalePoint([
                x,
                top
            ]);
            var text;
            var offset;
            if (n === 0) {
                text = options.label;
                offset = {
                    mm: 13,
                    cm: 11,
                    m: 8,
                    km: 11,
                    in: 8,
                    ft: 8,
                    yd: 10,
                    mi: 10
                }[text] || 3 * text.toString().length;
            } else {
                text = n;
                offset = -3 * (n.toString().length + 1);
            }
            var label = graphie.raphael.text(coord[0] + offset, coord[1] + 10, text);
            label.attr({
                'font-family': 'KaTeX_Main',
                'font-size': '12px',
                'color': '#444'
            });
            set.push(label);
        }
    });
    var mouseTarget = graphie.mouselayer.path(KhanUtil.svgPath([
        leftBottom,
        [
            left,
            top
        ],
        rightTop,
        [
            right,
            bottom
        ],
        true
    ]));
    mouseTarget.attr({
        fill: '#000',
        opacity: 0,
        stroke: '#000',
        'stroke-width': 2
    });
    set.push(mouseTarget);
    var setNodes = $.map(set, function (el) {
        return el.node;
    });
    $(setNodes).css('cursor', 'move');
    $(setNodes).bind('vmousedown', function (event) {
        event.preventDefault();
        var startx = event.pageX - $(graphie.raphael.canvas.parentNode).offset().left;
        var starty = event.pageY - $(graphie.raphael.canvas.parentNode).offset().top;
        $(document).bind('vmousemove.ruler', function (event) {
            var mouseX = event.pageX - $(graphie.raphael.canvas.parentNode).offset().left;
            var mouseY = event.pageY - $(graphie.raphael.canvas.parentNode).offset().top;
            mouseX = Math.max(10, Math.min(graphie.xpixels - 10, mouseX));
            mouseY = Math.max(10, Math.min(graphie.ypixels - 10, mouseY));
            var dx = mouseX - startx;
            var dy = mouseY - starty;
            set.translate(dx, dy);
            leftBottomHandle.setCoord([
                leftBottomHandle.coord[0] + dx / graphie.scale[0],
                leftBottomHandle.coord[1] - dy / graphie.scale[1]
            ]);
            rightBottomHandle.setCoord([
                rightBottomHandle.coord[0] + dx / graphie.scale[0],
                rightBottomHandle.coord[1] - dy / graphie.scale[1]
            ]);
            startx = mouseX;
            starty = mouseY;
        });
        $(document).one('vmouseup', function (event) {
            $(document).unbind('vmousemove.ruler');
        });
    });
    var leftBottomHandle = graphie.addMovablePoint({
        coord: leftBottom,
        normalStyle: {
            fill: KhanUtil.INTERACTIVE,
            'fill-opacity': 0,
            stroke: KhanUtil.INTERACTIVE
        },
        highlightStyle: {
            fill: KhanUtil.INTERACTING,
            'fill-opacity': 0.1,
            stroke: KhanUtil.INTERACTING
        },
        pointSize: 6,
        onMove: function (x, y) {
            var dy = rightBottomHandle.coord[1] - y;
            var dx = rightBottomHandle.coord[0] - x;
            var angle = Math.atan2(dy, dx) * 180 / Math.PI;
            var center = kvector.scale(kvector.add([
                x,
                y
            ], rightBottomHandle.coord), 0.5);
            var scaledCenter = graphie.scalePoint(center);
            var oldCenter = kvector.scale(kvector.add(leftBottomHandle.coord, rightBottomHandle.coord), 0.5);
            var scaledOldCenter = graphie.scalePoint(oldCenter);
            var diff = kvector.subtract(scaledCenter, scaledOldCenter);
            set.rotate(-angle, scaledOldCenter[0], scaledOldCenter[1]);
            set.translate(diff[0], diff[1]);
        }
    });
    var rightBottomHandle = graphie.addMovablePoint({
        coord: [
            right,
            bottom
        ],
        normalStyle: {
            fill: KhanUtil.INTERACTIVE,
            'fill-opacity': 0,
            stroke: KhanUtil.INTERACTIVE
        },
        highlightStyle: {
            fill: KhanUtil.INTERACTING,
            'fill-opacity': 0.1,
            stroke: KhanUtil.INTERACTING
        },
        pointSize: 6,
        onMove: function (x, y) {
            var dy = y - leftBottomHandle.coord[1];
            var dx = x - leftBottomHandle.coord[0];
            var angle = Math.atan2(dy, dx) * 180 / Math.PI;
            var center = kvector.scale(kvector.add([
                x,
                y
            ], leftBottomHandle.coord), 0.5);
            var scaledCenter = graphie.scalePoint(center);
            var oldCenter = kvector.scale(kvector.add(leftBottomHandle.coord, rightBottomHandle.coord), 0.5);
            var scaledOldCenter = graphie.scalePoint(oldCenter);
            var diff = kvector.subtract(scaledCenter, scaledOldCenter);
            set.rotate(-angle, scaledOldCenter[0], scaledOldCenter[1]);
            set.translate(diff[0], diff[1]);
        }
    });
    leftBottomHandle.constraints.fixedDistance.dist = width / graphie.scale[0];
    leftBottomHandle.constraints.fixedDistance.point = rightBottomHandle;
    rightBottomHandle.constraints.fixedDistance.dist = width / graphie.scale[0];
    rightBottomHandle.constraints.fixedDistance.point = leftBottomHandle;
    this.remove = function () {
        set.remove();
        leftBottomHandle.remove();
        rightBottomHandle.remove();
    };
    return this;
}
function MovableAngle(graphie, options) {
    this.graphie = graphie;
    _.extend(this, options);
    _.defaults(this, {
        normalStyle: {
            'stroke': KhanUtil.INTERACTIVE,
            'stroke-width': 2,
            'fill': KhanUtil.INTERACTIVE
        },
        highlightStyle: {
            'stroke': KhanUtil.INTERACTING,
            'stroke-width': 2,
            'fill': KhanUtil.INTERACTING
        },
        labelStyle: {
            'stroke': KhanUtil.DYNAMIC,
            'stroke-width': 1,
            'color': KhanUtil.DYNAMIC
        },
        angleStyle: {
            'stroke': KhanUtil.DYNAMIC,
            'stroke-width': 1,
            'color': KhanUtil.DYNAMIC
        },
        allowReflex: true
    });
    if (!this.points || this.points.length !== 3) {
        throw new Error('MovableAngle requires 3 points');
    }
    this.points = _.map(options.points, function (point) {
        if (_.isArray(point)) {
            return graphie.addMovablePoint({
                coord: point,
                visible: false,
                constraints: { fixed: true },
                normalStyle: this.normalStyle
            });
        } else {
            return point;
        }
    }, this);
    this.coords = _.pluck(this.points, 'coord');
    if (this.reflex == null) {
        if (this.allowReflex) {
            this.reflex = this._getClockwiseAngle(this.coords) > 180;
        } else {
            this.reflex = false;
        }
    }
    this.rays = _.map([
        0,
        2
    ], function (i) {
        return graphie.addMovableLineSegment({
            pointA: this.points[1],
            pointZ: this.points[i],
            fixed: true,
            extendRay: true
        });
    }, this);
    this.temp = [];
    this.labeledAngle = graphie.label([
        0,
        0
    ], '', 'center', this.labelStyle);
    if (!this.fixed) {
        this.addMoveHandlers();
        this.addHighlightHandlers();
    }
    this.update();
}
_.extend(MovableAngle.prototype, {
    points: [],
    snapDegrees: 0,
    snapOffsetDeg: 0,
    angleLabel: '',
    numArcs: 1,
    pushOut: 0,
    fixed: false,
    addMoveHandlers: function () {
        var graphie = this.graphie;
        function tooClose(point1, point2) {
            var safeDistance = 30;
            var distance = KhanUtil.getDistance(graphie.scalePoint(point1), graphie.scalePoint(point2));
            return distance < safeDistance;
        }
        var points = this.points;
        points[1].onMove = function (x, y) {
            var oldVertex = points[1].coord;
            var newVertex = [
                x,
                y
            ];
            var delta = addPoints(newVertex, reverseVector(oldVertex));
            var valid = true;
            var newPoints = {};
            _.each([
                0,
                2
            ], function (i) {
                var oldPoint = points[i].coord;
                var newPoint = addPoints(oldPoint, delta);
                var angle = KhanUtil.findAngle(newVertex, newPoint);
                angle *= Math.PI / 180;
                newPoint = graphie.constrainToBoundsOnAngle(newPoint, 10, angle);
                newPoints[i] = newPoint;
                if (tooClose(newVertex, newPoint)) {
                    valid = false;
                }
            });
            if (valid) {
                _.each(newPoints, function (newPoint, i) {
                    points[i].setCoord(newPoint);
                });
            }
            return valid;
        };
        var snap = this.snapDegrees;
        var snapOffset = this.snapOffsetDeg;
        _.each([
            0,
            2
        ], function (i) {
            points[i].onMove = function (x, y) {
                var newPoint = [
                    x,
                    y
                ];
                var vertex = points[1].coord;
                if (tooClose(vertex, newPoint)) {
                    return false;
                } else if (snap) {
                    var angle = KhanUtil.findAngle(newPoint, vertex);
                    angle = Math.round((angle - snapOffset) / snap) * snap + snapOffset;
                    var distance = KhanUtil.getDistance(newPoint, vertex);
                    return addPoints(vertex, graphie.polar(distance, angle));
                } else {
                    return true;
                }
            };
        });
        $(points).on('move', function () {
            this.update();
            $(this).trigger('move');
        }.bind(this));
    },
    addHighlightHandlers: function () {
        var vertex = this.points[1];
        vertex.onHighlight = function () {
            _.each(this.points, function (point) {
                point.visibleShape.animate(this.highlightStyle, 50);
            }, this);
            _.each(this.rays, function (ray) {
                ray.visibleLine.animate(this.highlightStyle, 50);
                ray.arrowStyle = _.extend({}, ray.arrowStyle, {
                    'color': this.highlightStyle.stroke,
                    'stroke': this.highlightStyle.stroke
                });
            }, this);
            this.angleStyle = _.extend({}, this.angleStyle, {
                'color': this.highlightStyle.stroke,
                'stroke': this.highlightStyle.stroke
            });
            this.update();
        }.bind(this);
        vertex.onUnhighlight = function () {
            _.each(this.points, function (point) {
                point.visibleShape.animate(this.normalStyle, 50);
            }, this);
            _.each(this.rays, function (ray) {
                ray.visibleLine.animate(ray.normalStyle, 50);
                ray.arrowStyle = _.extend({}, ray.arrowStyle, {
                    'color': ray.normalStyle.stroke,
                    'stroke': ray.normalStyle.stroke
                });
            }, this);
            this.angleStyle = _.extend({}, this.angleStyle, {
                'color': KhanUtil.DYNAMIC,
                'stroke': KhanUtil.DYNAMIC
            });
            this.update();
        }.bind(this);
    },
    _getClockwiseAngle: function (coords) {
        var clockwiseAngle = (KhanUtil.findAngle(coords[2], coords[0], coords[1]) + 360) % 360;
        return clockwiseAngle;
    },
    isReflex: function () {
        return this.reflex;
    },
    isClockwise: function () {
        var clockwiseReflexive = this._getClockwiseAngle(this.coords) > 180;
        return clockwiseReflexive === this.reflex;
    },
    getClockwiseCoords: function () {
        if (this.isClockwise()) {
            return _.clone(this.coords);
        } else {
            return _.clone(this.coords).reverse();
        }
    },
    update: function (shouldChangeReflexivity) {
        var prevCoords = this.coords;
        this.coords = _.pluck(this.points, 'coord');
        _.invoke(this.points, 'updateLineEnds');
        var prevAngle = this._getClockwiseAngle(prevCoords);
        var angle = this._getClockwiseAngle(this.coords);
        var prevClockwiseReflexive = prevAngle > 180;
        var clockwiseReflexive = angle > 180;
        if (this.allowReflex) {
            if (shouldChangeReflexivity == null) {
                shouldChangeReflexivity = prevClockwiseReflexive !== clockwiseReflexive && Math.abs(angle - prevAngle) < 180;
            }
            if (shouldChangeReflexivity) {
                this.reflex = !this.reflex;
            }
        }
        _.invoke(this.temp, 'remove');
        this.temp = this.graphie.labelAngle({
            point1: this.coords[0],
            vertex: this.coords[1],
            point3: this.coords[2],
            label: this.labeledAngle,
            text: this.angleLabel,
            numArcs: this.numArcs,
            pushOut: this.pushOut,
            clockwise: this.reflex === clockwiseReflexive,
            style: this.angleStyle
        });
    },
    remove: function () {
        _.invoke(this.rays, 'remove');
        _.invoke(this.temp, 'remove');
        this.labeledAngle.remove();
    }
});
},{"../third_party/jquery.mobile.vmouse.js":16,"./graphie.js":2,"./kline.js":4,"./kpoint.js":6,"./kvector.js":7,"./wrapped-ellipse.js":13,"./wrapped-line.js":14,"./wrapped-path.js":15}],4:[function(require,module,exports){
var kpoint = require('./kpoint.js');
var knumber = require('./knumber.js');
var kline = KhanUtil.kline = {
    distanceToPoint: function (line, point) {
        return kpoint.distanceToLine(point, line);
    },
    reflectPoint: function (line, point) {
        return kpoint.reflectOverLine(point, line);
    },
    midpoint: function (line) {
        return [
            (line[0][0] + line[1][0]) / 2,
            (line[0][1] + line[1][1]) / 2
        ];
    },
    equal: function (line1, line2, tolerance) {
        var x1 = line1[0][0];
        var y1 = line1[0][1];
        var x2 = line1[1][0];
        var y2 = line1[1][1];
        return _.every(line2, function (point) {
            var x3 = point[0];
            var y3 = point[1];
            var area = 1 / 2 * Math.abs(x1 * y2 + x2 * y3 + x3 * y1 - x2 * y1 - x3 * y2 - x1 * y3);
            return knumber.equal(area, 0, tolerance);
        });
    },
    intersect: function (px, py, rx, ry, qx, qy, sx, sy) {
        function cross(vx, vy, wx, wy) {
            return vx * wy - vy * wx;
        }
        if (cross(rx, ry, sx, sy) === 0) {
            return cross(qx - px, qy - py, rx, ry) === 0;
        } else {
            var t = cross(qx - px, qy - py, sx, sy) / cross(rx, ry, sx, sy);
            var u = cross(qx - px, qy - py, rx, ry) / cross(rx, ry, sx, sy);
            return 0 <= t && t <= 1 && 0 <= u && u <= 1;
        }
    }
};
module.exports = kline;
},{"./knumber.js":5,"./kpoint.js":6}],5:[function(require,module,exports){
var DEFAULT_TOLERANCE = 1e-9;
var EPSILON = Math.pow(2, -42);
var knumber = KhanUtil.knumber = {
    DEFAULT_TOLERANCE: DEFAULT_TOLERANCE,
    EPSILON: EPSILON,
    is: function (x) {
        return _.isNumber(x) && !_.isNaN(x);
    },
    equal: function (x, y, tolerance) {
        if (x == null || y == null) {
            return x === y;
        }
        if (tolerance == null) {
            tolerance = DEFAULT_TOLERANCE;
        }
        return Math.abs(x - y) < tolerance;
    },
    sign: function (x, tolerance) {
        return knumber.equal(x, 0, tolerance) ? 0 : Math.abs(x) / x;
    },
    round: function (num, precision) {
        var factor = Math.pow(10, precision);
        return Math.round(num * factor) / factor;
    },
    roundTo: function (num, increment) {
        return Math.round(num / increment) * increment;
    },
    floorTo: function (num, increment) {
        return Math.floor(num / increment) * increment;
    },
    ceilTo: function (num, increment) {
        return Math.ceil(num / increment) * increment;
    },
    isInteger: function (num, tolerance) {
        return knumber.equal(Math.round(num), num, tolerance);
    },
    toFraction: function (decimal, tolerance, max_denominator) {
        max_denominator = max_denominator || 1000;
        tolerance = tolerance || EPSILON;
        var n = [
                1,
                0
            ], d = [
                0,
                1
            ];
        var a = Math.floor(decimal);
        var rem = decimal - a;
        while (d[0] <= max_denominator) {
            if (knumber.equal(n[0] / d[0], decimal, tolerance)) {
                return [
                    n[0],
                    d[0]
                ];
            }
            n = [
                a * n[0] + n[1],
                n[0]
            ];
            d = [
                a * d[0] + d[1],
                d[0]
            ];
            a = Math.floor(1 / rem);
            rem = 1 / rem - a;
        }
        return [
            decimal,
            1
        ];
    }
};
module.exports = knumber;
},{}],6:[function(require,module,exports){
var kvector = require('./kvector.js');
var knumber = require('./knumber.js');
var kpoint = KhanUtil.kpoint = {
    rotateRad: function (point, theta, center) {
        if (center === undefined) {
            return kvector.rotateRad(point, theta);
        } else {
            return kvector.add(center, kvector.rotateRad(kvector.subtract(point, center), theta));
        }
    },
    rotateDeg: function (point, theta, center) {
        if (center === undefined) {
            return kvector.rotateDeg(point, theta);
        } else {
            return kvector.add(center, kvector.rotateDeg(kvector.subtract(point, center), theta));
        }
    },
    distanceToPoint: function (point1, point2) {
        return kvector.length(kvector.subtract(point1, point2));
    },
    distanceToLine: function (point, line) {
        var lv = kvector.subtract(line[1], line[0]);
        var pv = kvector.subtract(point, line[0]);
        var projectedPv = kvector.projection(pv, lv);
        var distancePv = kvector.subtract(projectedPv, pv);
        return kvector.length(distancePv);
    },
    reflectOverLine: function (point, line) {
        var lv = kvector.subtract(line[1], line[0]);
        var pv = kvector.subtract(point, line[0]);
        var projectedPv = kvector.projection(pv, lv);
        var reflectedPv = kvector.subtract(kvector.scale(projectedPv, 2), pv);
        return kvector.add(line[0], reflectedPv);
    },
    compare: function (point1, point2, equalityTolerance) {
        if (point1.length !== point2.length) {
            return point1.length - point2.length;
        }
        for (var i = 0; i < point1.length; i++) {
            if (!knumber.equal(point1[i], point2[i], equalityTolerance)) {
                return point1[i] - point2[i];
            }
        }
        return 0;
    }
};
_.extend(kpoint, {
    is: kvector.is,
    addVector: kvector.add,
    addVectors: kvector.add,
    subtractVector: kvector.subtract,
    equal: kvector.equal,
    polarRadFromCart: kvector.polarRadFromCart,
    polarDegFromCart: kvector.polarDegFromCart,
    cartFromPolarRad: kvector.cartFromPolarRad,
    cartFromPolarDeg: kvector.cartFromPolarDeg,
    round: kvector.round,
    roundTo: kvector.roundTo,
    floorTo: kvector.floorTo,
    ceilTo: kvector.ceilTo
});
module.exports = kpoint;
},{"./knumber.js":5,"./kvector.js":7}],7:[function(require,module,exports){
var knumber = require('./knumber.js');
function arraySum(array) {
    return _.reduce(array, function (memo, arg) {
        return memo + arg;
    }, 0);
}
function arrayProduct(array) {
    return _.reduce(array, function (memo, arg) {
        return memo * arg;
    }, 1);
}
var kvector = KhanUtil.kvector = {
    is: function (vec, length) {
        if (!_.isArray(vec)) {
            return false;
        }
        if (length !== undefined && vec.length !== length) {
            return false;
        }
        return _.all(vec, knumber.is);
    },
    normalize: function (v) {
        return kvector.scale(v, 1 / kvector.length(v));
    },
    length: function (v) {
        return Math.sqrt(kvector.dot(v, v));
    },
    dot: function (a, b) {
        var vecs = _.toArray(arguments);
        var zipped = _.zip.apply(_, vecs);
        var multiplied = _.map(zipped, arrayProduct);
        return arraySum(multiplied);
    },
    add: function () {
        var points = _.toArray(arguments);
        var zipped = _.zip.apply(_, points);
        return _.map(zipped, arraySum);
    },
    subtract: function (v1, v2) {
        return _.map(_.zip(v1, v2), function (dim) {
            return dim[0] - dim[1];
        });
    },
    negate: function (v) {
        return _.map(v, function (x) {
            return -x;
        });
    },
    scale: function (v1, scalar) {
        return _.map(v1, function (x) {
            return x * scalar;
        });
    },
    equal: function (v1, v2, tolerance) {
        return _.all(_.zip(v1, v2), function (pair) {
            return knumber.equal(pair[0], pair[1], tolerance);
        });
    },
    codirectional: function (v1, v2, tolerance) {
        if (knumber.equal(kvector.length(v1), 0, tolerance) || knumber.equal(kvector.length(v2), 0, tolerance)) {
            return true;
        }
        v1 = kvector.normalize(v1);
        v2 = kvector.normalize(v2);
        return kvector.equal(v1, v2, tolerance);
    },
    collinear: function (v1, v2, tolerance) {
        return kvector.codirectional(v1, v2, tolerance) || kvector.codirectional(v1, kvector.negate(v2), tolerance);
    },
    polarRadFromCart: function (v) {
        var radius = kvector.length(v);
        var theta = Math.atan2(v[1], v[0]);
        if (theta < 0) {
            theta += 2 * Math.PI;
        }
        return [
            radius,
            theta
        ];
    },
    polarDegFromCart: function (v) {
        var polar = kvector.polarRadFromCart(v);
        return [
            polar[0],
            polar[1] * 180 / Math.PI
        ];
    },
    cartFromPolarRad: function (radius, theta) {
        if (_.isUndefined(theta)) {
            theta = radius[1];
            radius = radius[0];
        }
        return [
            radius * Math.cos(theta),
            radius * Math.sin(theta)
        ];
    },
    cartFromPolarDeg: function (radius, theta) {
        if (_.isUndefined(theta)) {
            theta = radius[1];
            radius = radius[0];
        }
        return kvector.cartFromPolarRad(radius, theta * Math.PI / 180);
    },
    rotateRad: function (v, theta) {
        var polar = kvector.polarRadFromCart(v);
        var angle = polar[1] + theta;
        return kvector.cartFromPolarRad(polar[0], angle);
    },
    rotateDeg: function (v, theta) {
        var polar = kvector.polarDegFromCart(v);
        var angle = polar[1] + theta;
        return kvector.cartFromPolarDeg(polar[0], angle);
    },
    angleRad: function (v1, v2) {
        return Math.acos(kvector.dot(v1, v2) / (kvector.length(v1) * kvector.length(v2)));
    },
    angleDeg: function (v1, v2) {
        return kvector.angleRad(v1, v2) * 180 / Math.PI;
    },
    projection: function (v1, v2) {
        var scalar = kvector.dot(v1, v2) / kvector.dot(v2, v2);
        return kvector.scale(v2, scalar);
    },
    round: function (vec, precision) {
        return _.map(vec, function (elem, i) {
            return knumber.round(elem, precision[i] || precision);
        });
    },
    roundTo: function (vec, increment) {
        return _.map(vec, function (elem, i) {
            return knumber.roundTo(elem, increment[i] || increment);
        });
    },
    floorTo: function (vec, increment) {
        return _.map(vec, function (elem, i) {
            return knumber.floorTo(elem, increment[i] || increment);
        });
    },
    ceilTo: function (vec, increment) {
        return _.map(vec, function (elem, i) {
            return knumber.ceilTo(elem, increment[i] || increment);
        });
    }
};
module.exports = kvector;
},{"./knumber.js":5}],8:[function(require,module,exports){
var pluck = function (table, subKey) {
    return _.object(_.map(table, function (value, key) {
        return [
            key,
            value[subKey]
        ];
    }));
};
var mapObject = function (obj, lambda) {
    var result = {};
    _.each(_.keys(obj), function (key) {
        result[key] = lambda(obj[key], key);
    });
    return result;
};
var mapObjectFromArray = function (arr, lambda) {
    var result = {};
    _.each(arr, function (elem) {
        result[elem] = lambda(elem);
    });
    return result;
};
module.exports = {
    pluck: pluck,
    mapObject: mapObject,
    mapObjectFromArray: mapObjectFromArray
};
},{}],9:[function(require,module,exports){
function findChildOrAdd(elem, className) {
    var $child = $(elem).find('.' + className);
    if ($child.length === 0) {
        return $('<span>').addClass(className).appendTo($(elem));
    } else {
        return $child;
    }
}
function doCallback(elem, callback) {
    var tries = 0;
    (function check() {
        var height = elem.scrollHeight;
        if (height > 18 || tries >= 10) {
            callback();
        } else {
            tries++;
            setTimeout(check, 100);
        }
    }());
}
$.extend(KhanUtil, {
    processMath: function (elem, text, force, callback) {
        var $elem = $(elem);
        if ($elem.attr('data-math-formula') == null || force) {
            var $katexHolder = findChildOrAdd($elem, 'katex-holder');
            var $mathjaxHolder = findChildOrAdd($elem, 'mathjax-holder');
            var script = $mathjaxHolder.find('script[type=\'math/tex\']')[0];
            if (text == null) {
                if ($elem.attr('data-math-formula')) {
                    text = $elem.attr('data-math-formula');
                } else if (script) {
                    text = script.text || script.textContent;
                }
            }
            text = text != null ? text + '' : '';
            if (KhanUtil.cleanMath) {
                text = KhanUtil.cleanMath(text);
            }
            $elem.attr('data-math-formula', text);
            if (Exercises.useKatex) {
                try {
                    katex.render(text, $katexHolder[0]);
                    if ($elem.attr('data-math-type') === 'mathjax') {
                        var jax = MathJax.Hub.getJaxFor(script);
                        if (jax) {
                            var e = jax.SourceElement();
                            if (e.previousSibling && e.previousSibling.className) {
                                jax.Remove();
                            }
                        }
                    }
                    $elem.attr('data-math-type', 'katex');
                    if (callback) {
                        doCallback(elem, callback);
                    }
                    return;
                } catch (err) {
                    if (err.__proto__ !== katex.ParseError.prototype) {
                        throw err;
                    }
                }
            }
            $elem.attr('data-math-type', 'mathjax');
            if (!script) {
                $mathjaxHolder.append('<script type=\'math/tex\'>' + text.replace(/<\//g, '< /') + '</script>');
            } else {
                if ('text' in script) {
                    script.text = text;
                } else {
                    script.textContent = text;
                }
            }
            if (typeof MathJax !== 'undefined') {
                MathJax.Hub.Queue([
                    'Reprocess',
                    MathJax.Hub,
                    $mathjaxHolder[0]
                ]);
                MathJax.Hub.Queue(function () {
                    KhanUtil.debugLog('MathJax done typesetting (' + text + ')');
                });
                if (callback) {
                    MathJax.Hub.Queue(function () {
                        var cb = MathJax.Callback(function () {
                        });
                        doCallback(elem, function () {
                            callback();
                            cb();
                        });
                        return cb;
                    });
                }
            }
        }
    },
    processAllMath: function (elem, force) {
        var $elem = $(elem);
        $elem.filter('code').add($elem.find('code')).each(function () {
            var $this = $(this);
            var text = $this.attr('data-math-formula');
            if (text == null) {
                text = $this.text();
                $this.empty();
            }
            KhanUtil.processMath(this, text, force);
        });
    },
    cleanupMath: function (elem) {
        var $elem = $(elem);
        if ($elem.attr('data-math-formula')) {
            if (typeof MathJax !== 'undefined') {
                var jax = MathJax.Hub.getJaxFor($elem.find('script')[0]);
                if (jax) {
                    var e = jax.SourceElement();
                    if (e.previousSibling && e.previousSibling.className) {
                        jax.Remove();
                    }
                }
            }
            $elem.text($elem.attr('data-math-formula'));
            $elem.attr('data-math-formula', null);
            $elem.attr('data-math-type', null);
        }
        return elem;
    },
    retrieveMathFormula: function (elem) {
        return $(elem).attr('data-math-formula');
    }
});
$.fn.tex = function () {
    KhanUtil.processAllMath(this, false);
    return this;
};
$.fn.texCleanup = function () {
    this.filter('code').add(this.find('code')).each(function () {
        KhanUtil.cleanupMath(this);
    });
    return this;
};
},{}],10:[function(require,module,exports){
var crc32 = require('./crc32.js');
var localMode;
var VARS = {};
$.tmpl = {
    DATA_ENSURE_LOOPS: 0,
    attr: {
        'data-ensure': function (elem, ensure) {
            return function (elem) {
                var result = !!(ensure && $.tmpl.getVAR(ensure));
                if (!result) {
                    if ($.tmpl.DATA_ENSURE_LOOPS++ > 10000 && localMode) {
                        alert('unsatisfiable data-ensure?');
                        return true;
                    }
                }
                return result;
            };
        },
        'data-if': function (elem, value) {
            var $elem = $(elem);
            value = value && $.tmpl.getVAR(value);
            var $nextElem = $elem.next();
            if ($nextElem.data('lastCond') === undefined) {
                $nextElem.data('lastCond', value);
            }
            if (!value) {
                return [];
            }
        },
        'data-else-if': function (elem, value) {
            var $elem = $(elem);
            var lastCond = $elem.data('lastCond');
            value = !lastCond && value && $.tmpl.getVAR(value);
            var $nextElem = $elem.next();
            if ($nextElem.data('lastCond') === undefined) {
                $nextElem.data('lastCond', lastCond || value);
            }
            if (!value) {
                return [];
            }
        },
        'data-else': function (elem) {
            var $elem = $(elem);
            if ($elem.data('lastCond')) {
                return [];
            }
        },
        'data-each': function (elem, value) {
            var match;
            $(elem).removeAttr('data-each');
            if (match = /^(.+) times(?: as (\w+))?$/.exec(value)) {
                var times = $.tmpl.getVAR(match[1]);
                return {
                    items: $.map(new Array(times), function (e, i) {
                        return i;
                    }),
                    value: match[2],
                    oldValue: VARS[match[2]]
                };
            } else if (match = /^(.*?)(?: as (?:(\w+), )?(\w+))?$/.exec(value)) {
                return {
                    items: $.tmpl.getVAR(match[1]),
                    value: match[3],
                    pos: match[2],
                    oldValue: VARS[match[3]],
                    oldPos: VARS[match[2]]
                };
            }
        },
        'data-unwrap': function (elem) {
            return $(elem).contents();
        },
        'data-video-hint': function (elem) {
            var youtubeIds = $(elem).data('youtube-id');
            if (!youtubeIds) {
                return;
            }
            youtubeIds = youtubeIds.split(/,\s*/);
            var author = $(elem).data('video-hint-author') || 'Sal';
            var msg = $._('Watch %(author)s work through a very similar ' + 'problem:', { author: author });
            var preface = $('<p>').text(msg);
            var wrapper = $('<div>', { 'class': 'video-hint' });
            wrapper.append(preface);
            _.each(youtubeIds, function (youtubeId) {
                var href = 'http://www.khanacademy.org/embed_video?v=' + youtubeId;
                var iframe = $('<iframe>').attr({
                    'frameborder': '0',
                    'scrolling': 'no',
                    'width': '100%',
                    'height': '360px',
                    'src': href
                });
                wrapper.append(iframe);
            });
            return wrapper;
        }
    },
    type: {
        'var': function (elem, value) {
            if (!value && $(elem).children().length > 0) {
                return function (elem) {
                    return $.tmpl.type['var'](elem, elem.innerHTML);
                };
            }
            value = value || $.tmpl.getVAR(elem);
            var name = elem.id;
            if (name) {
                var setVAR = function (name, value) {
                    if (KhanUtil[name]) {
                        Khan.error('Defining variable \'' + name + '\' overwrites utility property of same name.');
                    }
                    VARS[name] = value;
                };
                if (name.indexOf(',') !== -1) {
                    var parts = name.split(/\s*,\s*/);
                    $.each(parts, function (i, part) {
                        if (part.length > 0) {
                            setVAR(part, value[i]);
                        }
                    });
                } else {
                    setVAR(name, value);
                }
            } else {
                if (value == null) {
                    return [];
                } else {
                    var div = $('<div>');
                    var html = div.append(value + ' ').html();
                    return div.html(html.slice(0, -1)).contents();
                }
            }
        }
    },
    getVAR: function (elem, ctx) {
        var code = elem.nodeName ? $(elem).text() : elem;
        if (ctx == null) {
            ctx = {};
        }
        function doEval() {
            with (Math) {
                with (KhanUtil) {
                    with (ctx) {
                        with (VARS) {
                            return eval('(function() { return (' + code + '); })()');
                        }
                    }
                }
            }
        }
        if (Khan.query.debug != null) {
            return doEval();
        } else {
            try {
                return doEval();
            } catch (e) {
                var info;
                if (elem.nodeName) {
                    info = elem.nodeName.toLowerCase();
                    if (elem.id != null && elem.id.length > 0) {
                        info += '#' + elem.id;
                    }
                } else {
                    info = JSON.stringify(code);
                }
                Khan.error('Error while evaluating ' + info, e);
            }
        }
    },
    getVarsHash: function () {
        return crc32(JSON.stringify($.map(VARS, function (value, key) {
            return [
                key,
                String(value)
            ];
        })));
    }
};
if (typeof KhanUtil !== 'undefined') {
    KhanUtil.tmpl = $.tmpl;
}
$.fn.tmplLoad = function (problem, info) {
    VARS = {};
    $.tmpl.DATA_ENSURE_LOOPS = 0;
    localMode = info.localMode;
    if (localMode) {
        $.tmpl.VARS = VARS;
    }
};
$.fn.tmpl = function () {
    for (var i = 0, l = this.length; i < l; i++) {
        traverse(this[i]);
    }
    return this;
    function traverse(elem) {
        var post = [], child = elem.childNodes, ret = process(elem, post);
        if (ret === false) {
            return traverse(elem);
        } else if (ret === undefined) {
        } else if (typeof ret === 'object' && typeof ret.length !== 'undefined') {
            if (elem.parentNode) {
                $.each(ret, function (i, rep) {
                    if (rep.nodeType) {
                        elem.parentNode.insertBefore(rep, elem);
                    }
                });
                $.each(ret, function (i, rep) {
                    traverse(rep);
                });
                elem.parentNode.removeChild(elem);
            }
            return null;
        } else if (ret.items) {
            var origParent = elem.parentNode, origNext = elem.nextSibling;
            $.each(ret.items, function (pos, value) {
                if (ret.value) {
                    VARS[ret.value] = value;
                }
                if (ret.pos) {
                    VARS[ret.pos] = pos;
                }
                var clone = $(elem).clone(true).removeAttr('data-each').removeData('each')[0];
                var conditionals = [
                    'data-if',
                    'data-else-if',
                    'data-else'
                ];
                var declarations = '';
                declarations += ret.pos ? 'var ' + ret.pos + ' = ' + JSON.stringify(pos) + ';' : '';
                declarations += ret.value ? 'var ' + ret.value + ' = ' + JSON.stringify(value) + ';' : '';
                for (var i = 0; i < conditionals.length; i++) {
                    var conditional = conditionals[i];
                    $(clone).find('[' + conditional + ']').each(function () {
                        var code = $(this).attr(conditional);
                        code = '(function() { ' + declarations + ' return ' + code + ' })()';
                        $(this).attr(conditional, code);
                    });
                }
                $(clone).find('.graphie').addBack().filter('.graphie').each(function () {
                    var code = $(this).text();
                    $(this).text(declarations + code);
                });
                if (origNext) {
                    origParent.insertBefore(clone, origNext);
                } else {
                    origParent.appendChild(clone);
                }
                traverse(clone);
            });
            if (ret.value) {
                VARS[ret.value] = ret.oldValue;
            }
            if (ret.pos) {
                VARS[ret.pos] = ret.oldPos;
            }
            $(elem).remove();
            return null;
        }
        for (var i = 0; i < child.length; i++) {
            if (child[i].nodeType === 1 && traverse(child[i]) === null) {
                i--;
            }
        }
        for (var i = 0, l = post.length; i < l; i++) {
            if (post[i](elem) === false) {
                return traverse(elem);
            }
        }
        return elem;
    }
    function process(elem, post) {
        var ret, $elem = $(elem);
        for (var attr in $.tmpl.attr) {
            if ($.tmpl.attr.hasOwnProperty(attr)) {
                var value;
                if (/^data-/.test(attr)) {
                    value = $elem.data(attr.replace(/^data-/, ''));
                } else {
                    value = $elem.attr(attr);
                }
                if (value !== undefined) {
                    ret = $.tmpl.attr[attr](elem, value);
                    if (typeof ret === 'function') {
                        post.push(ret);
                    } else if (ret !== undefined) {
                        return ret;
                    }
                }
            }
        }
        var type = elem.nodeName.toLowerCase();
        if ($.tmpl.type[type] != null) {
            ret = $.tmpl.type[type](elem);
            if (typeof ret === 'function') {
                post.push(ret);
            }
        }
        return ret;
    }
};
$.extend($.expr[':'], {
    inherited: function (el) {
        return $(el).data('inherited');
    }
});
$.fn.extend({
    tmplApply: function (options) {
        options = options || {};
        var attribute = options.attribute || 'id', defaultApply = options.defaultApply || 'replace', parent = {};
        return this.each(function () {
            var $this = $(this), name = $this.attr(attribute), hint = $this.data('apply') && !$this.data('apply').indexOf('hint');
            if (name) {
                if (name in parent && !hint) {
                    parent[name] = $.tmplApplyMethods[$this.data('apply') || defaultApply].call(parent[name], this);
                    if (parent[name] == null) {
                        delete parent[name];
                    }
                } else if ($this.closest(':inherited').length > 0) {
                    parent[name] = this;
                }
            }
        });
    }
});
$.extend({
    tmplApplyMethods: {
        remove: function (elem) {
            $(this).remove();
            $(elem).remove();
        },
        replace: function (elem) {
            $(this).replaceWith(elem);
            return elem;
        },
        splice: function (elem) {
            $(this).replaceWith($(elem).contents());
        },
        append: function (elem) {
            $(this).append(elem);
            return this;
        },
        appendContents: function (elem) {
            $(this).append($(elem).contents());
            $(elem).remove();
            return this;
        },
        prepend: function (elem) {
            $(this).prepend(elem);
            return this;
        },
        prependContents: function (elem) {
            $(this).prepend($(elem).contents());
            $(elem).remove();
            return this;
        },
        before: function (elem) {
            $(this).before(elem);
            return this;
        },
        beforeContents: function (elem) {
            $(this).before($(elem).contents());
            $(elem).remove();
            return this;
        },
        after: function (elem) {
            $(this).after(elem);
            return this;
        },
        afterContents: function (elem) {
            $(this).after($(elem).contents());
            $(elem).remove();
            return this;
        },
        appendVars: function (elem) {
            var parentEnsure = $(this).data('ensure') || '1';
            var childEnsure = $(elem).data('ensure') || '1';
            $(this).data('ensure', '(' + parentEnsure + ') && (' + childEnsure + ')');
            return $.tmplApplyMethods.appendContents.call(this, elem);
        },
        prependVars: function (elem) {
            var parentEnsure = $(this).data('ensure') || '1';
            var childEnsure = $(elem).data('ensure') || '1';
            $(this).data('ensure', '(' + childEnsure + ') && (' + parentEnsure + ')');
            return $.tmplApplyMethods.prependContents.call(this, elem);
        }
    }
});
},{"./crc32.js":1}],11:[function(require,module,exports){
var prefixedTransform = null;
function computePrefixedTransform() {
    var el = document.createElement('div');
    var prefixes = [
        'transform',
        'msTransform',
        'MozTransform',
        'WebkitTransform',
        'OTransform'
    ];
    var correctPrefix = null;
    _.each(prefixes, function (prefix) {
        if (typeof el.style[prefix] !== 'undefined') {
            correctPrefix = prefix;
        }
    });
    return correctPrefix;
}
var canUse3dTransform = null;
function computeCanUse3dTransform() {
    var el = document.createElement('div');
    var prefix = KhanUtil.getPrefixedTransform();
    el.style[prefix] = 'translateZ(0px)';
    return !!el.style[prefix];
}
$.extend(KhanUtil, {
    getPrefixedTransform: function () {
        prefixedTransform = prefixedTransform || computePrefixedTransform();
        return prefixedTransform;
    },
    getCanUse3dTransform: function () {
        if (canUse3dTransform == null) {
            canUse3dTransform = computeCanUse3dTransform();
        }
        return canUse3dTransform;
    }
});
},{}],12:[function(require,module,exports){
var objective_ = require('./objective_.js');
var kvector = require('./kvector.js');
require('./transform-helpers.js');
var PASS_TO_RAPHAEL = [
    'attr',
    'animate'
];
var WrappedDefaults = _.extend({
    transform: function (transformation) {
        var prefixedTransform = KhanUtil.getPrefixedTransform();
        this.wrapper.style[prefixedTransform] = transformation;
    },
    toFront: function () {
        var parentNode = this.wrapper.parentNode;
        if (parentNode) {
            parentNode.appendChild(this.wrapper);
        }
    },
    toBack: function () {
        var parentNode = this.wrapper.parentNode;
        if (parentNode.firstChild !== this.wrapper) {
            parentNode.insertBefore(this.wrapper, parentNode.firstChild);
        }
    },
    remove: function () {
        this.visibleShape.remove();
        $(this.wrapper).remove();
    },
    getMouseTarget: function () {
        return this.visibleShape[0];
    },
    moveTo: function (point) {
        var delta = kvector.subtract(this.graphie.scalePoint(point), this.graphie.scalePoint(this.initialPoint));
        var do3dTransform = KhanUtil.getCanUse3dTransform();
        var transformation = 'translateX(' + delta[0] + 'px) ' + 'translateY(' + delta[1] + 'px)' + (do3dTransform ? ' translateZ(0)' : '');
        this.transform(transformation);
    },
    hide: function () {
        this.visibleShape.hide();
    },
    show: function () {
        this.visibleShape.show();
    }
}, objective_.mapObjectFromArray(PASS_TO_RAPHAEL, function (attribute) {
    return function () {
        this.visibleShape[attribute].apply(this.visibleShape, arguments);
    };
}));
module.exports = WrappedDefaults;
},{"./kvector.js":7,"./objective_.js":8,"./transform-helpers.js":11}],13:[function(require,module,exports){
var WrappedDefaults = require('./wrapped-defaults.js');
var kvector = require('./kvector.js');
var DEFAULT_OPTIONS = {
    maxScale: 1,
    mouselayer: false
};
var WrappedEllipse = function (graphie, center, radii, options) {
    options = _.extend({}, DEFAULT_OPTIONS, options);
    _.extend(this, graphie.fixedEllipse(center, radii, options.maxScale), {
        graphie: graphie,
        initialPoint: center
    });
    if (options.mouselayer) {
        this.graphie.addToMouseLayerWrapper(this.wrapper);
    } else {
        this.graphie.addToVisibleLayerWrapper(this.wrapper);
    }
};
_.extend(WrappedEllipse.prototype, {
    animateTo: function (point, time, cb) {
        var delta = kvector.subtract(this.graphie.scalePoint(point), this.graphie.scalePoint(this.initialPoint));
        var do3dTransform = KhanUtil.getCanUse3dTransform();
        var self = this;
        var prevX = null;
        var prevY = null;
        $(this.wrapper).animate({
            cx: delta[0],
            cy: delta[1]
        }, {
            duration: time,
            step: function (now, fx) {
                prevX = fx.prop === 'cx' && now || prevX != null && prevX || fx.prop === 'cx' && fx.start;
                prevY = fx.prop === 'cy' && now || prevY != null && prevY || fx.prop === 'cy' && fx.start;
                var transformation = 'translateX(' + prevX + 'px) ' + 'translateY(' + prevY + 'px)' + (do3dTransform ? ' translateZ(0)' : '');
                self.transform(transformation);
                var unscaledPoint = self.graphie.unscalePoint(kvector.add(self.graphie.scalePoint(self.initialPoint), [
                    prevX,
                    prevY
                ]));
                cb && cb(unscaledPoint);
            }
        });
    }
}, WrappedDefaults);
module.exports = WrappedEllipse;
},{"./kvector.js":7,"./wrapped-defaults.js":12}],14:[function(require,module,exports){
var WrappedDefaults = require('./wrapped-defaults.js');
var kpoint = require('./kpoint.js');
var kvector = require('./kvector.js');
require('./transform-helpers.js');
var DEFAULT_OPTIONS = {
    thickness: 2,
    mouselayer: false
};
var WrappedLine = function (graphie, start, end, options) {
    options = _.extend({}, DEFAULT_OPTIONS, options);
    var initialStart = [
        graphie.range[0][0],
        0
    ];
    var initialEnd = [
        graphie.range[0][1],
        0
    ];
    _.extend(this, graphie.fixedLine(initialStart, initialEnd, options.thickness));
    _.extend(this, {
        graphie: graphie,
        initialPoint: graphie.scalePoint(initialStart),
        initialLength: kpoint.distanceToPoint(graphie.scalePoint(initialStart), graphie.scalePoint(initialEnd))
    });
    if (options.mouselayer) {
        this.graphie.addToMouseLayerWrapper(this.wrapper);
    } else {
        this.graphie.addToVisibleLayerWrapper(this.wrapper);
    }
    this.moveTo(start, end);
};
_.extend(WrappedLine.prototype, WrappedDefaults, {
    getMouseTarget: function () {
        return this.wrapper;
    },
    moveTo: function (start, end) {
        var scaledStart = this.graphie.scalePoint(start);
        var scaledEnd = this.graphie.scalePoint(end);
        var polarDiff = kvector.polarDegFromCart(kvector.subtract(scaledEnd, scaledStart));
        var lineLength = polarDiff[0];
        var angle = KhanUtil.bound(polarDiff[1]);
        var delta = kvector.subtract(scaledStart, this.initialPoint);
        var scale = KhanUtil.bound(lineLength / this.initialLength);
        var do3dTransform = KhanUtil.getCanUse3dTransform();
        var transformation = 'translateX(' + delta[0] + 'px) ' + 'translateY(' + delta[1] + 'px) ' + (do3dTransform ? 'translateZ(0) ' : '') + 'rotate(' + angle + 'deg) ' + 'scaleX(' + scale + ') scaleY(1)';
        this.transform(transformation);
    }
});
module.exports = WrappedLine;
},{"./kpoint.js":6,"./kvector.js":7,"./transform-helpers.js":11,"./wrapped-defaults.js":12}],15:[function(require,module,exports){
var WrappedDefaults = require('./wrapped-defaults.js');
var DEFAULT_OPTIONS = {
    center: null,
    createPath: null,
    mouselayer: false
};
var WrappedPath = function (graphie, points, options) {
    options = _.extend({}, DEFAULT_OPTIONS, options);
    _.extend(this, graphie.fixedPath(points, options.center, options.createPath));
    _.extend(this, {
        graphie: graphie,
        initialPoint: graphie.scalePoint(_.head(points))
    });
    if (options.mouselayer) {
        this.graphie.addToMouseLayerWrapper(this.wrapper);
    } else {
        this.graphie.addToVisibleLayerWrapper(this.wrapper);
    }
};
_.extend(WrappedPath.prototype, WrappedDefaults);
module.exports = WrappedPath;
},{"./wrapped-defaults.js":12}],16:[function(require,module,exports){
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

},{}]},{},[3]);
