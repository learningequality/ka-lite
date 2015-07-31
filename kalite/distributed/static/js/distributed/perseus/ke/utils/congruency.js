(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    commonAngles: [
        {
            deg: 15,
            rad: '\\frac{\\pi}{12}'
        },
        {
            deg: 30,
            rad: '\\frac{\\pi}{6}'
        },
        {
            deg: 45,
            rad: '\\frac{\\pi}{4}'
        },
        {
            deg: 60,
            rad: '\\frac{\\pi}{3}'
        },
        {
            deg: 90,
            rad: '\\frac{\\pi}{2}'
        },
        {
            deg: 120,
            rad: '\\frac{2\\pi}{3}'
        },
        {
            deg: 135,
            rad: '\\frac{3\\pi}{4}'
        },
        {
            deg: 150,
            rad: '\\frac{5\\pi}{6}'
        },
        {
            deg: 180,
            rad: '\\pi'
        },
        {
            deg: 210,
            rad: '\\frac{7\\pi}{6}'
        },
        {
            deg: 225,
            rad: '\\frac{5\\pi}{4}'
        },
        {
            deg: 240,
            rad: '\\frac{4\\pi}{3}'
        },
        {
            deg: 270,
            rad: '\\frac{3\\pi}{2}'
        },
        {
            deg: 300,
            rad: '\\frac{5\\pi}{3}'
        },
        {
            deg: 315,
            rad: '\\frac{7\\pi}{4}'
        },
        {
            deg: 330,
            rad: '\\frac{11\\pi}{6}'
        },
        {
            deg: 360,
            rad: '2\\pi'
        }
    ],
    toRadians: function (degrees) {
        return degrees * Math.PI / 180;
    },
    toDegrees: function (radians) {
        return radians * 180 / Math.PI;
    }
});
},{}],2:[function(require,module,exports){
require('./angles.js');
require('./interactive.js');
require('./graphie-helpers.js');
$.extend(KhanUtil, {
    addCongruency: function (options) {
        var congruency = $.extend(true, {
            x1: 0,
            x2: 10,
            y1: 0,
            y2: 3
        }, options);
        if (congruency.x1 > congruency.x2) {
            var hold = congruency.x1;
            congruency.x1 = congruency.x2;
            congruency.x2 = hold;
        }
        if (congruency.y1 > congruency.y2) {
            var hold = congruency.y1;
            congruency.y1 = congruency.y2;
            congruency.y2 = hold;
        }
        var graph = KhanUtil.currentGraph;
        congruency.lines = {};
        congruency.angles = {};
        congruency.points = {};
        congruency.getPoint = function (pt) {
            if (typeof pt === 'string') {
                return congruency.points[pt];
            } else {
                return pt;
            }
        };
        congruency.addPoint = function (name, position) {
            var point = {
                name: name,
                pos: position,
                connected: [],
                arcs: []
            };
            point.angleTo = function (p) {
                p = congruency.getPoint(p);
                return Math.atan2(p.pos[1] - point.pos[1], p.pos[0] - point.pos[0]);
            };
            congruency.points[name] = point;
            return point;
        };
        congruency.addLine = function (options) {
            var line = $.extend(true, {
                start: [
                    0,
                    0
                ],
                extend: false,
                clickable: false,
                state: 0,
                maxState: 1,
                tickDiff: 0.15,
                tickLength: 0.2,
                highlighted: false
            }, options);
            if (typeof line.start === 'string') {
                line.startPt = congruency.points[line.start];
                line.start = line.startPt.pos;
            }
            if (typeof line.end === 'string') {
                line.endPt = congruency.points[line.end];
                line.end = line.endPt.pos;
            }
            if (line.end != null) {
                line.radAngle = Math.atan2(line.end[1] - line.start[1], line.end[0] - line.start[0]);
                line.angle = KhanUtil.toDegrees(line.radAngle);
            } else if (line.angle != null) {
                line.radAngle = KhanUtil.toRadians(line.angle);
                line.end = [
                    Math.cos(line.radAngle) + line.start[0],
                    Math.sin(line.radAngle) + line.start[1]
                ];
            }
            line.slope = (line.end[1] - line.start[1]) / (line.end[0] - line.start[0]);
            line.slope = Math.max(-999999, Math.min(999999, line.slope));
            line.func = function (x) {
                return line.start[1] + line.slope * (x - line.start[0]);
            };
            line.invfunc = function (y) {
                var slope = line.slope === 0 ? 0.00001 : line.slope;
                return line.start[0] + (y - line.start[1]) / slope;
            };
            if (line.extend) {
                var order = line.start[0] < line.end[0];
                var left, right;
                var y1int = line.func(congruency.x1);
                if (y1int >= congruency.y1 && y1int <= congruency.y2) {
                    left = [
                        congruency.x1,
                        y1int
                    ];
                } else if (y1int > congruency.y2) {
                    left = [
                        line.invfunc(congruency.y2),
                        congruency.y2
                    ];
                } else {
                    left = [
                        line.invfunc(congruency.y1),
                        congruency.y1
                    ];
                }
                var y2int = line.func(congruency.x2);
                if (y2int >= congruency.y1 && y2int <= congruency.y2) {
                    right = [
                        congruency.x2,
                        y2int
                    ];
                } else if (y2int > congruency.y2) {
                    right = [
                        line.invfunc(congruency.y2),
                        congruency.y2
                    ];
                } else {
                    right = [
                        line.invfunc(congruency.y1),
                        congruency.y1
                    ];
                }
                if (order) {
                    line.start = left;
                    line.end = right;
                } else {
                    line.end = left;
                    line.start = right;
                }
            }
            if (line.placeAtStart != null) {
                line.startPt = congruency.addPoint(line.placeAtStart, line.start);
            }
            if (line.placeAtEnd != null) {
                line.endPt = congruency.addPoint(line.placeAtEnd, line.end);
            }
            if (line.startPt != null && line.endPt != null) {
                congruency.lines[line.startPt.name + line.endPt.name] = line;
                congruency.lines[line.endPt.name + line.startPt.name] = line;
            }
            if (line.startPt != null && line.endPt != null) {
                line.startPt.connected.push(line.endPt);
                line.endPt.connected.push(line.startPt);
            }
            line.draw = function () {
                if (this.line != null) {
                    this.line.remove();
                }
                this.line = graph.raphael.set();
                var startDiff = this.tickDiff * (this.state - 1) / 2;
                var direction = [
                    Math.cos(this.radAngle),
                    Math.sin(this.radAngle)
                ];
                var normalDir = [
                    -direction[1] * this.tickLength,
                    direction[0] * this.tickLength
                ];
                var midpoint = [
                    (this.start[0] + this.end[0]) / 2,
                    (this.start[1] + this.end[1]) / 2
                ];
                var startPos = [
                    midpoint[0] - startDiff * direction[0],
                    midpoint[1] - startDiff * direction[1]
                ];
                for (var curr = 0; curr < this.state; curr += 1) {
                    var currPos = [
                        startPos[0] + curr * direction[0] * this.tickDiff,
                        startPos[1] + curr * direction[1] * this.tickDiff
                    ];
                    var start = [
                        currPos[0] + normalDir[0],
                        currPos[1] + normalDir[1]
                    ];
                    var end = [
                        currPos[0] - normalDir[0],
                        currPos[1] - normalDir[1]
                    ];
                    this.line.push(graph.line(start, end));
                }
                this.line.push(graph.line(this.start, this.end));
                if (direction[1] === 0) {
                    ParallelLineMarkers(this.end[0] - 0.5, this.end[1]);
                }
                this.line.attr(this.point.normalStyle);
                this.point.visibleShape = this.line;
            };
            var pointPos = [
                (line.start[0] + line.end[0]) / 2,
                (line.start[1] + line.end[1]) / 2
            ];
            line.point = graph.addMovablePoint({ coord: pointPos });
            line.point.onMove = function (x, y) {
                return false;
            };
            line.point.mouseTarget.attr({ r: graph.scale[0] * 0.7 });
            line.point.visibleShape.remove();
            line.normal = {
                stroke: 'black',
                'stroke-width': 2
            };
            line.hover = {
                stroke: 'black',
                'stroke-width': 3
            };
            line.highlight = {};
            line.setStyles = function () {
                if (this.highlighted) {
                    this.point.normalStyle = this.highlight;
                    this.point.highlightStyle = this.highlight;
                } else {
                    this.point.normalStyle = this.normal;
                    this.point.highlightStyle = this.hover;
                }
            };
            line.setSelectedStyle = function (style) {
                $.extend(true, this.hover, style);
                this.draw();
            };
            line.setUnselectedStyle = function (style) {
                $.extend(true, this.normal, style);
                this.draw();
            };
            line.setHighlighted = function (style) {
                $.extend(true, this.highlight, style);
                this.highlighted = true;
                this.setStyles();
                this.draw();
            };
            line.unsetHighlighted = function () {
                this.highlighted = false;
                this.setStyles();
                this.draw();
            };
            line.setStyles();
            line.draw();
            line.setState = function (state) {
                this.state = state;
                this.draw();
            };
            $(line.point.mouseTarget.getMouseTarget()).bind('vmouseup', function (event) {
                line.setState(line.state === line.maxState ? 0 : line.state + 1);
            });
            line.stick = function () {
                line.point.mouseTarget.remove();
            };
            if (!line.clickable) {
                line.stick();
            }
            return line;
        };
        congruency.addAngle = function (name, options) {
            var angle = $.extend({
                radius: 0.7,
                state: 0,
                maxState: 1,
                shown: false,
                clickable: true,
                arcDiff: 0.15,
                highlighted: false
            }, options);
            angle.center = name[1];
            angle.left = name[0];
            angle.right = name[2];
            angle.centerPt = congruency.getPoint(angle.center);
            angle.leftPt = congruency.getPoint(angle.left);
            angle.rightPt = congruency.getPoint(angle.right);
            angle.pos = angle.centerPt.pos;
            angle.start = KhanUtil.toDegrees(angle.centerPt.angleTo(angle.leftPt));
            angle.end = KhanUtil.toDegrees(angle.centerPt.angleTo(angle.rightPt));
            while (angle.start > angle.end) {
                angle.start -= 360;
            }
            angle.angle = angle.end - angle.start;
            var aveAngle = KhanUtil.toRadians((angle.start + angle.end) / 2);
            var pointPos = angle.pos.slice();
            pointPos[0] += Math.cos(aveAngle) * angle.radius;
            pointPos[1] += Math.sin(aveAngle) * angle.radius;
            angle.point = graph.addMovablePoint({ coord: pointPos });
            angle.point.onMove = function (x, y) {
                return false;
            };
            $(angle.point.mouseTarget.getMouseTarget()).css('cursor', 'pointer');
            var pointRadius = Math.sin(KhanUtil.toRadians(angle.angle) / 2) * angle.radius * graph.scale[0];
            angle.point.mouseTarget.attr({ r: pointRadius });
            angle.point.visibleShape.remove();
            angle.unselected = {
                stroke: KhanUtil.GRAY,
                'stroke-width': 2,
                opacity: 0.1
            };
            angle.unselectedHover = {
                stroke: KhanUtil.GRAY,
                'stroke-width': 2,
                opacity: 0.4
            };
            angle.selected = {
                stroke: KhanUtil.BLUE,
                'stroke-width': 3,
                opacity: 0.9
            };
            angle.selectedHover = {
                stroke: KhanUtil.BLUE,
                'stroke-width': 3,
                opacity: 1
            };
            angle.highlight = {};
            angle.draw = function () {
                if (this.arc != null) {
                    this.arc.remove();
                }
                var arcs = this.state === 0 ? 1 : this.state;
                var startRad = this.radius - this.arcDiff * (arcs - 1) / 2;
                this.arc = graph.raphael.set();
                for (var curr = 0; curr < arcs; curr += 1) {
                    var currRad = startRad + this.arcDiff * curr;
                    this.arc.push(graph.arc(this.pos, currRad, this.start, this.end));
                }
                this.point.visibleShape = this.arc;
                this.arc.attr(this.point.normalStyle);
            };
            angle.setStyles = function () {
                if (this.highlighted) {
                    this.point.normalStyle = this.highlight;
                    this.point.highlightStyle = this.highlight;
                } else if (this.state === 0) {
                    this.point.normalStyle = this.unselected;
                    this.point.highlightStyle = this.unselectedHover;
                } else {
                    this.point.normalStyle = this.selected;
                    this.point.highlightStyle = this.selectedHover;
                }
            };
            angle.setState = function (state) {
                this.state = state;
                this.setStyles();
                this.draw();
            };
            angle.setStyles();
            angle.draw();
            $(angle.point.mouseTarget.getMouseTarget()).bind('vmouseup', function (event) {
                angle.setState(angle.state === angle.maxState ? 0 : angle.state + 1);
            });
            angle.stick = function () {
                $(this.point.mouseTarget.getMouseTarget()).unbind();
                this.point.mouseTarget.remove();
            };
            if (!angle.clickable) {
                angle.stick();
            }
            angle.setUnselectedStyle = function (style) {
                $.extend(true, this.unselected, style);
                $.extend(true, this.unselectedHover, style);
                this.draw();
            };
            angle.setSelectedStyle = function (style) {
                $.extend(true, this.selected, style);
                $.extend(true, this.selectedHover, style);
                this.draw();
            };
            angle.setHighlighted = function (style) {
                $.extend(true, this.highlight, style);
                this.highlighted = true;
                this.setStyles();
                this.draw();
            };
            angle.unsetHighlighted = function () {
                this.highlighted = false;
                this.setStyles();
                this.draw();
            };
            var name = angle.left + angle.center + angle.right;
            congruency.angles[name] = angle;
            name = angle.right + angle.center + angle.left;
            congruency.angles[name] = angle;
            return angle;
        };
        congruency.addAngles = function (point, options) {
            var pt = congruency.getPoint(point);
            var sortConnected = _.sortBy(pt.connected, function (cpt) {
                return pt.angleTo(cpt);
            });
            var numAngs = sortConnected.length;
            for (var i = 0; i < numAngs; i += 1) {
                var pt1 = sortConnected[i];
                var pt2 = sortConnected[(i + 1) % numAngs];
                var ang1 = pt.angleTo(pt1);
                var ang2 = pt.angleTo(pt2);
                if (i + 1 === numAngs) {
                    ang2 += Math.PI * 2;
                }
                if (ang2 - ang1 >= Math.PI) {
                    continue;
                }
                congruency.addAngle(pt1.name + pt.name + pt2.name, options);
            }
        };
        congruency.intersect = function (line1, line2, pointName, addAngles) {
            if (line1.slope === line2.slope) {
                return false;
            }
            var point = null;
            var coord = [];
            coord[0] = (line1.slope * line1.start[0] - line2.slope * line2.start[0] + line2.start[1] - line1.start[1]) / (line1.slope - line2.slope);
            coord[1] = line1.func(coord[0]);
            point = congruency.addPoint(pointName, coord);
            point.connected.push(line1.startPt);
            point.connected.push(line1.endPt);
            point.connected.push(line2.startPt);
            point.connected.push(line2.endPt);
            if (addAngles) {
                congruency.addAngles(point.name);
            }
        };
        congruency.addLabel = function (point, position) {
            var p = congruency.getPoint(point);
            graph.label(p.pos, point, position);
        };
        congruency.getGuess = function () {
            var guess = {};
            _.each(congruency.lines, function (line, name) {
                guess[name] = line.state;
            });
            _.each(congruency.angles, function (angle, name) {
                guess[name] = angle.state;
            });
            return guess;
        };
        congruency.showGuess = function (guess) {
            _.each(guess, function (t, g) {
                if (g.length === 2) {
                    congruency.lines[g].setState(t);
                } else {
                    congruency.angles[g].setState(t);
                }
            });
        };
        return congruency;
    }
});
},{"./angles.js":1,"./graphie-helpers.js":5,"./interactive.js":7}],3:[function(require,module,exports){
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
},{}],4:[function(require,module,exports){
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
},{}],5:[function(require,module,exports){
require('./math-format.js');
window.numberLine = function (start, end, step, x, y, denominator) {
    step = step || 1;
    x = x || 0;
    y = y || 0;
    var decPlaces = (step + '').length - (step + '').indexOf('.') - 1;
    if ((step + '').indexOf('.') < 0) {
        decPlaces = 0;
    }
    var graph = KhanUtil.currentGraph;
    var set = graph.raphael.set();
    set.push(graph.line([
        x,
        y
    ], [
        x + end - start,
        y
    ]));
    set.labels = [];
    for (var i = 0; i <= end - start; i += step) {
        set.push(graph.line([
            x + i,
            y - 0.2
        ], [
            x + i,
            y + 0.2
        ]));
        if (denominator) {
            var base = KhanUtil.roundTowardsZero(start + i + 0.001);
            var frac = start + i - base;
            var lab = base;
            if (!(Math.abs(Math.round(frac * denominator)) === denominator || Math.round(frac * denominator) === 0)) {
                if (base === 0) {
                    lab = KhanUtil.fraction(Math.round(frac * denominator), denominator, false, false, true);
                } else {
                    lab = base + '\\frac{' + Math.abs(Math.round(frac * denominator)) + '}{' + denominator + '}';
                }
            }
            var label = graph.label([
                x + i,
                y - 0.2
            ], '\\small{' + lab + '}', 'below', { labelDistance: 3 });
            set.labels.push(label);
            set.push(label);
        } else {
            var label = graph.label([
                x + i,
                y - 0.2
            ], '\\small{' + KhanUtil.localeToFixed(start + i, decPlaces) + '}', 'below', { labelDistance: 3 });
            set.labels.push(label);
            set.push(label);
        }
    }
    return set;
};
window.piechart = function (divisions, colors, radius, strokeColor, x, y) {
    var graph = KhanUtil.currentGraph;
    var set = graph.raphael.set();
    var arcColor = strokeColor || 'none';
    var lineColor = strokeColor || '#fff';
    x = x || 0;
    y = y || 0;
    var sum = 0;
    $.each(divisions, function (i, slice) {
        sum += slice;
    });
    var partial = 0;
    $.each(divisions, function (i, slice) {
        if (slice === sum) {
            set.push(graph.ellipse([
                x,
                y
            ], [
                radius,
                radius
            ], {
                stroke: arcColor,
                fill: colors[i]
            }));
        } else {
            set.push(graph.arc([
                x,
                y
            ], radius, partial * 360 / sum, (partial + slice) * 360 / sum, true, {
                stroke: arcColor,
                fill: colors[i]
            }));
        }
        partial += slice;
    });
    for (var i = 0; i < sum; i++) {
        var p = graph.polar(radius, i * 360 / sum);
        set.push(graph.line([
            x,
            y
        ], [
            x + p[0],
            y + p[1]
        ], { stroke: lineColor }));
    }
    return set;
};
window.shadeRect = function (x, y, width, height, pad) {
    var graph = KhanUtil.currentGraph;
    var set = graph.raphael.set();
    var x2 = graph.range[0][0];
    var y1 = graph.range[1][0];
    var y2 = graph.range[1][1];
    var x1 = x2 - (y2 - y1) * graph.scale[1] / graph.scale[0];
    var step = 8 / graph.scale[0];
    var xpad = (pad || 0) / graph.scale[0];
    var ypad = (pad || 0) / graph.scale[1];
    while (x1 < graph.range[0][1]) {
        set.push(graph.line([
            x1,
            y1
        ], [
            x2,
            y2
        ], {
            clipRect: [
                [
                    x + xpad,
                    y + ypad
                ],
                [
                    width - 2 * xpad,
                    height - 2 * ypad
                ]
            ]
        }));
        x1 += step;
        x2 += step;
    }
    return set;
};
window.rectchart = function (divisions, fills, y, strokes, shading) {
    var graph = KhanUtil.currentGraph;
    var set = graph.raphael.set();
    y = y || 0;
    var sum = 0;
    $.each(divisions, function (i, slice) {
        sum += slice;
    });
    var unit = graph.unscaleVector([
        1,
        1
    ]);
    var partial = 0;
    $.each(divisions, function (i, slice) {
        var fill = fills[i];
        var stroke = strokes && strokes[i] || fill;
        for (var j = 0; j < slice; j++) {
            var x = partial / sum, w = 1 / sum;
            set.push(graph.path([
                [
                    x + 2 * unit[0],
                    y + 2 * unit[1]
                ],
                [
                    x + w - 2 * unit[0],
                    y + 2 * unit[1]
                ],
                [
                    x + w - 2 * unit[0],
                    y + 1 - 2 * unit[1]
                ],
                [
                    x + 2 * unit[0],
                    y + 1 - 2 * unit[1]
                ],
                true
            ], {
                stroke: stroke,
                fill: fill
            }));
            if (shading && shading[i]) {
                graph.style({
                    stroke: '#000',
                    strokeWidth: 2,
                    strokeOpacity: 0.5,
                    fillOpacity: 0,
                    fill: null
                }, function () {
                    set.push(shadeRect(x + 2 * unit[0], y + 2 * unit[1], w - 4 * unit[0], 1 - 4 * unit[1], strokes && strokes[i] ? 1 : -1));
                });
            }
            partial += 1;
        }
    });
    return set;
};
window.Parabola = function (lc, x, y) {
    var leadingCoefficient = lc;
    var x1 = x;
    var y1 = y;
    var raphaelObjects = [];
    this.graphieFunction = function (x) {
        return leadingCoefficient * (x - x1) * (x - x1) + y1;
    };
    this.plot = function (fShowFocusDirectrix) {
        var graph = KhanUtil.currentGraph;
        raphaelObjects.push(graph.plot(this.graphieFunction, [
            -10,
            10
        ]));
        if (fShowFocusDirectrix) {
            var focusX = this.getFocusX();
            var focusY = this.getFocusY();
            var directrixK = this.getDirectrixK();
            graph.style({ fill: '#6495ED' }, function () {
                raphaelObjects.push(graph.circle([
                    focusX,
                    focusY
                ], 0.1));
                raphaelObjects.push(graph.line([
                    -10,
                    directrixK
                ], [
                    10,
                    directrixK
                ]));
            });
        }
    };
    this.redraw = function (fShowFocusDirectrix) {
        $.each(raphaelObjects, function (i, el) {
            el.remove();
        });
        raphaelObjects = [];
        this.plot(fShowFocusDirectrix);
    };
    this.update = function (newLC, newX, newY) {
        leadingCoefficient = newLC;
        x1 = newX;
        y1 = newY;
    };
    this.delta = function (deltaLC, deltaX, deltaY) {
        this.update(leadingCoefficient + deltaLC, x1 + deltaX, y1 + deltaY);
    };
    this.deltaFocusDirectrix = function (deltaX, deltaY, deltaK) {
        var focusY = this.getFocusY() + deltaY;
        var k = this.getDirectrixK() + deltaK;
        if (focusY === k) {
            focusY += deltaY;
            k += deltaK;
        }
        var newVertexY = (focusY + k) / 2;
        var newLeadingCoefficient = 1 / (2 * (focusY - k));
        this.update(newLeadingCoefficient, this.getVertexX() + deltaX, newVertexY);
    };
    this.getVertexX = function () {
        return x1;
    };
    this.getVertexY = function () {
        return y1;
    };
    this.getLeadingCoefficient = function () {
        return leadingCoefficient;
    };
    this.getFocusX = function () {
        return x1;
    };
    this.getFocusY = function () {
        return y1 + 1 / (4 * leadingCoefficient);
    };
    this.getDirectrixK = function () {
        return y1 - 1 / (4 * leadingCoefficient);
    };
};
window.redrawParabola = function (fShowFocusDirectrix) {
    var graph = KhanUtil.currentGraph;
    var storage = graph.graph;
    var currParabola = storage.currParabola;
    currParabola.redraw(fShowFocusDirectrix);
    var leadingCoefficient = currParabola.getLeadingCoefficient();
    var vertexX = currParabola.getVertexX();
    var vertexY = currParabola.getVertexY();
    if (fShowFocusDirectrix) {
        $('#focus-x-label').html('<code>' + currParabola.getFocusX() + '</code>').runModules();
        $('#focus-y-label').html('<code>' + KhanUtil.localeToFixed(currParabola.getFocusY(), 2) + '</code>').runModules();
        $('#directrix-label').html('<code>' + 'y = ' + KhanUtil.localeToFixed(currParabola.getDirectrixK(), 2) + '</code>').runModules();
    } else {
        var equation = 'y - ' + vertexY + '=' + leadingCoefficient + '(x - ' + vertexX + ')^{2}';
        equation = KhanUtil.cleanMath(equation);
        $('#equation-label').html('<code>' + equation + '</code>').runModules();
    }
    $('#leading-coefficient input').val(leadingCoefficient);
    $('#vertex-x input').val(vertexX);
    $('#vertex-y input').val(vertexY);
};
window.updateParabola = function (deltaA, deltaX, deltaY, fShowFocusDirectrix) {
    KhanUtil.currentGraph.graph.currParabola.delta(deltaA, deltaX, deltaY);
    redrawParabola(fShowFocusDirectrix);
};
window.updateFocusDirectrix = function (deltaX, deltaY, deltaK) {
    KhanUtil.currentGraph.graph.currParabola.deltaFocusDirectrix(deltaX, deltaY, deltaK);
    redrawParabola(true);
};
window.ParallelLineMarkers = function (x, y, rotation) {
    var graph = KhanUtil.currentGraph;
    rotation = rotation || 0;
    var s = 8 / graph.scaleVector([
        1,
        1
    ])[0];
    var x2 = x + 0.75 * s * Math.cos(rotation);
    var y2 = y + 0.75 * s * Math.sin(rotation);
    var dx1 = s * Math.cos(rotation + Math.PI / 4);
    var dy1 = s * Math.sin(rotation + Math.PI / 4);
    var dx2 = s * Math.cos(rotation - Math.PI / 4);
    var dy2 = s * Math.sin(rotation - Math.PI / 4);
    graph.path([
        [
            x - dx1,
            y - dy1
        ],
        [
            x,
            y
        ],
        [
            x - dx2,
            y - dy2
        ]
    ]);
    graph.path([
        [
            x2 - dx1,
            y2 - dy1
        ],
        [
            x2,
            y2
        ],
        [
            x2 - dx2,
            y2 - dy2
        ]
    ]);
};
window.ParallelLines = function (x, y, length, distance, rotation) {
    var lowerIntersection;
    var upperIntersection;
    var anchorAngle;
    var dx1 = distance / 2 * Math.cos(rotation + Math.PI / 2);
    var dy1 = distance / 2 * Math.sin(rotation + Math.PI / 2);
    var dx2 = length / 2 * Math.cos(rotation);
    var dy2 = length / 2 * Math.sin(rotation);
    var labels = {};
    this.draw = function () {
        var graph = KhanUtil.currentGraph;
        graph.line([
            x + dx1 + dx2,
            y + dy1 + dy2
        ], [
            x + dx1 - dx2,
            y + dy1 - dy2
        ]);
        graph.line([
            x - dx1 + dx2,
            y - dy1 + dy2
        ], [
            x - dx1 - dx2,
            y - dy1 - dy2
        ]);
    };
    this.drawMarkers = function (position) {
        var graph = KhanUtil.currentGraph;
        var pmarkX = 0;
        var pmarkY = 0;
        var s = 120 / graph.scaleVector([
            1,
            1
        ])[0];
        if (position === 'right' || position >= 40 && position <= 140) {
            pmarkX += s * Math.cos(rotation);
            pmarkY += s * Math.sin(rotation);
        } else if (position === 'left') {
            pmarkX -= s * Math.cos(rotation);
            pmarkY -= s * Math.sin(rotation);
        }
        ParallelLineMarkers(x + dx1 + pmarkX, y + dy1 + pmarkY, rotation);
        ParallelLineMarkers(x - dx1 + pmarkX, y - dy1 + pmarkY, rotation);
    };
    this.drawTransverse = function (angleDeg) {
        var graph = KhanUtil.currentGraph;
        var angleRad = KhanUtil.toRadians(angleDeg);
        var cosAngle = Math.cos(rotation + angleRad);
        var sinAngle = Math.sin(rotation + angleRad);
        var dx3 = 0.5 * length * cosAngle;
        var dy3 = 0.5 * length * sinAngle;
        graph.line([
            x + dx3,
            y + dy3
        ], [
            x - dx3,
            y - dy3
        ]);
        var hypot = 0.5 * distance / Math.cos(Math.PI / 2 - angleRad);
        var dx4 = hypot * cosAngle;
        var dy4 = hypot * sinAngle;
        upperIntersection = [
            x + dx4,
            y + dy4
        ];
        lowerIntersection = [
            x - dx4,
            y - dy4
        ];
        anchorAngle = angleDeg;
    };
    function labelAngle(index, coords, angles, color, text) {
        var graph = KhanUtil.currentGraph;
        var measure = angles[1] - angles[0];
        var bisect = KhanUtil.toRadians(angles[0] + measure / 2);
        var radius = 0.7;
        if (measure < 70) {
            radius /= Math.cos(KhanUtil.toRadians(70 - measure));
        }
        var dx = radius * Math.cos(bisect);
        var dy = radius * Math.sin(bisect);
        var placement = 'center';
        if (typeof text === 'boolean') {
            text = angles[1] - angles[0] + '^\\circ';
        }
        if (text.length > 10 && Math.abs(dx) > 0.25) {
            dx *= 0.6;
            dy *= 0.8;
            placement = dx > 0 ? 'right' : 'left';
        }
        if (labels[index]) {
            labels[index].remove();
        }
        labels[index] = graph.label([
            coords[0] + dx,
            coords[1] + dy
        ], text, placement, { color: color });
    }
    this.drawAngle = function (index, label, color) {
        var graph = KhanUtil.currentGraph;
        var radius = 0.4;
        color = color || KhanUtil.BLUE;
        index = (index + 8) % 8;
        var args = index < 4 ? [
            lowerIntersection,
            radius
        ] : [
            upperIntersection,
            radius
        ];
        var angles = [
            KhanUtil.toDegrees(rotation),
            KhanUtil.toDegrees(rotation)
        ];
        switch (index % 4) {
        case 0:
            angles[1] += anchorAngle;
            break;
        case 1:
            angles[0] += anchorAngle;
            angles[1] += 180;
            break;
        case 2:
            angles[0] += 180;
            angles[1] += 180 + anchorAngle;
            break;
        case 3:
            angles[0] += 180 + anchorAngle;
            angles[1] += 360;
            break;
        }
        $.merge(args, angles);
        graph.style({ stroke: color }, function () {
            if (!labels[index]) {
                graph.arc.apply(graph, args);
            }
            if (label) {
                labelAngle(index, args[0], angles, color, label);
            }
        });
    };
    this.drawVerticalAngle = function (index, label, color) {
        index = (index + 8) % 8;
        var vert = (index + 2) % 4;
        if (index >= 4) {
            vert += 4;
        }
        this.drawAngle(vert, label, color);
    };
    this.drawAdjacentAngles = function (index, label, color) {
        index = (index + 8) % 8;
        var adj1 = (index + 1) % 4;
        var adj2 = (index + 3) % 4;
        if (index >= 4) {
            adj1 += 4;
            adj2 += 4;
        }
        this.drawAngle(adj1, label, color);
        this.drawAngle(adj2, label, color);
    };
};
window.drawComplexChart = function (radius, denominator) {
    var graph = KhanUtil.currentGraph;
    var safeRadius = radius * Math.sqrt(2);
    var color = '#ddd';
    graph.style({ strokeWidth: 1 });
    for (var i = 1; i <= safeRadius; i++) {
        graph.circle([
            0,
            0
        ], i, {
            fill: 'none',
            stroke: color
        });
    }
    for (var i = 0; i < denominator; i++) {
        var angle = i * 2 * Math.PI / denominator;
        if (denominator % 4 === 0 && i % (denominator / 4) !== 0) {
            graph.line([
                0,
                0
            ], [
                Math.sin(angle) * safeRadius,
                Math.cos(angle) * safeRadius
            ], { stroke: color });
        }
    }
    graph.label([
        radius,
        0.5
    ], 'Re', 'left');
    graph.label([
        0.5,
        radius - 1
    ], 'Im', 'right');
};
window.ComplexPolarForm = function (angleDenominator, maxRadius, euler) {
    var denominator = angleDenominator;
    var maximumRadius = maxRadius;
    var angle = 0, radius = 1;
    var circle;
    var useEulerForm = euler;
    this.update = function (newAngle, newRadius) {
        angle = newAngle;
        while (angle < 0) {
            angle += denominator;
        }
        angle %= denominator;
        radius = Math.max(1, Math.min(newRadius, maximumRadius));
        this.redraw();
    };
    this.delta = function (deltaAngle, deltaRadius) {
        this.update(angle + deltaAngle, radius + deltaRadius);
    };
    this.getAngleNumerator = function () {
        return angle;
    };
    this.getAngleDenominator = function () {
        return denominator;
    };
    this.getAngle = function () {
        return angle * 2 * Math.PI / denominator;
    };
    this.getRadius = function () {
        return radius;
    };
    this.getRealPart = function () {
        return Math.cos(this.getAngle()) * radius;
    };
    this.getImaginaryPart = function () {
        return Math.sin(this.getAngle()) * radius;
    };
    this.getUseEulerForm = function () {
        return useEulerForm;
    };
    this.plot = function () {
        circle = KhanUtil.currentGraph.circle([
            this.getRealPart(),
            this.getImaginaryPart()
        ], 1 / 4, {
            fill: KhanUtil.ORANGE,
            stroke: 'none'
        });
    };
    this.redraw = function () {
        if (circle) {
            circle.remove();
        }
        this.plot();
    };
};
window.updateComplexPolarForm = function (deltaAngle, deltaRadius) {
    KhanUtil.currentGraph.graph.currComplexPolar.delta(deltaAngle, deltaRadius);
    redrawComplexPolarForm();
};
window.redrawComplexPolarForm = function (angle, radius) {
    var graph = KhanUtil.currentGraph;
    var storage = graph.graph;
    var point = storage.currComplexPolar;
    point.redraw();
    if (typeof radius === 'undefined') {
        radius = point.getRadius();
    }
    if (typeof angle === 'undefined') {
        angle = point.getAngleNumerator();
    }
    angle *= 2 * Math.PI / point.getAngleDenominator();
    var equation = KhanUtil.polarForm(radius, angle, point.getUseEulerForm());
    $('#number-label').html('<code>' + equation + '</code>').runModules();
    $('#current-radius').html('<code>' + radius + '</code>').runModules();
    $('#current-angle').html('<code>' + KhanUtil.piFraction(angle, true) + '</code>').runModules();
};
window.labelDirection = function (angle) {
    angle = angle % 360;
    if (angle === 0) {
        return 'right';
    } else if (angle > 0 && angle < 90) {
        return 'above right';
    } else if (angle === 90) {
        return 'above';
    } else if (angle > 90 && angle < 180) {
        return 'above left';
    } else if (angle === 180) {
        return 'left';
    } else if (angle > 180 && angle < 270) {
        return 'below left';
    } else if (angle === 270) {
        return 'below';
    } else if (angle > 270 && angle < 360) {
        return 'below right';
    }
};
window.curvyArrow = function (center, radius, arcOrientation, arrowDirection, styles) {
    styles = styles || {};
    var graph = KhanUtil.currentGraph;
    var set = graph.raphael.set();
    var angles;
    if (arcOrientation === 'left') {
        angles = [
            90,
            270
        ];
    } else if (arcOrientation === 'right') {
        angles = [
            270,
            90
        ];
    } else if (arcOrientation === 'top') {
        angles = [
            0,
            180
        ];
    } else if (arcOrientation === 'bottom') {
        angles = [
            180,
            0
        ];
    }
    angles.push(styles);
    var arcArgs = [
        center,
        radius
    ].concat(angles);
    set.push(graph.arc.apply(graph, arcArgs));
    var offset = graph.unscaleVector([
        1,
        1
    ]);
    var from = _.clone(center);
    var to = _.clone(center);
    if (arcOrientation === 'left' || arcOrientation === 'right') {
        var left = arcOrientation === 'left';
        from[1] = to[1] = to[1] + radius * (arrowDirection === left ? 1 : -1);
        to[0] = from[0] + offset[0] * (left ? 1 : -1);
    } else {
        var bottom = arcOrientation === 'bottom';
        from[0] = to[0] = to[0] + radius * (arrowDirection === bottom ? 1 : -1);
        to[1] = from[1] + offset[1] * (bottom ? 1 : -1);
    }
    set.push(graph.line(from, to, _.extend({ arrows: '->' }, styles)));
    return set;
};
window.curlyBrace = function (startPointGraph, endPointGraph) {
    var graph = KhanUtil.currentGraph;
    var startPoint = graph.scalePoint(startPointGraph);
    var endPoint = graph.scalePoint(endPointGraph);
    var angle = KhanUtil.findAngle(endPoint, startPoint);
    var length = KhanUtil.getDistance(endPoint, startPoint);
    var midPoint = _.map(startPoint, function (start, i) {
        return (start + endPoint[i]) / 2;
    });
    var specialLen = 16 * 2 + 13 * 2;
    if (length < specialLen) {
        throw new Error('Curly brace length is too short.');
    }
    var straight = (length - specialLen) / 2;
    var half = length / 2;
    var firstHook = 'c 1 -3 6 -5 10 -6' + 'c 0 0 3 -1 6 -1';
    var secondHook = 'c 3 1 6 1 6 1' + 'c 4 1 9 3 10 6';
    var straightPart = 'l ' + straight + ' 0';
    var firstMiddle = 'c 5 0 10 -3 10 -3' + 'l 3 -4';
    var secondMiddle = 'l 3 4' + 'c 0 0 5 3 10 3';
    var path = [
        'M -' + half + ' 0',
        firstHook,
        straightPart,
        firstMiddle,
        secondMiddle,
        straightPart,
        secondHook
    ].join('');
    var brace = graph.raphael.path(path);
    brace.rotate(angle);
    brace.translate(midPoint[0], midPoint[1]);
    return brace;
};
},{"./math-format.js":12}],6:[function(require,module,exports){
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
},{"./kpoint.js":10,"./kvector.js":11,"./tex.js":15,"./tmpl.js":16}],7:[function(require,module,exports){
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
},{"../third_party/jquery.mobile.vmouse.js":22,"./graphie.js":6,"./kline.js":8,"./kpoint.js":10,"./kvector.js":11,"./wrapped-ellipse.js":19,"./wrapped-line.js":20,"./wrapped-path.js":21}],8:[function(require,module,exports){
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
},{"./knumber.js":9,"./kpoint.js":10}],9:[function(require,module,exports){
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
},{}],10:[function(require,module,exports){
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
},{"./knumber.js":9,"./kvector.js":11}],11:[function(require,module,exports){
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
},{"./knumber.js":9}],12:[function(require,module,exports){
require('./math.js');
require('./expressions.js');
$.extend(KhanUtil, {
    negParens: function (n, color) {
        var n2 = color ? '\\' + color + '{' + n + '}' : n;
        return n < 0 ? '(' + n2 + ')' : n2;
    },
    decimalFraction: function (num, defraction, reduce, small, parens) {
        var f = KhanUtil.toFraction(num);
        return KhanUtil.fraction(f[0], f[1], defraction, reduce, small, parens);
    },
    reduce: function (n, d) {
        var gcd = KhanUtil.getGCD(n, d);
        n = n / gcd;
        d = d / gcd;
        return [
            n,
            d
        ];
    },
    toFractionTex: function (n, dfrac) {
        var f = KhanUtil.toFraction(n);
        if (f[1] === 1) {
            return f[0];
        } else {
            return (n < 0 ? '-' : '') + '\\' + (dfrac ? 'd' : '') + 'frac{' + Math.abs(f[0]) + '}{' + Math.abs(f[1]) + '}';
        }
    },
    fraction: function (n, d, defraction, reduce, small, parens) {
        var frac = function (n, d) {
            return (small ? '\\frac' : '\\dfrac') + '{' + n + '}{' + d + '}';
        };
        var neg = n * d < 0;
        var sign = neg ? '-' : '';
        n = Math.abs(n);
        d = Math.abs(d);
        if (reduce) {
            var gcd = KhanUtil.getGCD(n, d);
            n = n / gcd;
            d = d / gcd;
        }
        defraction = defraction && (n === 0 || d === 0 || d === 1);
        parens = parens && (!defraction || neg);
        var begin = parens ? '\\left(' : '';
        var end = parens ? '\\right)' : '';
        var main;
        if (defraction) {
            if (n === 0) {
                main = '0';
            } else if (d === 0) {
                main = '\\text{undefined}';
            } else if (d === 1) {
                main = sign + n;
            }
        } else {
            main = sign + frac(n, d);
        }
        return begin + main + end;
    },
    mixedFractionFromImproper: function (n, d, defraction, reduce, small, parens) {
        return KhanUtil.mixedFraction(Math.floor(n / d), n % d, d, defraction, reduce, small, parens);
    },
    mixedFraction: function (number, n, d, defraction, reduce, small, parens) {
        var wholeNum = number ? number : 0;
        var numerator = n ? n : 0;
        var denominator = d ? d : 1;
        if (wholeNum < 0 && numerator < 0) {
            throw 'NumberFormatException: Both integer portion and fraction cannot both be negative.';
        }
        if (denominator < 0) {
            throw 'NumberFormatException: Denominator cannot be be negative.';
        }
        if (denominator === 0) {
            throw 'NumberFormatException: Denominator cannot be be 0.';
        }
        if (reduce) {
            if (wholeNum < 0) {
                wholeNum -= Math.floor(numerator / denominator);
            } else {
                wholeNum += Math.floor(numerator / denominator);
            }
            numerator = numerator % denominator;
        }
        if (wholeNum !== 0 && numerator !== 0) {
            return wholeNum + ' ' + KhanUtil.fraction(n, d, defraction, reduce, small, parens);
        } else if (wholeNum !== 0 && numerator === 0) {
            return wholeNum;
        } else if (wholeNum === 0 && numerator !== 0) {
            return KhanUtil.fraction(n, d, defraction, reduce, small, parens);
        } else {
            return 0;
        }
    },
    fractionReduce: function (n, d, small, parens) {
        return KhanUtil.fraction(n, d, true, true, small, parens);
    },
    fractionSmall: function (n, d, defraction, reduce, parens) {
        return KhanUtil.fraction(n, d, defraction, reduce, true, parens);
    },
    piFraction: function (num, niceAngle, tolerance, big) {
        if (num.constructor === Number) {
            if (tolerance == null) {
                tolerance = 0.001;
            }
            var f = KhanUtil.toFraction(num / Math.PI, tolerance), n = f[0], d = f[1];
            if (niceAngle) {
                if (n === 0) {
                    return '0';
                }
                if (n === 1 && d === 1) {
                    return '\\pi';
                }
            }
            var frac = big ? KhanUtil.fraction(n, d) : KhanUtil.fractionSmall(n, d);
            return d === 1 ? n + '\\pi' : frac + '\\pi';
        }
    },
    reduces: function (n, d) {
        return KhanUtil.getGCD(n, d) > 1;
    },
    fractionSimplification: function (n, d) {
        var result = '\\frac{' + n + '}{' + d + '}';
        if (d <= 1 || KhanUtil.getGCD(n, d) > 1) {
            result += ' = ' + KhanUtil.fractionReduce(n, d);
        }
        return result;
    },
    mixedOrImproper: function (n, d) {
        if (n < d || KhanUtil.rand(2) > 0) {
            return KhanUtil.fraction(n, d);
        } else {
            var imp = Math.floor(n / d);
            return imp + KhanUtil.fraction(n - d * imp, d);
        }
    },
    splitRadical: function (n) {
        if (n === 0) {
            return [
                0,
                1
            ];
        }
        var coefficient = 1;
        var radical = n;
        for (var i = 2; i * i <= n; i++) {
            while (radical % (i * i) === 0) {
                radical /= i * i;
                coefficient *= i;
            }
        }
        return [
            coefficient,
            radical
        ];
    },
    formattedSquareRootOf: function (n) {
        if (n === 1 || n === 0) {
            return n.toString();
        } else {
            var split = KhanUtil.splitRadical(n);
            var coefficient = split[0] === 1 ? '' : split[0].toString();
            var radical = split[1] === 1 ? '' : '\\sqrt{' + split[1] + '}';
            return coefficient + radical;
        }
    },
    squareRootCanSimplify: function (n) {
        return KhanUtil.formattedSquareRootOf(n) !== '\\sqrt{' + n + '}';
    },
    cardinalThrough20: function (n) {
        var cardinalUnits = [
            $._('zero'),
            $._('one'),
            $._('two'),
            $._('three'),
            $._('four'),
            $._('five'),
            $._('six'),
            $._('seven'),
            $._('eight'),
            $._('nine'),
            $._('ten'),
            $._('eleven'),
            $._('twelve'),
            $._('thirteen'),
            $._('fourteen'),
            $._('fifteen'),
            $._('sixteen'),
            $._('seventeen'),
            $._('eighteen'),
            $._('nineteen'),
            $._('twenty')
        ];
        if (n >= 0 && n <= 20) {
            return cardinalUnits[n];
        }
        return String(n);
    },
    CardinalThrough20: function (n) {
        var card = KhanUtil.cardinalThrough20(n);
        return card.charAt(0).toUpperCase() + card.slice(1);
    },
    ordinalThrough20: function (n) {
        var ordinalUnits = [
            $._('zeroth'),
            $._('first'),
            $._('second'),
            $._('third'),
            $._('fourth'),
            $._('fifth'),
            $._('sixth'),
            $._('seventh'),
            $._('eighth'),
            $._('ninth'),
            $._('tenth'),
            $._('eleventh'),
            $._('twelfth'),
            $._('thirteenth'),
            $._('fourteenth'),
            $._('fifteenth'),
            $._('sixteenth'),
            $._('seventeenth'),
            $._('eighteenth'),
            $._('nineteenth'),
            $._('twentieth')
        ];
        if (n >= 0 && n <= 20) {
            return ordinalUnits[n];
        }
        return n + 'th';
    },
    cardinal: function (n) {
        var cardinalScales = [
            '',
            $._('thousand'),
            $._('million'),
            $._('billion'),
            $._('trillion'),
            $._('quadrillion'),
            $._('quintillion'),
            $._('sextillion'),
            $._('septillion'),
            $._('octillion'),
            $._('nonillion'),
            $._('decillion'),
            $._('undecillion'),
            $._('duodecillion'),
            $._('tredecillion'),
            $._('quattuordecillion'),
            $._('quindecillion'),
            $._('sexdecillion'),
            $._('septendecillion'),
            $._('octodecillion'),
            $._('novemdecillion'),
            $._('vigintillion')
        ];
        var cardinalUnits = [
            $._('zero'),
            $._('one'),
            $._('two'),
            $._('three'),
            $._('four'),
            $._('five'),
            $._('six'),
            $._('seven'),
            $._('eight'),
            $._('nine'),
            $._('ten'),
            $._('eleven'),
            $._('twelve'),
            $._('thirteen'),
            $._('fourteen'),
            $._('fifteen'),
            $._('sixteen'),
            $._('seventeen'),
            $._('eighteen'),
            $._('nineteen')
        ];
        var cardinalTens = [
            '',
            '',
            $._('twenty'),
            $._('thirty'),
            $._('forty'),
            $._('fifty'),
            $._('sixty'),
            $._('seventy'),
            $._('eighty'),
            $._('ninety')
        ];
        var smallNumberWords = function (n) {
            var hundredDigit = Math.floor(n / 100);
            var rest = n % 100;
            var str = '';
            if (hundredDigit) {
                str += $._('%(unit)s hundred', { unit: cardinalUnits[hundredDigit] });
            }
            if (hundredDigit && rest) {
                str += ' ';
            }
            if (rest) {
                if (rest < 20) {
                    str += cardinalUnits[rest];
                } else {
                    var tenDigit = Math.floor(rest / 10);
                    var unitDigit = rest % 10;
                    if (tenDigit) {
                        str += cardinalTens[tenDigit];
                    }
                    if (tenDigit && unitDigit) {
                        str += '-';
                    }
                    if (unitDigit) {
                        str += cardinalUnits[unitDigit];
                    }
                }
            }
            return str;
        };
        if (n === 0) {
            return $._('zero');
        } else {
            var neg = false;
            if (n < 0) {
                neg = true;
                n = Math.abs(n);
            }
            var words = [];
            var scale = 0;
            while (n > 0) {
                var end = n % 1000;
                if (end > 0) {
                    if (scale > 0) {
                        words.unshift(cardinalScales[scale]);
                    }
                    words.unshift(smallNumberWords(end));
                }
                n = Math.floor(n / 1000);
                scale += 1;
            }
            if (neg) {
                words.unshift($._('negative'));
            }
            return words.join(' ');
        }
    },
    Cardinal: function (n) {
        var card = KhanUtil.cardinal(n);
        return card.charAt(0).toUpperCase() + card.slice(1);
    },
    quadraticRoots: function (a, b, c) {
        var underRadical = KhanUtil.splitRadical(b * b - 4 * a * c);
        var rootString = 'x =';
        if (b * b - 4 * a * c === 0) {
            rootString += KhanUtil.fraction(-b, 2 * a, true, true, true);
        } else if (underRadical[1] === 1) {
            rootString += KhanUtil.fraction(-b + underRadical[0], 2 * a, true, true, true) + ',' + KhanUtil.fraction(-b - underRadical[0], 2 * a, true, true, true);
        } else if (underRadical[0] === 1) {
            rootString += KhanUtil.expr([
                'frac',
                [
                    '+-',
                    -b,
                    [
                        'sqrt',
                        underRadical[1]
                    ]
                ],
                2 * a
            ]);
        } else {
            var divisor = KhanUtil.getGCD(b, 2 * a, underRadical[0]);
            if (divisor === Math.abs(2 * a)) {
                rootString += KhanUtil.expr([
                    '+-',
                    -b / (2 * a),
                    [
                        '*',
                        underRadical[0] / divisor,
                        [
                            'sqrt',
                            underRadical[1]
                        ]
                    ]
                ]);
            } else {
                rootString += KhanUtil.expr([
                    'frac',
                    [
                        '+-',
                        -b / divisor,
                        [
                            '*',
                            underRadical[0] / divisor,
                            [
                                'sqrt',
                                underRadical[1]
                            ]
                        ]
                    ],
                    2 * a / divisor
                ]);
            }
        }
        return rootString;
    },
    commafy: function (num) {
        var str = num.toString().split('.');
        var thousands = icu.getDecimalFormatSymbols().grouping_separator;
        var decimal = icu.getDecimalFormatSymbols().decimal_separator;
        if (thousands === '\xA0') {
            thousands = '\\;';
        }
        if (str[0].length >= 5) {
            str[0] = str[0].replace(/(\d)(?=(\d{3})+$)/g, '$1{' + thousands + '}');
        }
        if (str[1] && str[1].length >= 5) {
            str[1] = str[1].replace(/(\d{3})(?=\d)/g, '$1\\;');
        }
        return str.join(decimal);
    },
    plus: function () {
        var args = [], s;
        for (var i = 0; i < arguments.length; i++) {
            s = KhanUtil._plusTrim(arguments[i]);
            if (s) {
                args.push(s);
            }
        }
        return args.length > 0 ? args.join(' + ') : '0';
    },
    _plusTrim: function (s) {
        if (typeof s === 'string' && isNaN(s)) {
            if (s.indexOf('{') !== -1) {
                var l = s.indexOf('{', s.indexOf('{') + 1) + 1;
                var r = s.indexOf('}', s.indexOf('}') + 1);
                if (l !== s.lastIndexOf('{') + 1 && +KhanUtil._plusTrim(s.slice(l, r)) === 1) {
                    if (s.indexOf('\\') !== -1) {
                        return s.slice(0, s.indexOf('\\')) + s.slice(r + 1);
                    } else {
                        return s.slice(r + 1);
                    }
                }
                return s.slice(0, l) + KhanUtil._plusTrim(s.slice(l, r)) + s.slice(r);
            }
            if (s.indexOf('1') === 0 && isNaN(s[1])) {
                return s.slice(1);
            } else if (s.indexOf('-1') === 0 && isNaN(s[2])) {
                return '-' + s.slice(2);
            } else if (s.indexOf('0') === 0 || s.indexOf('-0') === 0) {
                return '';
            } else {
                return s;
            }
        } else if (typeof s === 'number') {
            return s;
        } else if (!isNaN(s)) {
            return +s;
        }
    },
    randVar: function () {
        return KhanUtil.randFromArray([
            'a',
            'k',
            'n',
            'p',
            'q',
            'r',
            't',
            'x',
            'y',
            'z'
        ]);
    },
    eulerFormExponent: function (angle) {
        var fraction = KhanUtil.toFraction(angle / Math.PI, 0.001);
        var numerator = fraction[0], denominator = fraction[1];
        var eExp = (numerator > 1 ? numerator : '') + '\\pi i';
        if (denominator !== 1) {
            eExp += ' / ' + denominator;
        }
        return eExp;
    },
    polarForm: function (radius, angle, useEulerForm) {
        var fraction = KhanUtil.toFraction(angle / Math.PI, 0.001);
        var numerator = fraction[0];
        var equation;
        if (useEulerForm) {
            if (numerator > 0) {
                var ePower = KhanUtil.expr([
                    '^',
                    'e',
                    KhanUtil.eulerFormExponent(angle)
                ]);
                equation = (radius > 1 ? radius : '') + ' ' + ePower;
            } else {
                equation = radius;
            }
        } else {
            if (angle === 0) {
                equation = radius;
            } else {
                var angleRep = KhanUtil.piFraction(angle, true);
                var cis = '\\cos \\left(' + angleRep + '\\right) + i \\sin \\left(' + angleRep + '\\right)';
                if (radius !== 1) {
                    equation = radius + '\\left(' + cis + '\\right)';
                } else {
                    equation = cis;
                }
            }
        }
        return equation;
    },
    coefficient: function (n) {
        if (n === 1 || n === '1') {
            return '';
        } else if (n === -1 || n === '-1') {
            return '-';
        } else {
            return n;
        }
    },
    fractionVariable: function (numerator, denominator, variable) {
        variable = variable || '';
        if (denominator === 0) {
            return '\\text{undefined}';
        }
        if (numerator === 0) {
            return 0;
        }
        if (typeof denominator === 'number') {
            if (denominator < 0) {
                numerator *= -1;
                denominator *= -1;
            }
            var GCD = KhanUtil.getGCD(numerator, denominator);
            numerator /= GCD;
            denominator /= GCD;
            if (denominator === 1) {
                return KhanUtil.coefficient(numerator) + variable;
            }
        }
        if (numerator < 0) {
            return '-\\dfrac{' + KhanUtil.coefficient(-numerator) + variable + '}{' + denominator + '}';
        } else {
            return '\\dfrac{' + KhanUtil.coefficient(numerator) + variable + '}{' + denominator + '}';
        }
    },
    complexNumber: function (real, imaginary) {
        if (real === 0 && imaginary === 0) {
            return '0';
        } else if (real === 0) {
            return KhanUtil.coefficient(imaginary) + 'i';
        } else if (imaginary === 0) {
            return real;
        } else {
            return KhanUtil.expr([
                '+',
                real,
                [
                    '*',
                    imaginary,
                    'i'
                ]
            ]);
        }
    },
    complexFraction: function (real, realDenominator, imag, imagDenominator) {
        var ret = '';
        if (real === 0 && imag === 0) {
            ret = '0';
        }
        if (real !== 0) {
            ret += KhanUtil.fraction(real, realDenominator, false, true);
        }
        if (imag !== 0) {
            if (imag / imagDenominator > 0) {
                if (real !== 0) {
                    ret += ' + ';
                }
                ret += KhanUtil.fraction(imag, imagDenominator, false, true) + ' i';
            } else {
                imag = Math.abs(imag);
                imagDenominator = Math.abs(imagDenominator);
                ret += ' - ';
                ret += KhanUtil.fraction(imag, imagDenominator, false, true) + ' i';
            }
        }
        return ret;
    },
    scientificExponent: function (num) {
        return Math.floor(Math.log(Math.abs(num)) / Math.log(10));
    },
    scientificMantissa: function (precision, num) {
        var exponent = KhanUtil.scientificExponent(num);
        var factor = Math.pow(10, exponent);
        precision -= 1;
        var mantissa = KhanUtil.roundTo(precision, num / factor);
        return mantissa;
    },
    scientific: function (precision, num) {
        var exponent = KhanUtil.scientificExponent(num);
        var mantissa = KhanUtil.localeToFixed(KhanUtil.scientificMantissa(precision, num), precision - 1);
        return '' + mantissa + '\\times 10^{' + exponent + '}';
    }
});
},{"./expressions.js":4,"./math.js":13}],13:[function(require,module,exports){
require('../third_party/raphael.js');
var knumber = require('./knumber.js');
$.extend(KhanUtil, {
    cleanMath: function (expr) {
        return typeof expr === 'string' ? expr.replace(/\+\s*-/g, '- ').replace(/-\s*-/g, '+ ').replace(/\^1/g, '') : expr;
    },
    rand: function (num) {
        return Math.floor(num * KhanUtil.random());
    },
    digits: function (n) {
        if (n === 0) {
            return [0];
        }
        var list = [];
        while (n > 0) {
            list.push(n % 10);
            n = Math.floor(n / 10);
        }
        return list;
    },
    integerToDigits: function (n) {
        return KhanUtil.digits(n).reverse();
    },
    decimalDigits: function (n) {
        var str = '' + Math.abs(n);
        str = str.replace('.', '');
        var list = [];
        for (var i = str.length; i > 0; i--) {
            list.push(str.charAt(i - 1));
        }
        return list;
    },
    decimalPlaces: function (n) {
        var str = '' + Math.abs(n);
        str = str.split('.');
        if (str.length === 1) {
            return 0;
        } else {
            return str[1].length;
        }
    },
    digitsToInteger: function (digits) {
        var place = Math.floor(Math.pow(10, digits.length - 1));
        var number = 0;
        $.each(digits, function (index, digit) {
            number += digit * place;
            place /= 10;
        });
        return number;
    },
    padDigitsToNum: function (digits, num) {
        digits = digits.slice(0);
        while (digits.length < num) {
            digits.push(0);
        }
        return digits;
    },
    placesLeftOfDecimal: [
        $._('one'),
        $._('ten'),
        $._('hundred'),
        $._('thousand')
    ],
    placesRightOfDecimal: [
        $._('one'),
        $._('tenth'),
        $._('hundredth'),
        $._('thousandth'),
        $._('ten thousandth')
    ],
    powerToPlace: function (power) {
        if (power < 0) {
            return KhanUtil.placesRightOfDecimal[-1 * power];
        } else {
            return KhanUtil.placesLeftOfDecimal[power];
        }
    },
    roundTowardsZero: function (x) {
        if (x < 0) {
            return Math.ceil(x - 0.001);
        }
        return Math.floor(x + 0.001);
    },
    bound: function (num) {
        if (num === 0) {
            return num;
        } else if (num < 0) {
            return -KhanUtil.bound(-num);
        } else {
            return Math.max(0.000001, Math.min(num, 100000000000000000000));
        }
    },
    factorial: function (x) {
        if (x <= 1) {
            return x;
        } else {
            return x * KhanUtil.factorial(x - 1);
        }
    },
    getGCD: function (a, b) {
        if (arguments.length > 2) {
            var rest = [].slice.call(arguments, 1);
            return KhanUtil.getGCD(a, KhanUtil.getGCD.apply(KhanUtil, rest));
        } else {
            var mod;
            a = Math.abs(a);
            b = Math.abs(b);
            while (b) {
                mod = a % b;
                a = b;
                b = mod;
            }
            return a;
        }
    },
    getLCM: function (a, b) {
        if (arguments.length > 2) {
            var rest = [].slice.call(arguments, 1);
            return KhanUtil.getLCM(a, KhanUtil.getLCM.apply(KhanUtil, rest));
        } else {
            return Math.abs(a * b) / KhanUtil.getGCD(a, b);
        }
    },
    primes: [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
        31,
        37,
        41,
        43,
        47,
        53,
        59,
        61,
        67,
        71,
        73,
        79,
        83,
        89,
        97
    ],
    denominators: [
        2,
        3,
        4,
        5,
        6,
        8,
        10,
        12,
        100
    ],
    smallDenominators: [
        2,
        3,
        4,
        5,
        6,
        8,
        10,
        12
    ],
    getPrime: function () {
        return KhanUtil.primes[KhanUtil.rand(KhanUtil.primes.length)];
    },
    isPrime: function (n) {
        if (n <= 1) {
            return false;
        } else if (n < 101) {
            return !!$.grep(KhanUtil.primes, function (p, i) {
                return Math.abs(p - n) <= 0.5;
            }).length;
        } else {
            if (n <= 1 || n > 2 && n % 2 === 0) {
                return false;
            } else {
                for (var i = 3, sqrt = Math.sqrt(n); i <= sqrt; i += 2) {
                    if (n % i === 0) {
                        return false;
                    }
                }
            }
            return true;
        }
    },
    isOdd: function (n) {
        return n % 2 === 1;
    },
    isEven: function (n) {
        return n % 2 === 0;
    },
    getOddComposite: function (min, max) {
        if (min === undefined) {
            min = 0;
        }
        if (max === undefined) {
            max = 100;
        }
        var oddComposites = [
            9,
            15,
            21,
            25,
            27,
            33,
            35,
            39,
            45,
            49,
            51,
            55
        ];
        oddComposites = oddComposites.concat([
            57,
            63,
            65,
            69,
            75,
            77,
            81,
            85,
            87,
            91,
            93,
            95,
            99
        ]);
        var result = -1;
        while (result < min || result > max) {
            result = oddComposites[KhanUtil.rand(oddComposites.length)];
        }
        return result;
    },
    getEvenComposite: function (min, max) {
        if (min === undefined) {
            min = 0;
        }
        if (max === undefined) {
            max = 100;
        }
        var evenComposites = [
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
            20,
            22,
            24,
            26
        ];
        evenComposites = evenComposites.concat([
            28,
            30,
            32,
            34,
            36,
            38,
            40,
            42,
            44,
            46,
            48
        ]);
        evenComposites = evenComposites.concat([
            50,
            52,
            54,
            56,
            58,
            60,
            62,
            64,
            66,
            68,
            70,
            72
        ]);
        evenComposites = evenComposites.concat([
            74,
            76,
            78,
            80,
            82,
            84,
            86,
            88,
            90,
            92,
            94,
            96,
            98
        ]);
        var result = -1;
        while (result < min || result > max) {
            result = evenComposites[KhanUtil.rand(evenComposites.length)];
        }
        return result;
    },
    getComposite: function () {
        if (KhanUtil.randRange(0, 1)) {
            return KhanUtil.getEvenComposite();
        } else {
            return KhanUtil.getOddComposite();
        }
    },
    getPrimeFactorization: function (number) {
        if (number === 1) {
            return [];
        } else if (KhanUtil.isPrime(number)) {
            return [number];
        }
        var maxf = Math.sqrt(number);
        for (var f = 2; f <= maxf; f++) {
            if (number % f === 0) {
                return $.merge(KhanUtil.getPrimeFactorization(f), KhanUtil.getPrimeFactorization(number / f));
            }
        }
    },
    getFactors: function (number) {
        var factors = [], ins = function (n) {
                if (_(factors).indexOf(n) === -1) {
                    factors.push(n);
                }
            };
        var maxf2 = number;
        for (var f = 1; f * f <= maxf2; f++) {
            if (number % f === 0) {
                ins(f);
                ins(number / f);
            }
        }
        return KhanUtil.sortNumbers(factors);
    },
    getNontrivialFactor: function (number) {
        var factors = KhanUtil.getFactors(number);
        return factors[KhanUtil.randRange(1, factors.length - 2)];
    },
    getMultiples: function (number, upperLimit) {
        var multiples = [];
        for (var i = 1; i * number <= upperLimit; i++) {
            multiples.push(i * number);
        }
        return multiples;
    },
    splitRadical: function (n) {
        if (n === 0) {
            return [
                0,
                1
            ];
        }
        var coefficient = 1;
        var radical = n;
        for (var i = 2; i * i <= n; i++) {
            while (radical % (i * i) === 0) {
                radical /= i * i;
                coefficient *= i;
            }
        }
        return [
            coefficient,
            radical
        ];
    },
    splitCube: function (n) {
        if (n === 0) {
            return [
                0,
                1
            ];
        }
        var coefficient = 1;
        var radical = n;
        for (var i = 2; i * i * i <= n; i++) {
            while (radical % (i * i * i) === 0) {
                radical /= i * i * i;
                coefficient *= i;
            }
        }
        return [
            coefficient,
            radical
        ];
    },
    randRange: function (min, max) {
        var dimensions = [].slice.call(arguments, 2);
        if (dimensions.length === 0) {
            return Math.floor(KhanUtil.rand(max - min + 1)) + min;
        } else {
            var args = [
                min,
                max
            ].concat(dimensions.slice(1));
            return $.map(new Array(dimensions[0]), function () {
                return [KhanUtil.randRange.apply(null, args)];
            });
        }
    },
    randRangeUnique: function (min, max, count) {
        if (count == null) {
            return KhanUtil.randRange(min, max);
        } else {
            var toReturn = [];
            for (var i = min; i <= max; i++) {
                toReturn.push(i);
            }
            return KhanUtil.shuffle(toReturn, count);
        }
    },
    randRangeUniqueNonZero: function (min, max, count) {
        if (count == null) {
            return KhanUtil.randRangeNonZero(min, max);
        } else {
            var toReturn = [];
            for (var i = min; i <= max; i++) {
                if (i === 0) {
                    continue;
                }
                toReturn.push(i);
            }
            return KhanUtil.shuffle(toReturn, count);
        }
    },
    randRangeWeighted: function (min, max, target, perc) {
        if (KhanUtil.random() < perc || target === min && target === max) {
            return target;
        } else {
            return KhanUtil.randRangeExclude(min, max, [target]);
        }
    },
    randRangeExclude: function (min, max, excludes) {
        var result;
        do {
            result = KhanUtil.randRange(min, max);
        } while (_(excludes).indexOf(result) !== -1);
        return result;
    },
    randRangeWeightedExclude: function (min, max, target, perc, excludes) {
        var result;
        do {
            result = KhanUtil.randRangeWeighted(min, max, target, perc);
        } while (_(excludes).indexOf(result) !== -1);
        return result;
    },
    randRangeNonZero: function (min, max) {
        return KhanUtil.randRangeExclude(min, max, [0]);
    },
    randFromArray: function (arr, count) {
        if (count == null) {
            return arr[KhanUtil.rand(arr.length)];
        } else {
            return $.map(new Array(count), function () {
                return KhanUtil.randFromArray(arr);
            });
        }
    },
    randFromArrayExclude: function (arr, excludes) {
        var cleanArr = [];
        for (var i = 0; i < arr.length; i++) {
            if (_(excludes).indexOf(arr[i]) === -1) {
                cleanArr.push(arr[i]);
            }
        }
        return KhanUtil.randFromArray(cleanArr);
    },
    roundToNearest: function (increment, num) {
        return Math.round(num / increment) * increment;
    },
    roundTo: function (precision, num) {
        var factor = Math.pow(10, precision).toFixed(5);
        return Math.round((num * factor).toFixed(5)) / factor;
    },
    toFixedApprox: function (num, precision) {
        var fixedStr = num.toFixed(precision);
        if (knumber.equal(+fixedStr, num)) {
            return fixedStr;
        } else {
            return '\\approx ' + fixedStr;
        }
    },
    roundToApprox: function (num, precision) {
        var fixed = KhanUtil.roundTo(precision, num);
        if (knumber.equal(fixed, num)) {
            return String(fixed);
        } else {
            return KhanUtil.toFixedApprox(num, precision);
        }
    },
    floorTo: function (precision, num) {
        var factor = Math.pow(10, precision).toFixed(5);
        return Math.floor((num * factor).toFixed(5)) / factor;
    },
    ceilTo: function (precision, num) {
        var factor = Math.pow(10, precision).toFixed(5);
        return Math.ceil((num * factor).toFixed(5)) / factor;
    },
    toFraction: function (decimal, tolerance) {
        if (tolerance == null) {
            tolerance = Math.pow(2, -46);
        }
        if (decimal < 0 || decimal > 1) {
            var fract = decimal % 1;
            fract += fract < 0 ? 1 : 0;
            var nd = KhanUtil.toFraction(fract, tolerance);
            nd[0] += Math.round(decimal - fract) * nd[1];
            return nd;
        } else if (Math.abs(Math.round(Number(decimal)) - decimal) <= tolerance) {
            return [
                Math.round(decimal),
                1
            ];
        } else {
            var loN = 0, loD = 1, hiN = 1, hiD = 1, midN = 1, midD = 2;
            while (1) {
                if (Math.abs(Number(midN / midD) - decimal) <= tolerance) {
                    return [
                        midN,
                        midD
                    ];
                } else if (midN / midD < decimal) {
                    loN = midN;
                    loD = midD;
                } else {
                    hiN = midN;
                    hiD = midD;
                }
                midN = loN + hiN;
                midD = loD + hiD;
            }
        }
    },
    getNumericFormat: function (text) {
        text = $.trim(text);
        text = text.replace(/\u2212/, '-').replace(/([+-])\s+/g, '$1');
        if (text.match(/^[+-]?\d+$/)) {
            return 'integer';
        } else if (text.match(/^[+-]?\d+\s+\d+\s*\/\s*\d+$/)) {
            return 'mixed';
        }
        var fraction = text.match(/^[+-]?(\d+)\s*\/\s*(\d+)$/);
        if (fraction) {
            return parseFloat(fraction[1]) > parseFloat(fraction[2]) ? 'improper' : 'proper';
        } else if (text.replace(/[,. ]/g, '').match(/^\d+$/)) {
            return 'decimal';
        } else if (text.match(/(pi?|\u03c0|t(?:au)?|\u03c4|pau)/)) {
            return 'pi';
        } else {
            return null;
        }
    },
    toNumericString: function (number, format) {
        if (number == null) {
            return '';
        } else if (number === 0) {
            return '0';
        }
        if (format === 'percent') {
            return number * 100 + '%';
        }
        if (format === 'pi') {
            var fraction = knumber.toFraction(number / Math.PI);
            var numerator = Math.abs(fraction[0]), denominator = fraction[1];
            if (knumber.isInteger(numerator)) {
                var sign = number < 0 ? '-' : '';
                var pi = '\u03C0';
                return sign + (numerator === 1 ? '' : numerator) + pi + (denominator === 1 ? '' : '/' + denominator);
            }
        }
        if (_([
                'proper',
                'improper',
                'mixed',
                'fraction'
            ]).contains(format)) {
            var fraction = knumber.toFraction(number);
            var numerator = Math.abs(fraction[0]), denominator = fraction[1];
            var sign = number < 0 ? '-' : '';
            if (denominator === 1) {
                return sign + numerator;
            } else if (format === 'mixed') {
                var modulus = numerator % denominator;
                var integer = (numerator - modulus) / denominator;
                return sign + (integer ? integer + ' ' : '') + modulus + '/' + denominator;
            }
            return sign + numerator + '/' + denominator;
        }
        return String(number);
    },
    shuffle: function (array, count) {
        array = [].slice.call(array, 0);
        var beginning = typeof count === 'undefined' || count > array.length ? 0 : array.length - count;
        for (var top = array.length; top > beginning; top--) {
            var newEnd = Math.floor(KhanUtil.random() * top), tmp = array[newEnd];
            array[newEnd] = array[top - 1];
            array[top - 1] = tmp;
        }
        return array.slice(beginning);
    },
    sortNumbers: function (array) {
        return array.slice(0).sort(function (a, b) {
            return a - b;
        });
    },
    truncate_to_max: function (num, digits) {
        return parseFloat(num.toFixed(digits));
    },
    isInt: function (num) {
        return parseFloat(num) === parseInt(num, 10) && !isNaN(num);
    },
    colorMarkup: function (val, color) {
        return '\\color{' + color + '}{' + val + '}';
    },
    contains: function (list, item) {
        return _.any(list, function (elem) {
            if (_.isEqual(item, elem)) {
                return true;
            }
            return false;
        });
    },
    BLUE: '#6495ED',
    ORANGE: '#FFA500',
    PINK: '#FF00AF',
    GREEN: '#28AE7B',
    PURPLE: '#9D38BD',
    RED: '#DF0030',
    GRAY: 'gray',
    BLACK: 'black',
    LIGHT_BLUE: '#9AB8ED',
    LIGHT_ORANGE: '#EDD19B',
    LIGHT_PINK: '#ED9BD3',
    LIGHT_GREEN: '#9BEDCE',
    LIGHT_PURPLE: '#DA9BED',
    LIGHT_RED: '#ED9AAC',
    LIGHT_GRAY: '#ED9B9B',
    LIGHT_BLACK: '#ED9B9B',
    GRAY10: '#D6D6D6',
    GRAY20: '#CDCDCD',
    GRAY30: '#B3B3B3',
    GRAY40: '#9A9A9A',
    GRAY50: '#808080',
    GRAY60: '#666666',
    GRAY70: '#4D4D4D',
    GRAY80: '#333333',
    GRAY90: '#1A1A1A',
    BLUE_A: '#C7E9F1',
    BLUE_B: '#9CDCEB',
    BLUE_C: '#58C4DD',
    BLUE_D: '#29ABCA',
    BLUE_E: '#1C758A',
    TEAL_A: '#ACEAD7',
    TEAL_B: '#76DDC0',
    TEAL_C: '#5CD0B3',
    TEAL_D: '#55C1A7',
    TEAL_E: '#49A88F',
    GREEN_A: '#C9E2AE',
    GREEN_B: '#A6CF8C',
    GREEN_C: '#83C167',
    GREEN_D: '#77B05D',
    GREEN_E: '#699C52',
    GOLD_A: '#F7C797',
    GOLD_B: '#F9B775',
    GOLD_C: '#F0AC5F',
    GOLD_D: '#E1A158',
    GOLD_E: '#C78D46',
    RED_A: '#F7A1A3',
    RED_B: '#FF8080',
    RED_C: '#FC6255',
    RED_D: '#E65A4C',
    RED_E: '#CF5044',
    MAROON_A: '#ECABC1',
    MAROON_B: '#EC92AB',
    MAROON_C: '#C55F73',
    MAROON_D: '#A24D61',
    MAROON_E: '#94424F',
    PURPLE_A: '#CAA3E8',
    PURPLE_B: '#B189C6',
    PURPLE_C: '#9A72AC',
    PURPLE_D: '#715582',
    PURPLE_E: '#644172',
    MINT_A: '#F5F9E8',
    MINT_B: '#EDF2DF',
    MINT_C: '#E0E5CC',
    GRAY_A: '#FDFDFD',
    GRAY_B: '#F7F7F7',
    GRAY_C: '#EEEEEE',
    GRAY_D: '#DDDDDD',
    GRAY_E: '#CCCCCC',
    GRAY_F: '#AAAAAA',
    GRAY_G: '#999999',
    GRAY_H: '#555555',
    GRAY_I: '#333333',
    KA_BLUE: '#314453',
    KA_GREEN: '#639B24',
    _BACKGROUND: '#FDFDFD'
});
$.extend(KhanUtil, {
    INTERACTING: KhanUtil.ORANGE,
    INTERACTIVE: KhanUtil.ORANGE,
    DYNAMIC: KhanUtil.BLUE
});
},{"../third_party/raphael.js":23,"./knumber.js":9}],14:[function(require,module,exports){
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
},{}],15:[function(require,module,exports){
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
},{}],16:[function(require,module,exports){
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
},{"./crc32.js":3}],17:[function(require,module,exports){
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
},{}],18:[function(require,module,exports){
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
},{"./kvector.js":11,"./objective_.js":14,"./transform-helpers.js":17}],19:[function(require,module,exports){
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
},{"./kvector.js":11,"./wrapped-defaults.js":18}],20:[function(require,module,exports){
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
},{"./kpoint.js":10,"./kvector.js":11,"./transform-helpers.js":17,"./wrapped-defaults.js":18}],21:[function(require,module,exports){
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
},{"./wrapped-defaults.js":18}],22:[function(require,module,exports){
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

},{}],23:[function(require,module,exports){
/*!
 * Raphael 1.5.2 - JavaScript Vector Library
 *
 * Copyright (c) 2010 Dmitry Baranovskiy (http://raphaeljs.com)
 * Licensed under the MIT (http://raphaeljs.com/license.html) license.
 */
(function () {
    var setAttr;
    if ("".trim) {
        setAttr = function(node, att, value) {
            node.setAttribute(att, String(value).trim());
        };
    } else {
        setAttr = function(node, att, value) {
            node.setAttribute(att, String(value));
        };
    }
    function R() {
        if (R.is(arguments[0], array)) {
            var a = arguments[0],
                cnv = create[apply](R, a.splice(0, 3 + R.is(a[0], nu))),
                res = cnv.set();
            for (var i = 0, ii = a[length]; i < ii; i++) {
                var j = a[i] || {};
                elements[has](j.type) && res[push](cnv[j.type]().attr(j));
            }
            return res;
        }
        return create[apply](R, arguments);
    }
    R.version = "1.5.2";
    var separator = /[, ]+/,
        elements = {circle: 1, rect: 1, path: 1, ellipse: 1, text: 1, image: 1},
        formatrg = /\{(\d+)\}/g,
        proto = "prototype",
        has = "hasOwnProperty",
        doc = document,
        win = window,
        oldRaphael = {
            was: Object[proto][has].call(win, "Raphael"),
            is: win.Raphael
        },
        Paper = function () {
            this.customAttributes = {};
        },
        paperproto,
        appendChild = "appendChild",
        apply = "apply",
        concat = "concat",
        supportsTouch = "createTouch" in doc,
        E = "",
        S = " ",
        Str = String,
        split = "split",
        events = "click dblclick mousedown mousemove mouseout mouseover mouseup touchstart touchmove touchend orientationchange touchcancel gesturestart gesturechange gestureend"[split](S),
        touchMap = {
            mousedown: "touchstart",
            mousemove: "touchmove",
            mouseup: "touchend"
        },
        join = "join",
        length = "length",
        lowerCase = Str[proto].toLowerCase,
        math = Math,
        mmax = math.max,
        mmin = math.min,
        abs = math.abs,
        pow = math.pow,
        PI = math.PI,
        nu = "number",
        string = "string",
        array = "array",
        toString = "toString",
        fillString = "fill",
        objectToString = Object[proto][toString],
        paper = {},
        push = "push",
        ISURL = /^url\(['"]?([^\)]+?)['"]?\)$/i,
        colourRegExp = /^\s*((#[a-f\d]{6})|(#[a-f\d]{3})|rgba?\(\s*([\d\.]+%?\s*,\s*[\d\.]+%?\s*,\s*[\d\.]+(?:%?\s*,\s*[\d\.]+)?)%?\s*\)|hsba?\(\s*([\d\.]+(?:deg|\xb0|%)?\s*,\s*[\d\.]+%?\s*,\s*[\d\.]+(?:%?\s*,\s*[\d\.]+)?)%?\s*\)|hsla?\(\s*([\d\.]+(?:deg|\xb0|%)?\s*,\s*[\d\.]+%?\s*,\s*[\d\.]+(?:%?\s*,\s*[\d\.]+)?)%?\s*\))\s*$/i,
        isnan = {"NaN": 1, "Infinity": 1, "-Infinity": 1},
        bezierrg = /^(?:cubic-)?bezier\(([^,]+),([^,]+),([^,]+),([^\)]+)\)/,
        round = math.round,
        toFloat = parseFloat,
        toInt = parseInt,
        ms = " progid:DXImageTransform.Microsoft",
        upperCase = Str[proto].toUpperCase,
        availableAttrs = {blur: 0, "clip-rect": "0 0 1e9 1e9", cursor: "default", cx: 0, cy: 0, fill: "#fff", "fill-opacity": 1, font: '10px "Arial"', "font-family": '"Arial"', "font-size": "10", "font-style": "normal", "font-weight": 400, gradient: 0, height: 0, href: "http://raphaeljs.com/", opacity: 1, path: "M0,0", r: 0, rotation: 0, rx: 0, ry: 0, scale: "1 1", src: "", stroke: "#000", "stroke-dasharray": "", "stroke-linecap": "butt", "stroke-linejoin": "butt", "stroke-miterlimit": 0, "stroke-opacity": 1, "stroke-width": 1, target: "_blank", "text-anchor": "middle", title: "Raphael", translation: "0 0", width: 0, x: 0, y: 0},
        availableAnimAttrs = {along: "along", blur: nu, "clip-rect": "csv", cx: nu, cy: nu, fill: "colour", "fill-opacity": nu, "font-size": nu, height: nu, opacity: nu, path: "path", r: nu, rotation: "csv", rx: nu, ry: nu, scale: "csv", stroke: "colour", "stroke-opacity": nu, "stroke-width": nu, translation: "csv", width: nu, x: nu, y: nu},
        rp = "replace",
        animKeyFrames= /^(from|to|\d+%?)$/,
        commaSpaces = /\s*,\s*/,
        hsrg = {hs: 1, rg: 1},
        p2s = /,?([achlmqrstvxz]),?/gi,
        pathCommand = /([achlmqstvz])[\s,]*((-?\d*\.?\d*(?:e[-+]?\d+)?\s*,?\s*)+)/ig,
        pathValues = /(-?\d*\.?\d*(?:e[-+]?\d+)?)\s*,?\s*/ig,
        radial_gradient = /^r(?:\(([^,]+?)\s*,\s*([^\)]+?)\))?/,
        sortByKey = function (a, b) {
            return a.key - b.key;
        };

    R.type = (win.SVGAngle || doc.implementation.hasFeature("http://www.w3.org/TR/SVG11/feature#BasicStructure", "1.1") ? "SVG" : "VML");
    if (R.type == "VML") {
        var d = doc.createElement("div"),
            b;
        d.innerHTML = '<v:shape adj="1"/>';
        b = d.firstChild;
        b.style.behavior = "url(#default#VML)";
        if (!(b && typeof b.adj == "object")) {
            return R.type = null;
        }
        d = null;
    }
    R.svg = !(R.vml = R.type == "VML");
    Paper[proto] = R[proto];
    paperproto = Paper[proto];
    R._id = 0;
    R._oid = 0;
    R.fn = {};
    R.is = function (o, type) {
        type = lowerCase.call(type);
        if (type == "finite") {
            return !isnan[has](+o);
        }
        return  (type == "null" && o === null) ||
                (type == typeof o) ||
                (type == "object" && o === Object(o)) ||
                (type == "array" && Array.isArray && Array.isArray(o)) ||
                objectToString.call(o).slice(8, -1).toLowerCase() == type;
    };
    R.angle = function (x1, y1, x2, y2, x3, y3) {
        if (x3 == null) {
            var x = x1 - x2,
                y = y1 - y2;
            if (!x && !y) {
                return 0;
            }
            return ((x < 0) * 180 + math.atan(-y / -x) * 180 / PI + 360) % 360;
        } else {
            return R.angle(x1, y1, x3, y3) - R.angle(x2, y2, x3, y3);
        }
    };
    R.rad = function (deg) {
        return deg % 360 * PI / 180;
    };
    R.deg = function (rad) {
        return rad * 180 / PI % 360;
    };
    R.snapTo = function (values, value, tolerance) {
        tolerance = R.is(tolerance, "finite") ? tolerance : 10;
        if (R.is(values, array)) {
            var i = values.length;
            while (i--) if (abs(values[i] - value) <= tolerance) {
                return values[i];
            }
        } else {
            values = +values;
            var rem = value % values;
            if (rem < tolerance) {
                return value - rem;
            }
            if (rem > values - tolerance) {
                return value - rem + values;
            }
        }
        return value;
    };
    function createUUID() {
        // http://www.ietf.org/rfc/rfc4122.txt
        var s = [],
            i = 0;
        for (; i < 32; i++) {
            s[i] = (~~(math.random() * 16))[toString](16);
        }
        s[12] = 4;  // bits 12-15 of the time_hi_and_version field to 0010
        s[16] = ((s[16] & 3) | 8)[toString](16);  // bits 6-7 of the clock_seq_hi_and_reserved to 01
        return "r-" + s[join]("");
    }

    R.setWindow = function (newwin) {
        win = newwin;
        doc = win.document;
    };
    // colour utilities
    var toHex = function (color) {
        if (R.vml) {
            // http://dean.edwards.name/weblog/2009/10/convert-any-colour-value-to-hex-in-msie/
            var trim = /^\s+|\s+$/g;
            var bod;
            try {
                var docum = new ActiveXObject("htmlfile");
                docum.write("<body>");
                docum.close();
                bod = docum.body;
            } catch(e) {
                bod = createPopup().document.body;
            }
            var range = bod.createTextRange();
            toHex = cacher(function (color) {
                try {
                    bod.style.color = Str(color)[rp](trim, E);
                    var value = range.queryCommandValue("ForeColor");
                    value = ((value & 255) << 16) | (value & 65280) | ((value & 16711680) >>> 16);
                    return "#" + ("000000" + value[toString](16)).slice(-6);
                } catch(e) {
                    return "none";
                }
            });
        } else {
            var i = doc.createElement("i");
            i.title = "Rapha\xebl Colour Picker";
            i.style.display = "none";
            doc.body[appendChild](i);
            toHex = cacher(function (color) {
                i.style.color = color;
                return doc.defaultView.getComputedStyle(i, E).getPropertyValue("color");
            });
        }
        return toHex(color);
    },
    hsbtoString = function () {
        return "hsb(" + [this.h, this.s, this.b] + ")";
    },
    hsltoString = function () {
        return "hsl(" + [this.h, this.s, this.l] + ")";
    },
    rgbtoString = function () {
        return this.hex;
    };
    R.hsb2rgb = function (h, s, b, o) {
        if (R.is(h, "object") && "h" in h && "s" in h && "b" in h) {
            b = h.b;
            s = h.s;
            h = h.h;
            o = h.o;
        }
        return R.hsl2rgb(h, s, b / 2, o);
    };
    R.hsl2rgb = function (h, s, l, o) {
        if (R.is(h, "object") && "h" in h && "s" in h && "l" in h) {
            l = h.l;
            s = h.s;
            h = h.h;
        }
        if (h > 1 || s > 1 || l > 1) {
            h /= 360;
            s /= 100;
            l /= 100;
        }
        var rgb = {},
            channels = ["r", "g", "b"],
            t2, t1, t3, r, g, b;
        if (!s) {
            rgb = {
                r: l,
                g: l,
                b: l
            };
        } else {
            if (l < .5) {
                t2 = l * (1 + s);
            } else {
                t2 = l + s - l * s;
            }
            t1 = 2 * l - t2;
            for (var i = 0; i < 3; i++) {
                t3 = h + 1 / 3 * -(i - 1);
                t3 < 0 && t3++;
                t3 > 1 && t3--;
                if (t3 * 6 < 1) {
                    rgb[channels[i]] = t1 + (t2 - t1) * 6 * t3;
                } else if (t3 * 2 < 1) {
                    rgb[channels[i]] = t2;
                } else if (t3 * 3 < 2) {
                    rgb[channels[i]] = t1 + (t2 - t1) * (2 / 3 - t3) * 6;
                } else {
                    rgb[channels[i]] = t1;
                }
            }
        }
        rgb.r *= 255;
        rgb.g *= 255;
        rgb.b *= 255;
        rgb.hex = "#" + (16777216 | rgb.b | (rgb.g << 8) | (rgb.r << 16)).toString(16).slice(1);
        R.is(o, "finite") && (rgb.opacity = o);
        rgb.toString = rgbtoString;
        return rgb;
    };
    R.rgb2hsb = function (red, green, blue) {
        if (green == null && R.is(red, "object") && "r" in red && "g" in red && "b" in red) {
            blue = red.b;
            green = red.g;
            red = red.r;
        }
        if (green == null && R.is(red, string)) {
            var clr = R.getRGB(red);
            red = clr.r;
            green = clr.g;
            blue = clr.b;
        }
        if (red > 1 || green > 1 || blue > 1) {
            red /= 255;
            green /= 255;
            blue /= 255;
        }
        var max = mmax(red, green, blue),
            min = mmin(red, green, blue),
            hue,
            saturation,
            brightness = max;
        if (min == max) {
            return {h: 0, s: 0, b: max, toString: hsbtoString};
        } else {
            var delta = (max - min);
            saturation = delta / max;
            if (red == max) {
                hue = (green - blue) / delta;
            } else if (green == max) {
                hue = 2 + ((blue - red) / delta);
            } else {
                hue = 4 + ((red - green) / delta);
            }
            hue /= 6;
            hue < 0 && hue++;
            hue > 1 && hue--;
        }
        return {h: hue, s: saturation, b: brightness, toString: hsbtoString};
    };
    R.rgb2hsl = function (red, green, blue) {
        if (green == null && R.is(red, "object") && "r" in red && "g" in red && "b" in red) {
            blue = red.b;
            green = red.g;
            red = red.r;
        }
        if (green == null && R.is(red, string)) {
            var clr = R.getRGB(red);
            red = clr.r;
            green = clr.g;
            blue = clr.b;
        }
        if (red > 1 || green > 1 || blue > 1) {
            red /= 255;
            green /= 255;
            blue /= 255;
        }
        var max = mmax(red, green, blue),
            min = mmin(red, green, blue),
            h,
            s,
            l = (max + min) / 2,
            hsl;
        if (min == max) {
            hsl =  {h: 0, s: 0, l: l};
        } else {
            var delta = max - min;
            s = l < .5 ? delta / (max + min) : delta / (2 - max - min);
            if (red == max) {
                h = (green - blue) / delta;
            } else if (green == max) {
                h = 2 + (blue - red) / delta;
            } else {
                h = 4 + (red - green) / delta;
            }
            h /= 6;
            h < 0 && h++;
            h > 1 && h--;
            hsl = {h: h, s: s, l: l};
        }
        hsl.toString = hsltoString;
        return hsl;
    };
    R._path2string = function () {
        return this.join(",")[rp](p2s, "$1");
    };
    function cacher(f, scope, postprocessor) {
        function newf() {
            var arg = Array[proto].slice.call(arguments, 0),
                args = arg[join]("\u25ba"),
                cache = newf.cache = newf.cache || {},
                count = newf.count = newf.count || [];
            if (cache[has](args)) {
                return postprocessor ? postprocessor(cache[args]) : cache[args];
            }
            count[length] >= 1e3 && delete cache[count.shift()];
            count[push](args);
            cache[args] = f[apply](scope, arg);
            return postprocessor ? postprocessor(cache[args]) : cache[args];
        }
        return newf;
    }

    R.getRGB = cacher(function (colour) {
        if (!colour || !!((colour = Str(colour)).indexOf("-") + 1)) {
            return {r: -1, g: -1, b: -1, hex: "none", error: 1};
        }
        if (colour == "none") {
            return {r: -1, g: -1, b: -1, hex: "none"};
        }
        !(hsrg[has](colour.toLowerCase().substring(0, 2)) || colour.charAt() == "#") && (colour = toHex(colour));
        var res,
            red,
            green,
            blue,
            opacity,
            t,
            values,
            rgb = colour.match(colourRegExp);
        if (rgb) {
            if (rgb[2]) {
                blue = toInt(rgb[2].substring(5), 16);
                green = toInt(rgb[2].substring(3, 5), 16);
                red = toInt(rgb[2].substring(1, 3), 16);
            }
            if (rgb[3]) {
                blue = toInt((t = rgb[3].charAt(3)) + t, 16);
                green = toInt((t = rgb[3].charAt(2)) + t, 16);
                red = toInt((t = rgb[3].charAt(1)) + t, 16);
            }
            if (rgb[4]) {
                values = rgb[4][split](commaSpaces);
                red = toFloat(values[0]);
                values[0].slice(-1) == "%" && (red *= 2.55);
                green = toFloat(values[1]);
                values[1].slice(-1) == "%" && (green *= 2.55);
                blue = toFloat(values[2]);
                values[2].slice(-1) == "%" && (blue *= 2.55);
                rgb[1].toLowerCase().slice(0, 4) == "rgba" && (opacity = toFloat(values[3]));
                values[3] && values[3].slice(-1) == "%" && (opacity /= 100);
            }
            if (rgb[5]) {
                values = rgb[5][split](commaSpaces);
                red = toFloat(values[0]);
                values[0].slice(-1) == "%" && (red *= 2.55);
                green = toFloat(values[1]);
                values[1].slice(-1) == "%" && (green *= 2.55);
                blue = toFloat(values[2]);
                values[2].slice(-1) == "%" && (blue *= 2.55);
                (values[0].slice(-3) == "deg" || values[0].slice(-1) == "\xb0") && (red /= 360);
                rgb[1].toLowerCase().slice(0, 4) == "hsba" && (opacity = toFloat(values[3]));
                values[3] && values[3].slice(-1) == "%" && (opacity /= 100);
                return R.hsb2rgb(red, green, blue, opacity);
            }
            if (rgb[6]) {
                values = rgb[6][split](commaSpaces);
                red = toFloat(values[0]);
                values[0].slice(-1) == "%" && (red *= 2.55);
                green = toFloat(values[1]);
                values[1].slice(-1) == "%" && (green *= 2.55);
                blue = toFloat(values[2]);
                values[2].slice(-1) == "%" && (blue *= 2.55);
                (values[0].slice(-3) == "deg" || values[0].slice(-1) == "\xb0") && (red /= 360);
                rgb[1].toLowerCase().slice(0, 4) == "hsla" && (opacity = toFloat(values[3]));
                values[3] && values[3].slice(-1) == "%" && (opacity /= 100);
                return R.hsl2rgb(red, green, blue, opacity);
            }
            rgb = {r: red, g: green, b: blue};
            rgb.hex = "#" + (16777216 | blue | (green << 8) | (red << 16)).toString(16).slice(1);
            R.is(opacity, "finite") && (rgb.opacity = opacity);
            return rgb;
        }
        return {r: -1, g: -1, b: -1, hex: "none", error: 1};
    }, R);
    R.getColor = function (value) {
        var start = this.getColor.start = this.getColor.start || {h: 0, s: 1, b: value || .75},
            rgb = this.hsb2rgb(start.h, start.s, start.b);
        start.h += .075;
        if (start.h > 1) {
            start.h = 0;
            start.s -= .2;
            start.s <= 0 && (this.getColor.start = {h: 0, s: 1, b: start.b});
        }
        return rgb.hex;
    };
    R.getColor.reset = function () {
        delete this.start;
    };
    // path utilities
    R.parsePathString = cacher(function (pathString) {
        if (!pathString) {
            return null;
        }
        var paramCounts = {a: 7, c: 6, h: 1, l: 2, m: 2, q: 4, s: 4, t: 2, v: 1, z: 0},
            data = [];
        if (R.is(pathString, array) && R.is(pathString[0], array)) { // rough assumption
            data = pathClone(pathString);
        }
        if (!data[length]) {
            Str(pathString)[rp](pathCommand, function (a, b, c) {
                var params = [],
                    name = lowerCase.call(b);
                c[rp](pathValues, function (a, b) {
                    b && params[push](+b);
                });
                if (name == "m" && params[length] > 2) {
                    data[push]([b][concat](params.splice(0, 2)));
                    name = "l";
                    b = b == "m" ? "l" : "L";
                }
                while (params[length] >= paramCounts[name]) {
                    data[push]([b][concat](params.splice(0, paramCounts[name])));
                    if (!paramCounts[name]) {
                        break;
                    }
                }
            });
        }
        data[toString] = R._path2string;
        return data;
    });
    R.findDotsAtSegment = function (p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, t) {
        var t1 = 1 - t,
            x = pow(t1, 3) * p1x + pow(t1, 2) * 3 * t * c1x + t1 * 3 * t * t * c2x + pow(t, 3) * p2x,
            y = pow(t1, 3) * p1y + pow(t1, 2) * 3 * t * c1y + t1 * 3 * t * t * c2y + pow(t, 3) * p2y,
            mx = p1x + 2 * t * (c1x - p1x) + t * t * (c2x - 2 * c1x + p1x),
            my = p1y + 2 * t * (c1y - p1y) + t * t * (c2y - 2 * c1y + p1y),
            nx = c1x + 2 * t * (c2x - c1x) + t * t * (p2x - 2 * c2x + c1x),
            ny = c1y + 2 * t * (c2y - c1y) + t * t * (p2y - 2 * c2y + c1y),
            ax = (1 - t) * p1x + t * c1x,
            ay = (1 - t) * p1y + t * c1y,
            cx = (1 - t) * c2x + t * p2x,
            cy = (1 - t) * c2y + t * p2y,
            alpha = (90 - math.atan((mx - nx) / (my - ny)) * 180 / PI);
        (mx > nx || my < ny) && (alpha += 180);
        return {x: x, y: y, m: {x: mx, y: my}, n: {x: nx, y: ny}, start: {x: ax, y: ay}, end: {x: cx, y: cy}, alpha: alpha};
    };
    var pathDimensions = cacher(function (path) {
        if (!path) {
            return {x: 0, y: 0, width: 0, height: 0};
        }
        path = path2curve(path);
        var x = 0,
            y = 0,
            X = [],
            Y = [],
            p;
        for (var i = 0, ii = path[length]; i < ii; i++) {
            p = path[i];
            if (p[0] == "M") {
                x = p[1];
                y = p[2];
                X[push](x);
                Y[push](y);
            } else {
                var dim = curveDim(x, y, p[1], p[2], p[3], p[4], p[5], p[6]);
                X = X[concat](dim.min.x, dim.max.x);
                Y = Y[concat](dim.min.y, dim.max.y);
                x = p[5];
                y = p[6];
            }
        }
        var xmin = mmin[apply](0, X),
            ymin = mmin[apply](0, Y);
        return {
            x: xmin,
            y: ymin,
            width: mmax[apply](0, X) - xmin,
            height: mmax[apply](0, Y) - ymin
        };
    }),
        pathClone = function (pathArray) {
            var res = [];
            if (!R.is(pathArray, array) || !R.is(pathArray && pathArray[0], array)) { // rough assumption
                pathArray = R.parsePathString(pathArray);
            }
            for (var i = 0, ii = pathArray[length]; i < ii; i++) {
                res[i] = [];
                for (var j = 0, jj = pathArray[i][length]; j < jj; j++) {
                    res[i][j] = pathArray[i][j];
                }
            }
            res[toString] = R._path2string;
            return res;
        },
        pathToRelative = cacher(function (pathArray) {
            if (!R.is(pathArray, array) || !R.is(pathArray && pathArray[0], array)) { // rough assumption
                pathArray = R.parsePathString(pathArray);
            }
            var res = [],
                x = 0,
                y = 0,
                mx = 0,
                my = 0,
                start = 0;
            if (pathArray[0][0] == "M") {
                x = pathArray[0][1];
                y = pathArray[0][2];
                mx = x;
                my = y;
                start++;
                res[push](["M", x, y]);
            }
            for (var i = start, ii = pathArray[length]; i < ii; i++) {
                var r = res[i] = [],
                    pa = pathArray[i];
                if (pa[0] != lowerCase.call(pa[0])) {
                    r[0] = lowerCase.call(pa[0]);
                    switch (r[0]) {
                        case "a":
                            r[1] = pa[1];
                            r[2] = pa[2];
                            r[3] = pa[3];
                            r[4] = pa[4];
                            r[5] = pa[5];
                            r[6] = +(pa[6] - x).toFixed(3);
                            r[7] = +(pa[7] - y).toFixed(3);
                            break;
                        case "v":
                            r[1] = +(pa[1] - y).toFixed(3);
                            break;
                        case "m":
                            mx = pa[1];
                            my = pa[2];
                        default:
                            for (var j = 1, jj = pa[length]; j < jj; j++) {
                                r[j] = +(pa[j] - ((j % 2) ? x : y)).toFixed(3);
                            }
                    }
                } else {
                    r = res[i] = [];
                    if (pa[0] == "m") {
                        mx = pa[1] + x;
                        my = pa[2] + y;
                    }
                    for (var k = 0, kk = pa[length]; k < kk; k++) {
                        res[i][k] = pa[k];
                    }
                }
                var len = res[i][length];
                switch (res[i][0]) {
                    case "z":
                        x = mx;
                        y = my;
                        break;
                    case "h":
                        x += +res[i][len - 1];
                        break;
                    case "v":
                        y += +res[i][len - 1];
                        break;
                    default:
                        x += +res[i][len - 2];
                        y += +res[i][len - 1];
                }
            }
            res[toString] = R._path2string;
            return res;
        }, 0, pathClone),
        pathToAbsolute = cacher(function (pathArray) {
            if (!R.is(pathArray, array) || !R.is(pathArray && pathArray[0], array)) { // rough assumption
                pathArray = R.parsePathString(pathArray);
            }
            var res = [],
                x = 0,
                y = 0,
                mx = 0,
                my = 0,
                start = 0;
            if (pathArray[0][0] == "M") {
                x = +pathArray[0][1];
                y = +pathArray[0][2];
                mx = x;
                my = y;
                start++;
                res[0] = ["M", x, y];
            }
            for (var i = start, ii = pathArray[length]; i < ii; i++) {
                var r = res[i] = [],
                    pa = pathArray[i];
                if (pa[0] != upperCase.call(pa[0])) {
                    r[0] = upperCase.call(pa[0]);
                    switch (r[0]) {
                        case "A":
                            r[1] = pa[1];
                            r[2] = pa[2];
                            r[3] = pa[3];
                            r[4] = pa[4];
                            r[5] = pa[5];
                            r[6] = +(pa[6] + x);
                            r[7] = +(pa[7] + y);
                            break;
                        case "V":
                            r[1] = +pa[1] + y;
                            break;
                        case "H":
                            r[1] = +pa[1] + x;
                            break;
                        case "M":
                            mx = +pa[1] + x;
                            my = +pa[2] + y;
                        default:
                            for (var j = 1, jj = pa[length]; j < jj; j++) {
                                r[j] = +pa[j] + ((j % 2) ? x : y);
                            }
                    }
                } else {
                    for (var k = 0, kk = pa[length]; k < kk; k++) {
                        res[i][k] = pa[k];
                    }
                }
                switch (r[0]) {
                    case "Z":
                        x = mx;
                        y = my;
                        break;
                    case "H":
                        x = r[1];
                        break;
                    case "V":
                        y = r[1];
                        break;
                    case "M":
                        mx = res[i][res[i][length] - 2];
                        my = res[i][res[i][length] - 1];
                    default:
                        x = res[i][res[i][length] - 2];
                        y = res[i][res[i][length] - 1];
                }
            }
            res[toString] = R._path2string;
            return res;
        }, null, pathClone),
        l2c = function (x1, y1, x2, y2) {
            return [x1, y1, x2, y2, x2, y2];
        },
        q2c = function (x1, y1, ax, ay, x2, y2) {
            var _13 = 1 / 3,
                _23 = 2 / 3;
            return [
                    _13 * x1 + _23 * ax,
                    _13 * y1 + _23 * ay,
                    _13 * x2 + _23 * ax,
                    _13 * y2 + _23 * ay,
                    x2,
                    y2
                ];
        },
        a2c = function (x1, y1, rx, ry, angle, large_arc_flag, sweep_flag, x2, y2, recursive) {
            // for more information of where this math came from visit:
            // http://www.w3.org/TR/SVG11/implnote.html#ArcImplementationNotes
            var _120 = PI * 120 / 180,
                rad = PI / 180 * (+angle || 0),
                res = [],
                xy,
                rotate = cacher(function (x, y, rad) {
                    var X = x * math.cos(rad) - y * math.sin(rad),
                        Y = x * math.sin(rad) + y * math.cos(rad);
                    return {x: X, y: Y};
                });
            if (!recursive) {
                xy = rotate(x1, y1, -rad);
                x1 = xy.x;
                y1 = xy.y;
                xy = rotate(x2, y2, -rad);
                x2 = xy.x;
                y2 = xy.y;
                var cos = math.cos(PI / 180 * angle),
                    sin = math.sin(PI / 180 * angle),
                    x = (x1 - x2) / 2,
                    y = (y1 - y2) / 2;
                var h = (x * x) / (rx * rx) + (y * y) / (ry * ry);
                if (h > 1) {
                    h = math.sqrt(h);
                    rx = h * rx;
                    ry = h * ry;
                }
                var rx2 = rx * rx,
                    ry2 = ry * ry,
                    k = (large_arc_flag == sweep_flag ? -1 : 1) *
                        math.sqrt(abs((rx2 * ry2 - rx2 * y * y - ry2 * x * x) / (rx2 * y * y + ry2 * x * x))),
                    cx = k * rx * y / ry + (x1 + x2) / 2,
                    cy = k * -ry * x / rx + (y1 + y2) / 2,
                    f1 = math.asin(((y1 - cy) / ry).toFixed(9)),
                    f2 = math.asin(((y2 - cy) / ry).toFixed(9));

                f1 = x1 < cx ? PI - f1 : f1;
                f2 = x2 < cx ? PI - f2 : f2;
                f1 < 0 && (f1 = PI * 2 + f1);
                f2 < 0 && (f2 = PI * 2 + f2);
                if (sweep_flag && f1 > f2) {
                    f1 = f1 - PI * 2;
                }
                if (!sweep_flag && f2 > f1) {
                    f2 = f2 - PI * 2;
                }
            } else {
                f1 = recursive[0];
                f2 = recursive[1];
                cx = recursive[2];
                cy = recursive[3];
            }
            var df = f2 - f1;
            if (abs(df) > _120) {
                var f2old = f2,
                    x2old = x2,
                    y2old = y2;
                f2 = f1 + _120 * (sweep_flag && f2 > f1 ? 1 : -1);
                x2 = cx + rx * math.cos(f2);
                y2 = cy + ry * math.sin(f2);
                res = a2c(x2, y2, rx, ry, angle, 0, sweep_flag, x2old, y2old, [f2, f2old, cx, cy]);
            }
            df = f2 - f1;
            var c1 = math.cos(f1),
                s1 = math.sin(f1),
                c2 = math.cos(f2),
                s2 = math.sin(f2),
                t = math.tan(df / 4),
                hx = 4 / 3 * rx * t,
                hy = 4 / 3 * ry * t,
                m1 = [x1, y1],
                m2 = [x1 + hx * s1, y1 - hy * c1],
                m3 = [x2 + hx * s2, y2 - hy * c2],
                m4 = [x2, y2];
            m2[0] = 2 * m1[0] - m2[0];
            m2[1] = 2 * m1[1] - m2[1];
            if (recursive) {
                return [m2, m3, m4][concat](res);
            } else {
                res = [m2, m3, m4][concat](res)[join]()[split](",");
                var newres = [];
                for (var i = 0, ii = res[length]; i < ii; i++) {
                    newres[i] = i % 2 ? rotate(res[i - 1], res[i], rad).y : rotate(res[i], res[i + 1], rad).x;
                }
                return newres;
            }
        },
        findDotAtSegment = function (p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, t) {
            var t1 = 1 - t;
            return {
                x: pow(t1, 3) * p1x + pow(t1, 2) * 3 * t * c1x + t1 * 3 * t * t * c2x + pow(t, 3) * p2x,
                y: pow(t1, 3) * p1y + pow(t1, 2) * 3 * t * c1y + t1 * 3 * t * t * c2y + pow(t, 3) * p2y
            };
        },
        curveDim = cacher(function (p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y) {
            var a = (c2x - 2 * c1x + p1x) - (p2x - 2 * c2x + c1x),
                b = 2 * (c1x - p1x) - 2 * (c2x - c1x),
                c = p1x - c1x,
                t1 = (-b + math.sqrt(b * b - 4 * a * c)) / 2 / a,
                t2 = (-b - math.sqrt(b * b - 4 * a * c)) / 2 / a,
                y = [p1y, p2y],
                x = [p1x, p2x],
                dot;
            abs(t1) > "1e12" && (t1 = .5);
            abs(t2) > "1e12" && (t2 = .5);
            if (t1 > 0 && t1 < 1) {
                dot = findDotAtSegment(p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, t1);
                x[push](dot.x);
                y[push](dot.y);
            }
            if (t2 > 0 && t2 < 1) {
                dot = findDotAtSegment(p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, t2);
                x[push](dot.x);
                y[push](dot.y);
            }
            a = (c2y - 2 * c1y + p1y) - (p2y - 2 * c2y + c1y);
            b = 2 * (c1y - p1y) - 2 * (c2y - c1y);
            c = p1y - c1y;
            t1 = (-b + math.sqrt(b * b - 4 * a * c)) / 2 / a;
            t2 = (-b - math.sqrt(b * b - 4 * a * c)) / 2 / a;
            abs(t1) > "1e12" && (t1 = .5);
            abs(t2) > "1e12" && (t2 = .5);
            if (t1 > 0 && t1 < 1) {
                dot = findDotAtSegment(p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, t1);
                x[push](dot.x);
                y[push](dot.y);
            }
            if (t2 > 0 && t2 < 1) {
                dot = findDotAtSegment(p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, t2);
                x[push](dot.x);
                y[push](dot.y);
            }
            return {
                min: {x: mmin[apply](0, x), y: mmin[apply](0, y)},
                max: {x: mmax[apply](0, x), y: mmax[apply](0, y)}
            };
        }),
        path2curve = cacher(function (path, path2) {
            var p = pathToAbsolute(path),
                p2 = path2 && pathToAbsolute(path2),
                attrs = {x: 0, y: 0, bx: 0, by: 0, X: 0, Y: 0, qx: null, qy: null},
                attrs2 = {x: 0, y: 0, bx: 0, by: 0, X: 0, Y: 0, qx: null, qy: null},
                processPath = function (path, d) {
                    var nx, ny;
                    if (!path) {
                        return ["C", d.x, d.y, d.x, d.y, d.x, d.y];
                    }
                    !(path[0] in {T:1, Q:1}) && (d.qx = d.qy = null);
                    switch (path[0]) {
                        case "M":
                            d.X = path[1];
                            d.Y = path[2];
                            break;
                        case "A":
                            path = ["C"][concat](a2c[apply](0, [d.x, d.y][concat](path.slice(1))));
                            break;
                        case "S":
                            nx = d.x + (d.x - (d.bx || d.x));
                            ny = d.y + (d.y - (d.by || d.y));
                            path = ["C", nx, ny][concat](path.slice(1));
                            break;
                        case "T":
                            d.qx = d.x + (d.x - (d.qx || d.x));
                            d.qy = d.y + (d.y - (d.qy || d.y));
                            path = ["C"][concat](q2c(d.x, d.y, d.qx, d.qy, path[1], path[2]));
                            break;
                        case "Q":
                            d.qx = path[1];
                            d.qy = path[2];
                            path = ["C"][concat](q2c(d.x, d.y, path[1], path[2], path[3], path[4]));
                            break;
                        case "L":
                            path = ["C"][concat](l2c(d.x, d.y, path[1], path[2]));
                            break;
                        case "H":
                            path = ["C"][concat](l2c(d.x, d.y, path[1], d.y));
                            break;
                        case "V":
                            path = ["C"][concat](l2c(d.x, d.y, d.x, path[1]));
                            break;
                        case "Z":
                            path = ["C"][concat](l2c(d.x, d.y, d.X, d.Y));
                            break;
                    }
                    return path;
                },
                fixArc = function (pp, i) {
                    if (pp[i][length] > 7) {
                        pp[i].shift();
                        var pi = pp[i];
                        while (pi[length]) {
                            pp.splice(i++, 0, ["C"][concat](pi.splice(0, 6)));
                        }
                        pp.splice(i, 1);
                        ii = mmax(p[length], p2 && p2[length] || 0);
                    }
                },
                fixM = function (path1, path2, a1, a2, i) {
                    if (path1 && path2 && path1[i][0] == "M" && path2[i][0] != "M") {
                        path2.splice(i, 0, ["M", a2.x, a2.y]);
                        a1.bx = 0;
                        a1.by = 0;
                        a1.x = path1[i][1];
                        a1.y = path1[i][2];
                        ii = mmax(p[length], p2 && p2[length] || 0);
                    }
                };
            for (var i = 0, ii = mmax(p[length], p2 && p2[length] || 0); i < ii; i++) {
                p[i] = processPath(p[i], attrs);
                fixArc(p, i);
                p2 && (p2[i] = processPath(p2[i], attrs2));
                p2 && fixArc(p2, i);
                fixM(p, p2, attrs, attrs2, i);
                fixM(p2, p, attrs2, attrs, i);
                var seg = p[i],
                    seg2 = p2 && p2[i],
                    seglen = seg[length],
                    seg2len = p2 && seg2[length];
                attrs.x = seg[seglen - 2];
                attrs.y = seg[seglen - 1];
                attrs.bx = toFloat(seg[seglen - 4]) || attrs.x;
                attrs.by = toFloat(seg[seglen - 3]) || attrs.y;
                attrs2.bx = p2 && (toFloat(seg2[seg2len - 4]) || attrs2.x);
                attrs2.by = p2 && (toFloat(seg2[seg2len - 3]) || attrs2.y);
                attrs2.x = p2 && seg2[seg2len - 2];
                attrs2.y = p2 && seg2[seg2len - 1];
            }
            return p2 ? [p, p2] : p;
        }, null, pathClone),
        parseDots = cacher(function (gradient) {
            var dots = [];
            for (var i = 0, ii = gradient[length]; i < ii; i++) {
                var dot = {},
                    par = gradient[i].match(/^([^:]*):?([\d\.]*)/);
                dot.color = R.getRGB(par[1]);
                if (dot.color.error) {
                    return null;
                }
                dot.color = dot.color.hex;
                par[2] && (dot.offset = par[2] + "%");
                dots[push](dot);
            }
            for (i = 1, ii = dots[length] - 1; i < ii; i++) {
                if (!dots[i].offset) {
                    var start = toFloat(dots[i - 1].offset || 0),
                        end = 0;
                    for (var j = i + 1; j < ii; j++) {
                        if (dots[j].offset) {
                            end = dots[j].offset;
                            break;
                        }
                    }
                    if (!end) {
                        end = 100;
                        j = ii;
                    }
                    end = toFloat(end);
                    var d = (end - start) / (j - i + 1);
                    for (; i < j; i++) {
                        start += d;
                        dots[i].offset = start + "%";
                    }
                }
            }
            return dots;
        }),
        getContainer = function (x, y, w, h) {
            var container;
            if (R.is(x, string) || R.is(x, "object")) {
                container = R.is(x, string) ? doc.getElementById(x) : x;
                if (container.tagName) {
                    if (y == null) {
                        return {
                            container: container,
                            width: container.style.pixelWidth || container.offsetWidth,
                            height: container.style.pixelHeight || container.offsetHeight
                        };
                    } else {
                        return {container: container, width: y, height: w};
                    }
                }
            } else {
                return {container: 1, x: x, y: y, width: w, height: h};
            }
        },
        plugins = function (con, add) {
            var that = this;
            for (var prop in add) {
                if (add[has](prop) && !(prop in con)) {
                    switch (typeof add[prop]) {
                        case "function":
                            (function (f) {
                                con[prop] = con === that ? f : function () { return f[apply](that, arguments); };
                            })(add[prop]);
                        break;
                        case "object":
                            con[prop] = con[prop] || {};
                            plugins.call(this, con[prop], add[prop]);
                        break;
                        default:
                            con[prop] = add[prop];
                        break;
                    }
                }
            }
        },
        tear = function (el, paper) {
            el == paper.top && (paper.top = el.prev);
            el == paper.bottom && (paper.bottom = el.next);
            el.next && (el.next.prev = el.prev);
            el.prev && (el.prev.next = el.next);
        },
        tofront = function (el, paper) {
            if (paper.top === el) {
                return;
            }
            tear(el, paper);
            el.next = null;
            el.prev = paper.top;
            paper.top.next = el;
            paper.top = el;
        },
        toback = function (el, paper) {
            if (paper.bottom === el) {
                return;
            }
            tear(el, paper);
            el.next = paper.bottom;
            el.prev = null;
            paper.bottom.prev = el;
            paper.bottom = el;
        },
        insertafter = function (el, el2, paper) {
            tear(el, paper);
            el2 == paper.top && (paper.top = el);
            el2.next && (el2.next.prev = el);
            el.next = el2.next;
            el.prev = el2;
            el2.next = el;
        },
        insertbefore = function (el, el2, paper) {
            tear(el, paper);
            el2 == paper.bottom && (paper.bottom = el);
            el2.prev && (el2.prev.next = el);
            el.prev = el2.prev;
            el2.prev = el;
            el.next = el2;
        },
        removed = function (methodname) {
            return function () {
                throw new Error("Rapha\xebl: you are calling to method \u201c" + methodname + "\u201d of removed object");
            };
        };
    R.pathToRelative = pathToRelative;
    // SVG
    if (R.svg) {
        paperproto.svgns = "http://www.w3.org/2000/svg";
        paperproto.xlink = "http://www.w3.org/1999/xlink";
        round = function (num) {
            return +num + (~~num === num) * .5;
        };
        var $ = function (el, attr) {
            if (attr) {
                for (var key in attr) {
                    if (attr[has](key)) {
                        setAttr(el, key, Str(attr[key]));
                    }
                }
            } else {
                el = doc.createElementNS(paperproto.svgns, el);
                el.style.webkitTapHighlightColor = "rgba(0,0,0,0)";
                return el;
            }
        };
        R[toString] = function () {
            return  "Your browser supports SVG.\nYou are running Rapha\xebl " + this.version;
        };
        var thePath = function (pathString, SVG) {
            var el = $("path");
            SVG.canvas && SVG.canvas[appendChild](el);
            var p = new Element(el, SVG);
            p.type = "path";
            setFillAndStroke(p, {fill: "none", stroke: "#000", path: pathString});
            return p;
        };
        var addGradientFill = function (o, gradient, SVG) {
            var type = "linear",
                fx = .5, fy = .5,
                s = o.style;
            gradient = Str(gradient)[rp](radial_gradient, function (all, _fx, _fy) {
                type = "radial";
                if (_fx && _fy) {
                    fx = toFloat(_fx);
                    fy = toFloat(_fy);
                    var dir = ((fy > .5) * 2 - 1);
                    pow(fx - .5, 2) + pow(fy - .5, 2) > .25 &&
                        (fy = math.sqrt(.25 - pow(fx - .5, 2)) * dir + .5) &&
                        fy != .5 &&
                        (fy = fy.toFixed(5) - 1e-5 * dir);
                }
                return E;
            });
            gradient = gradient[split](/\s*\-\s*/);
            if (type == "linear") {
                var angle = gradient.shift();
                angle = -toFloat(angle);
                if (isNaN(angle)) {
                    return null;
                }
                var vector = [0, 0, math.cos(angle * PI / 180), math.sin(angle * PI / 180)],
                    max = 1 / (mmax(abs(vector[2]), abs(vector[3])) || 1);
                vector[2] *= max;
                vector[3] *= max;
                if (vector[2] < 0) {
                    vector[0] = -vector[2];
                    vector[2] = 0;
                }
                if (vector[3] < 0) {
                    vector[1] = -vector[3];
                    vector[3] = 0;
                }
            }
            var dots = parseDots(gradient);
            if (!dots) {
                return null;
            }
            var id = o.getAttribute(fillString);
            id = id.match(/^url\(#(.*)\)$/);
            id && SVG.defs.removeChild(doc.getElementById(id[1]));

            var el = $(type + "Gradient");
            el.id = createUUID();
            $(el, type == "radial" ? {fx: fx, fy: fy} : {x1: vector[0], y1: vector[1], x2: vector[2], y2: vector[3]});
            SVG.defs[appendChild](el);
            for (var i = 0, ii = dots[length]; i < ii; i++) {
                var stop = $("stop");
                $(stop, {
                    offset: dots[i].offset ? dots[i].offset : !i ? "0%" : "100%",
                    "stop-color": dots[i].color || "#fff"
                });
                el[appendChild](stop);
            }
            $(o, {
                fill: "url(#" + el.id + ")",
                opacity: 1,
                "fill-opacity": 1
            });
            s.fill = E;
            s.opacity = 1;
            s.fillOpacity = 1;
            return 1;
        };
        var updatePosition = function (o) {
            var bbox = o.getBBox();
            $(o.pattern, {patternTransform: R.format("translate({0},{1})", bbox.x, bbox.y)});
        };
        var setFillAndStroke = function (o, params) {
            var dasharray = {
                    "": [0],
                    "none": [0],
                    "-": [3, 1],
                    ".": [1, 1],
                    "-.": [3, 1, 1, 1],
                    "-..": [3, 1, 1, 1, 1, 1],
                    ". ": [1, 3],
                    "- ": [4, 3],
                    "--": [8, 3],
                    "- .": [4, 3, 1, 3],
                    "--.": [8, 3, 1, 3],
                    "--..": [8, 3, 1, 3, 1, 3]
                },
                node = o.node,
                attrs = o.attrs,
                rot = o.rotate(),
                addDashes = function (o, value) {
                    value = dasharray[lowerCase.call(value)];
                    if (value) {
                        var width = o.attrs["stroke-width"] || "1",
                            butt = {round: width, square: width, butt: 0}[o.attrs["stroke-linecap"] || params["stroke-linecap"]] || 0,
                            dashes = [];
                        var i = value[length];
                        while (i--) {
                            dashes[i] = value[i] * width + ((i % 2) ? 1 : -1) * butt;
                        }
                        $(node, {"stroke-dasharray": dashes[join](",")});
                    }
                };
            params[has]("rotation") && (rot = params.rotation);
            var rotxy = Str(rot)[split](separator);
            if (!(rotxy.length - 1)) {
                rotxy = null;
            } else {
                rotxy[1] = +rotxy[1];
                rotxy[2] = +rotxy[2];
            }
            toFloat(rot) && o.rotate(0, true);
            for (var att in params) {
                if (params[has](att)) {
                    if (!availableAttrs[has](att)) {
                        continue;
                    }
                    var value = params[att];
                    attrs[att] = value;
                    switch (att) {
                        case "blur":
                            o.blur(value);
                            break;
                        case "rotation":
                            o.rotate(value, true);
                            break;
                        case "href":
                        case "title":
                        case "target":
                            var pn = node.parentNode;
                            if (lowerCase.call(pn.tagName) != "a") {
                                var hl = $("a");
                                pn.insertBefore(hl, node);
                                hl[appendChild](node);
                                pn = hl;
                            }
                            if (att == "target" && value == "blank") {
                                pn.setAttributeNS(o.paper.xlink, "show", "new");
                            } else {
                                pn.setAttributeNS(o.paper.xlink, att, value);
                            }
                            break;
                        case "cursor":
                            node.style.cursor = value;
                            break;
                        case "clip-rect":
                            var rect = Str(value)[split](separator);
                            if (rect[length] == 4) {
                                o.clip && o.clip.parentNode.parentNode.removeChild(o.clip.parentNode);
                                var el = $("clipPath"),
                                    rc = $("rect");
                                el.id = createUUID();
                                $(rc, {
                                    x: rect[0],
                                    y: rect[1],
                                    width: rect[2],
                                    height: rect[3]
                                });
                                el[appendChild](rc);
                                o.paper.defs[appendChild](el);
                                $(node, {"clip-path": "url(#" + el.id + ")"});
                                o.clip = rc;
                            }
                            if (!value) {
                                var clip = doc.getElementById(node.getAttribute("clip-path")[rp](/(^url\(#|\)$)/g, E));
                                clip && clip.parentNode.removeChild(clip);
                                $(node, {"clip-path": E});
                                delete o.clip;
                            }
                        break;
                        case "path":
                            if (o.type == "path") {
                                $(node, {d: value ? attrs.path = pathToAbsolute(value) : "M0,0"});
                            }
                            break;
                        case "width":
                            setAttr(node, att, value);
                            if (attrs.fx) {
                                att = "x";
                                value = attrs.x;
                            } else {
                                break;
                            }
                        case "x":
                            if (attrs.fx) {
                                value = -attrs.x - (attrs.width || 0);
                            }
                        case "rx":
                            if (att == "rx" && o.type == "rect") {
                                break;
                            }
                        case "cx":
                            rotxy && (att == "x" || att == "cx") && (rotxy[1] += value - attrs[att]);
                            setAttr(node, att, value);
                            o.pattern && updatePosition(o);
                            break;
                        case "height":
                            setAttr(node, att, value);
                            if (attrs.fy) {
                                att = "y";
                                value = attrs.y;
                            } else {
                                break;
                            }
                        case "y":
                            if (attrs.fy) {
                                value = -attrs.y - (attrs.height || 0);
                            }
                        case "ry":
                            if (att == "ry" && o.type == "rect") {
                                break;
                            }
                        case "cy":
                            rotxy && (att == "y" || att == "cy") && (rotxy[2] += value - attrs[att]);
                            setAttr(node, att, value);
                            o.pattern && updatePosition(o);
                            break;
                        case "r":
                            if (o.type == "rect") {
                                $(node, {rx: value, ry: value});
                            } else {
                                setAttr(node, att, value);
                            }
                            break;
                        case "src":
                            if (o.type == "image") {
                                node.setAttributeNS(o.paper.xlink, "href", value);
                            }
                            break;
                        case "stroke-width":
                            node.style.strokeWidth = value;
                            // Need following line for Firefox
                            setAttr(node, att, value);
                            if (attrs["stroke-dasharray"]) {
                                addDashes(o, attrs["stroke-dasharray"]);
                            }
                            break;
                        case "stroke-dasharray":
                            addDashes(o, value);
                            break;
                        case "translation":
                            var xy = Str(value)[split](separator);
                            xy[0] = +xy[0] || 0;
                            xy[1] = +xy[1] || 0;
                            if (rotxy) {
                                rotxy[1] += xy[0];
                                rotxy[2] += xy[1];
                            }
                            translate.call(o, xy[0], xy[1]);
                            break;
                        case "scale":
                            xy = Str(value)[split](separator);
                            o.scale(+xy[0] || 1, +xy[1] || +xy[0] || 1, isNaN(toFloat(xy[2])) ? null : +xy[2], isNaN(toFloat(xy[3])) ? null : +xy[3]);
                            break;
                        case fillString:
                            var isURL = Str(value).match(ISURL);
                            if (isURL) {
                                el = $("pattern");
                                var ig = $("image");
                                el.id = createUUID();
                                $(el, {x: 0, y: 0, patternUnits: "userSpaceOnUse", height: 1, width: 1});
                                $(ig, {x: 0, y: 0});
                                ig.setAttributeNS(o.paper.xlink, "href", isURL[1]);
                                el[appendChild](ig);

                                var img = doc.createElement("img");
                                img.style.cssText = "position:absolute;left:-9999em;top-9999em";
                                img.onload = function () {
                                    $(el, {width: this.offsetWidth, height: this.offsetHeight});
                                    $(ig, {width: this.offsetWidth, height: this.offsetHeight});
                                    doc.body.removeChild(this);
                                    o.paper.safari();
                                };
                                doc.body[appendChild](img);
                                img.src = isURL[1];
                                o.paper.defs[appendChild](el);
                                node.style.fill = "url(#" + el.id + ")";
                                $(node, {fill: "url(#" + el.id + ")"});
                                o.pattern = el;
                                o.pattern && updatePosition(o);
                                break;
                            }
                            var clr = R.getRGB(value);
                            if (!clr.error) {
                                delete params.gradient;
                                delete attrs.gradient;
                                !R.is(attrs.opacity, "undefined") &&
                                    R.is(params.opacity, "undefined") &&
                                    $(node, {opacity: attrs.opacity});
                                !R.is(attrs["fill-opacity"], "undefined") &&
                                    R.is(params["fill-opacity"], "undefined") &&
                                    $(node, {"fill-opacity": attrs["fill-opacity"]});
                            } else if ((({circle: 1, ellipse: 1})[has](o.type) || Str(value).charAt() != "r") && addGradientFill(node, value, o.paper)) {
                                attrs.gradient = value;
                                attrs.fill = "none";
                                break;
                            }
                            clr[has]("opacity") && $(node, {"fill-opacity": clr.opacity > 1 ? clr.opacity / 100 : clr.opacity});
                        case "stroke":
                            clr = R.getRGB(value);
                            setAttr(node, att, clr.hex);
                            att == "stroke" && clr[has]("opacity") && $(node, {"stroke-opacity": clr.opacity > 1 ? clr.opacity / 100 : clr.opacity});
                            break;
                        case "gradient":
                            (({circle: 1, ellipse: 1})[has](o.type) || Str(value).charAt() != "r") && addGradientFill(node, value, o.paper);
                            break;
                        case "opacity":
                            if (attrs.gradient && !attrs[has]("stroke-opacity")) {
                                $(node, {"stroke-opacity": value > 1 ? value / 100 : value});
                            }
                            // fall
                        case "fill-opacity":
                            if (attrs.gradient) {
                                var gradient = doc.getElementById(node.getAttribute(fillString)[rp](/^url\(#|\)$/g, E));
                                if (gradient) {
                                    var stops = gradient.getElementsByTagName("stop");
                                    setAttr(stops[stops[length] - 1], "stop-opacity", value);
                                }
                                break;
                            }
                        default:
                            att == "font-size" && (value = toInt(value, 10) + "px");
                            var cssrule = att[rp](/(\-.)/g, function (w) {
                                return upperCase.call(w.substring(1));
                            });
                            node.style[cssrule] = value;
                            // Need following line for Firefox
                            setAttr(node, att, value);
                            break;
                    }
                }
            }

            tuneText(o, params);
            if (rotxy) {
                o.rotate(rotxy.join(S));
            } else {
                toFloat(rot) && o.rotate(rot, true);
            }
        };
        var leading = 1.2,
        tuneText = function (el, params) {
            if (el.type != "text" || !(params[has]("text") || params[has]("font") || params[has]("font-size") || params[has]("x") || params[has]("y"))) {
                return;
            }
            var a = el.attrs,
                node = el.node,
                fontSize = node.firstChild ? toInt(doc.defaultView.getComputedStyle(node.firstChild, E).getPropertyValue("font-size"), 10) : 10;

            if (params[has]("text")) {
                a.text = params.text;
                while (node.firstChild) {
                    node.removeChild(node.firstChild);
                }
                var texts = Str(params.text)[split]("\n");
                for (var i = 0, ii = texts[length]; i < ii; i++) if (texts[i]) {
                    var tspan = $("tspan");
                    i && $(tspan, {dy: fontSize * leading, x: a.x});
                    tspan[appendChild](doc.createTextNode(texts[i]));
                    node[appendChild](tspan);
                }
            } else {
                texts = node.getElementsByTagName("tspan");
                for (i = 0, ii = texts[length]; i < ii; i++) {
                    i && $(texts[i], {dy: fontSize * leading, x: a.x});
                }
            }
            $(node, {y: a.y});
            var bb = el.getBBox(),
                dif = a.y - (bb.y + bb.height / 2);
            dif && R.is(dif, "finite") && $(node, {y: a.y + dif});
        },
        Element = function (node, svg) {
            var X = 0,
                Y = 0;
            this[0] = node;
            this.id = R._oid++;
            this.node = node;
            node.raphael = this;
            this.paper = svg;
            this.attrs = this.attrs || {};
            this.transformations = []; // rotate, translate, scale
            this._ = {
                tx: 0,
                ty: 0,
                rt: {deg: 0, cx: 0, cy: 0},
                sx: 1,
                sy: 1
            };
            !svg.bottom && (svg.bottom = this);
            this.prev = svg.top;
            svg.top && (svg.top.next = this);
            svg.top = this;
            this.next = null;
        };
        var elproto = Element[proto];
        Element[proto].rotate = function (deg, cx, cy) {
            if (this.removed) {
                return this;
            }
            if (deg == null) {
                if (this._.rt.cx) {
                    return [this._.rt.deg, this._.rt.cx, this._.rt.cy][join](S);
                }
                return this._.rt.deg;
            }
            var bbox = this.getBBox();
            deg = Str(deg)[split](separator);
            if (deg[length] - 1) {
                cx = toFloat(deg[1]);
                cy = toFloat(deg[2]);
            }
            deg = toFloat(deg[0]);
            if (cx != null && cx !== false) {
                this._.rt.deg = deg;
            } else {
                this._.rt.deg += deg;
            }
            (cy == null) && (cx = null);
            this._.rt.cx = cx;
            this._.rt.cy = cy;
            cx = cx == null ? bbox.x + bbox.width / 2 : cx;
            cy = cy == null ? bbox.y + bbox.height / 2 : cy;
            if (this._.rt.deg) {
                this.transformations[0] = R.format("rotate({0} {1} {2})", this._.rt.deg, cx, cy);
                this.clip && $(this.clip, {transform: R.format("rotate({0} {1} {2})", -this._.rt.deg, cx, cy)});
            } else {
                this.transformations[0] = E;
                this.clip && $(this.clip, {transform: E});
            }
            $(this.node, {transform: this.transformations[join](S)});
            return this;
        };
        Element[proto].hide = function () {
            !this.removed && (this.node.style.display = "none");
            return this;
        };
        Element[proto].show = function () {
            !this.removed && (this.node.style.display = "");
            return this;
        };
        Element[proto].remove = function () {
            if (this.removed) {
                return;
            }
            tear(this, this.paper);
            this.node.parentNode.removeChild(this.node);
            for (var i in this) {
                delete this[i];
            }
            this.removed = true;
        };
        Element[proto].getBBox = function () {
            if (this.removed) {
                return this;
            }
            if (this.type == "path") {
                return pathDimensions(this.attrs.path);
            }
            if (this.node.style.display == "none") {
                this.show();
                var hide = true;
            }
            var bbox = {};
            try {
                bbox = this.node.getBBox();
            } catch(e) {
                // Firefox 3.0.x plays badly here
            } finally {
                bbox = bbox || {};
            }
            if (this.type == "text") {
                bbox = {x: bbox.x, y: Infinity, width: 0, height: 0};
                for (var i = 0, ii = this.node.getNumberOfChars(); i < ii; i++) {
                    var bb = this.node.getExtentOfChar(i);
                    (bb.y < bbox.y) && (bbox.y = bb.y);
                    (bb.y + bb.height - bbox.y > bbox.height) && (bbox.height = bb.y + bb.height - bbox.y);
                    (bb.x + bb.width - bbox.x > bbox.width) && (bbox.width = bb.x + bb.width - bbox.x);
                }
            }
            hide && this.hide();
            return bbox;
        };
        Element[proto].attr = function (name, value) {
            if (this.removed) {
                return this;
            }
            if (name == null) {
                var res = {};
                for (var i in this.attrs) if (this.attrs[has](i)) {
                    res[i] = this.attrs[i];
                }
                this._.rt.deg && (res.rotation = this.rotate());
                (this._.sx != 1 || this._.sy != 1) && (res.scale = this.scale());
                res.gradient && res.fill == "none" && (res.fill = res.gradient) && delete res.gradient;
                return res;
            }
            if (value == null && R.is(name, string)) {
                if (name == "translation") {
                    return translate.call(this);
                }
                if (name == "rotation") {
                    return this.rotate();
                }
                if (name == "scale") {
                    return this.scale();
                }
                if (name == fillString && this.attrs.fill == "none" && this.attrs.gradient) {
                    return this.attrs.gradient;
                }
                return this.attrs[name];
            }
            if (value == null && R.is(name, array)) {
                var values = {};
                for (var j = 0, jj = name.length; j < jj; j++) {
                    values[name[j]] = this.attr(name[j]);
                }
                return values;
            }
            if (value != null) {
                var params = {};
                params[name] = value;
            } else if (name != null && R.is(name, "object")) {
                params = name;
            }
            for (var key in this.paper.customAttributes) if (this.paper.customAttributes[has](key) && params[has](key) && R.is(this.paper.customAttributes[key], "function")) {
                var par = this.paper.customAttributes[key].apply(this, [][concat](params[key]));
                this.attrs[key] = params[key];
                for (var subkey in par) if (par[has](subkey)) {
                    params[subkey] = par[subkey];
                }
            }
            setFillAndStroke(this, params);
            return this;
        };
        Element[proto].toFront = function () {
            if (this.removed) {
                return this;
            }
            this.node.parentNode[appendChild](this.node);
            var svg = this.paper;
            svg.top != this && tofront(this, svg);
            return this;
        };
        Element[proto].toBack = function () {
            if (this.removed) {
                return this;
            }
            if (this.node.parentNode.firstChild != this.node) {
                this.node.parentNode.insertBefore(this.node, this.node.parentNode.firstChild);
                toback(this, this.paper);
                var svg = this.paper;
            }
            return this;
        };
        Element[proto].insertAfter = function (element) {
            if (this.removed) {
                return this;
            }
            var node = element.node || element[element.length - 1].node;
            if (node.nextSibling) {
                node.parentNode.insertBefore(this.node, node.nextSibling);
            } else {
                node.parentNode[appendChild](this.node);
            }
            insertafter(this, element, this.paper);
            return this;
        };
        Element[proto].insertBefore = function (element) {
            if (this.removed) {
                return this;
            }
            var node = element.node || element[0].node;
            node.parentNode.insertBefore(this.node, node);
            insertbefore(this, element, this.paper);
            return this;
        };
        Element[proto].blur = function (size) {
            // Experimental. No Safari support. Use it on your own risk.
            var t = this;
            if (+size !== 0) {
                var fltr = $("filter"),
                    blur = $("feGaussianBlur");
                t.attrs.blur = size;
                fltr.id = createUUID();
                $(blur, {stdDeviation: +size || 1.5});
                fltr.appendChild(blur);
                t.paper.defs.appendChild(fltr);
                t._blur = fltr;
                $(t.node, {filter: "url(#" + fltr.id + ")"});
            } else {
                if (t._blur) {
                    t._blur.parentNode.removeChild(t._blur);
                    delete t._blur;
                    delete t.attrs.blur;
                }
                t.node.removeAttribute("filter");
            }
        };
        var theCircle = function (svg, x, y, r) {
            var el = $("circle");
            svg.canvas && svg.canvas[appendChild](el);
            var res = new Element(el, svg);
            res.attrs = {cx: x, cy: y, r: r, fill: "none", stroke: "#000"};
            res.type = "circle";
            $(el, res.attrs);
            return res;
        },
        theRect = function (svg, x, y, w, h, r) {
            var el = $("rect");
            svg.canvas && svg.canvas[appendChild](el);
            var res = new Element(el, svg);
            res.attrs = {x: x, y: y, width: w, height: h, r: r || 0, rx: r || 0, ry: r || 0, fill: "none", stroke: "#000"};
            res.type = "rect";
            $(el, res.attrs);
            return res;
        },
        theEllipse = function (svg, x, y, rx, ry) {
            var el = $("ellipse");
            svg.canvas && svg.canvas[appendChild](el);
            var res = new Element(el, svg);
            res.attrs = {cx: x, cy: y, rx: rx, ry: ry, fill: "none", stroke: "#000"};
            res.type = "ellipse";
            $(el, res.attrs);
            return res;
        },
        theImage = function (svg, src, x, y, w, h) {
            var el = $("image");
            $(el, {x: x, y: y, width: w, height: h, preserveAspectRatio: "none"});
            el.setAttributeNS(svg.xlink, "href", src);
            svg.canvas && svg.canvas[appendChild](el);
            var res = new Element(el, svg);
            res.attrs = {x: x, y: y, width: w, height: h, src: src};
            res.type = "image";
            return res;
        },
        theText = function (svg, x, y, text) {
            var el = $("text");
            $(el, {x: x, y: y, "text-anchor": "middle"});
            svg.canvas && svg.canvas[appendChild](el);
            var res = new Element(el, svg);
            res.attrs = {x: x, y: y, "text-anchor": "middle", text: text, font: availableAttrs.font, stroke: "none", fill: "#000"};
            res.type = "text";
            setFillAndStroke(res, res.attrs);
            return res;
        },
        setSize = function (width, height) {
            this.width = width || this.width;
            this.height = height || this.height;
            setAttr(this.canvas, "width", this.width);
            setAttr(this.canvas, "height", this.height);
            return this;
        },
        create = function () {
            var con = getContainer[apply](0, arguments),
                container = con && con.container,
                x = con.x,
                y = con.y,
                width = con.width,
                height = con.height;
            if (!container) {
                throw new Error("SVG container not found.");
            }
            var cnvs = $("svg");
            x = x || 0;
            y = y || 0;
            width = width || 512;
            height = height || 342;
            $(cnvs, {
                xmlns: "http://www.w3.org/2000/svg",
                version: 1.1,
                width: width,
                height: height
            });
            if (container == 1) {
                cnvs.style.cssText = "position:absolute;left:" + x + "px;top:" + y + "px";
                doc.body[appendChild](cnvs);
            } else {
                if (container.firstChild) {
                    container.insertBefore(cnvs, container.firstChild);
                } else {
                    container[appendChild](cnvs);
                }
            }
            container = new Paper;
            container.width = width;
            container.height = height;
            container.canvas = cnvs;
            plugins.call(container, container, R.fn);
            container.clear();
            return container;
        };
        paperproto.clear = function () {
            var c = this.canvas;
            while (c.firstChild) {
                c.removeChild(c.firstChild);
            }
            this.bottom = this.top = null;
            (this.desc = $("desc"))[appendChild](doc.createTextNode("Created with Rapha\xebl"));
            c[appendChild](this.desc);
            c[appendChild](this.defs = $("defs"));
        };
        paperproto.remove = function () {
            this.canvas.parentNode && this.canvas.parentNode.removeChild(this.canvas);
            for (var i in this) {
                this[i] = removed(i);
            }
        };
    }

    // VML
    if (R.vml) {
        var map = {M: "m", L: "l", C: "c", Z: "x", m: "t", l: "r", c: "v", z: "x"},
            bites = /([clmz]),?([^clmz]*)/gi,
            blurregexp = / progid:\S+Blur\([^\)]+\)/g,
            val = /-?[^,\s-]+/g,
            coordsize = 1e3 + S + 1e3,
            zoom = 10,
            pathlike = {path: 1, rect: 1},
            path2vml = function (path) {
                var total =  /[ahqstv]/ig,
                    command = pathToAbsolute;
                Str(path).match(total) && (command = path2curve);
                total = /[clmz]/g;
                if (command == pathToAbsolute && !Str(path).match(total)) {
                    var res = Str(path)[rp](bites, function (all, command, args) {
                        var vals = [],
                            isMove = lowerCase.call(command) == "m",
                            res = map[command];
                        args[rp](val, function (value) {
                            if (isMove && vals[length] == 2) {
                                res += vals + map[command == "m" ? "l" : "L"];
                                vals = [];
                            }
                            vals[push](round(value * zoom));
                        });
                        return res + vals;
                    });
                    return res;
                }
                var pa = command(path), p, r;
                res = [];
                for (var i = 0, ii = pa[length]; i < ii; i++) {
                    p = pa[i];
                    r = lowerCase.call(pa[i][0]);
                    r == "z" && (r = "x");
                    for (var j = 1, jj = p[length]; j < jj; j++) {
                        r += round(p[j] * zoom) + (j != jj - 1 ? "," : E);
                    }
                    res[push](r);
                }
                return res[join](S);
            };

        R[toString] = function () {
            return  "Your browser doesn\u2019t support SVG. Falling down to VML.\nYou are running Rapha\xebl " + this.version;
        };
        thePath = function (pathString, vml) {
            var g = createNode("group");
            g.style.cssText = "position:absolute;left:0;top:0;width:" + vml.width + "px;height:" + vml.height + "px";
            g.coordsize = vml.coordsize;
            g.coordorigin = vml.coordorigin;
            var el = createNode("shape"), ol = el.style;
            ol.width = vml.width + "px";
            ol.height = vml.height + "px";
            el.coordsize = coordsize;
            el.coordorigin = vml.coordorigin;
            g[appendChild](el);
            var p = new Element(el, g, vml),
                attr = {fill: "none", stroke: "#000"};
            pathString && (attr.path = pathString);
            p.type = "path";
            p.path = [];
            p.Path = E;
            setFillAndStroke(p, attr);
            vml.canvas[appendChild](g);
            return p;
        };
        setFillAndStroke = function (o, params) {
            o.attrs = o.attrs || {};
            var node = o.node,
                a = o.attrs,
                s = node.style,
                xy,
                newpath = (params.x != a.x || params.y != a.y || params.width != a.width || params.height != a.height || params.r != a.r) && o.type == "rect",
                res = o;

            for (var par in params) if (params[has](par)) {
                a[par] = params[par];
            }
            if (newpath) {
                a.path = rectPath(a.x, a.y, a.width, a.height, a.r);
                o.X = a.x;
                o.Y = a.y;
                o.W = a.width;
                o.H = a.height;
            }
            params.href && (node.href = params.href);
            params.title && (node.title = params.title);
            params.target && (node.target = params.target);
            params.cursor && (s.cursor = params.cursor);
            "blur" in params && o.blur(params.blur);
            if (params.path && o.type == "path" || newpath) {
                node.path = path2vml(a.path);
            }
            if (params.rotation != null) {
                o.rotate(params.rotation, true);
            }
            if (params.translation) {
                xy = Str(params.translation)[split](separator);
                translate.call(o, xy[0], xy[1]);
                if (o._.rt.cx != null) {
                    o._.rt.cx +=+ xy[0];
                    o._.rt.cy +=+ xy[1];
                    o.setBox(o.attrs, xy[0], xy[1]);
                }
            }
            if (params.scale) {
                xy = Str(params.scale)[split](separator);
                o.scale(+xy[0] || 1, +xy[1] || +xy[0] || 1, +xy[2] || null, +xy[3] || null);
            }
            if ("clip-rect" in params) {
                var rect = Str(params["clip-rect"])[split](separator);
                if (rect[length] == 4) {
                    rect[2] = +rect[2] + (+rect[0]);
                    rect[3] = +rect[3] + (+rect[1]);
                    var div = node.clipRect || doc.createElement("div"),
                        dstyle = div.style,
                        group = node.parentNode;
                    dstyle.clip = R.format("rect({1}px {2}px {3}px {0}px)", rect);
                    if (!node.clipRect) {
                        dstyle.position = "absolute";
                        dstyle.top = 0;
                        dstyle.left = 0;
                        dstyle.width = o.paper.width + "px";
                        dstyle.height = o.paper.height + "px";
                        group.parentNode.insertBefore(div, group);
                        div[appendChild](group);
                        node.clipRect = div;
                    }
                }
                if (!params["clip-rect"]) {
                    node.clipRect && (node.clipRect.style.clip = E);
                }
            }
            if (o.type == "image" && params.src) {
                node.src = params.src;
            }
            if (o.type == "image" && params.opacity) {
                node.filterOpacity = ms + ".Alpha(opacity=" + (params.opacity * 100) + ")";
                s.filter = (node.filterMatrix || E) + (node.filterOpacity || E);
            }
            params.font && (s.font = params.font);
            params["font-family"] && (s.fontFamily = '"' + params["font-family"][split](",")[0][rp](/^['"]+|['"]+$/g, E) + '"');
            params["font-size"] && (s.fontSize = params["font-size"]);
            params["font-weight"] && (s.fontWeight = params["font-weight"]);
            params["font-style"] && (s.fontStyle = params["font-style"]);
            if (params.opacity != null ||
                params["stroke-width"] != null ||
                params.fill != null ||
                params.stroke != null ||
                params["stroke-width"] != null ||
                params["stroke-opacity"] != null ||
                params["fill-opacity"] != null ||
                params["stroke-dasharray"] != null ||
                params["stroke-miterlimit"] != null ||
                params["stroke-linejoin"] != null ||
                params["stroke-linecap"] != null) {
                node = o.shape || node;
                var fill = (node.getElementsByTagName(fillString) && node.getElementsByTagName(fillString)[0]),
                    newfill = false;
                !fill && (newfill = fill = createNode(fillString));
                if ("fill-opacity" in params || "opacity" in params) {
                    var opacity = ((+a["fill-opacity"] + 1 || 2) - 1) * ((+a.opacity + 1 || 2) - 1) * ((+R.getRGB(params.fill).o + 1 || 2) - 1);
                    opacity = mmin(mmax(opacity, 0), 1);
                    fill.opacity = opacity;
                }
                params.fill && (fill.on = true);
                if (fill.on == null || params.fill == "none") {
                    fill.on = false;
                }
                if (fill.on && params.fill) {
                    var isURL = params.fill.match(ISURL);
                    if (isURL) {
                        fill.src = isURL[1];
                        fill.type = "tile";
                    } else {
                        fill.color = R.getRGB(params.fill).hex;
                        fill.src = E;
                        fill.type = "solid";
                        if (R.getRGB(params.fill).error && (res.type in {circle: 1, ellipse: 1} || Str(params.fill).charAt() != "r") && addGradientFill(res, params.fill)) {
                            a.fill = "none";
                            a.gradient = params.fill;
                        }
                    }
                }
                newfill && node[appendChild](fill);
                var stroke = (node.getElementsByTagName("stroke") && node.getElementsByTagName("stroke")[0]),
                newstroke = false;
                !stroke && (newstroke = stroke = createNode("stroke"));
                if ((params.stroke && params.stroke != "none") ||
                    params["stroke-width"] ||
                    params["stroke-opacity"] != null ||
                    params["stroke-dasharray"] ||
                    params["stroke-miterlimit"] ||
                    params["stroke-linejoin"] ||
                    params["stroke-linecap"]) {
                    stroke.on = true;
                }
                (params.stroke == "none" || stroke.on == null || params.stroke == 0 || params["stroke-width"] == 0) && (stroke.on = false);
                var strokeColor = R.getRGB(params.stroke);
                stroke.on && params.stroke && (stroke.color = strokeColor.hex);
                opacity = ((+a["stroke-opacity"] + 1 || 2) - 1) * ((+a.opacity + 1 || 2) - 1) * ((+strokeColor.o + 1 || 2) - 1);
                var width = (toFloat(params["stroke-width"]) || 1) * .75;
                opacity = mmin(mmax(opacity, 0), 1);
                params["stroke-width"] == null && (width = a["stroke-width"]);
                params["stroke-width"] && (stroke.weight = width);
                width && width < 1 && (opacity *= width) && (stroke.weight = 1);
                stroke.opacity = opacity;

                params["stroke-linejoin"] && (stroke.joinstyle = params["stroke-linejoin"] || "miter");
                stroke.miterlimit = params["stroke-miterlimit"] || 8;
                params["stroke-linecap"] && (stroke.endcap = params["stroke-linecap"] == "butt" ? "flat" : params["stroke-linecap"] == "square" ? "square" : "round");
                if (params["stroke-dasharray"]) {
                    var dasharray = {
                        "-": "shortdash",
                        ".": "shortdot",
                        "-.": "shortdashdot",
                        "-..": "shortdashdotdot",
                        ". ": "dot",
                        "- ": "dash",
                        "--": "longdash",
                        "- .": "dashdot",
                        "--.": "longdashdot",
                        "--..": "longdashdotdot"
                    };
                    stroke.dashstyle = dasharray[has](params["stroke-dasharray"]) ? dasharray[params["stroke-dasharray"]] : E;
                }
                newstroke && node[appendChild](stroke);
            }
            if (res.type == "text") {
                s = res.paper.span.style;
                a.font && (s.font = a.font);
                a["font-family"] && (s.fontFamily = a["font-family"]);
                a["font-size"] && (s.fontSize = a["font-size"]);
                a["font-weight"] && (s.fontWeight = a["font-weight"]);
                a["font-style"] && (s.fontStyle = a["font-style"]);
                res.node.string && (res.paper.span.innerHTML = Str(res.node.string)[rp](/</g, "&#60;")[rp](/&/g, "&#38;")[rp](/\n/g, "<br>"));
                res.W = a.w = res.paper.span.offsetWidth;
                res.H = a.h = res.paper.span.offsetHeight;
                res.X = a.x;
                res.Y = a.y + round(res.H / 2);

                // text-anchor emulationm
                switch (a["text-anchor"]) {
                    case "start":
                        res.node.style["v-text-align"] = "left";
                        res.bbx = round(res.W / 2);
                    break;
                    case "end":
                        res.node.style["v-text-align"] = "right";
                        res.bbx = -round(res.W / 2);
                    break;
                    default:
                        res.node.style["v-text-align"] = "center";
                    break;
                }
            }
        };
        addGradientFill = function (o, gradient) {
            o.attrs = o.attrs || {};
            var attrs = o.attrs,
                fill,
                type = "linear",
                fxfy = ".5 .5";
            o.attrs.gradient = gradient;
            gradient = Str(gradient)[rp](radial_gradient, function (all, fx, fy) {
                type = "radial";
                if (fx && fy) {
                    fx = toFloat(fx);
                    fy = toFloat(fy);
                    pow(fx - .5, 2) + pow(fy - .5, 2) > .25 && (fy = math.sqrt(.25 - pow(fx - .5, 2)) * ((fy > .5) * 2 - 1) + .5);
                    fxfy = fx + S + fy;
                }
                return E;
            });
            gradient = gradient[split](/\s*\-\s*/);
            if (type == "linear") {
                var angle = gradient.shift();
                angle = -toFloat(angle);
                if (isNaN(angle)) {
                    return null;
                }
            }
            var dots = parseDots(gradient);
            if (!dots) {
                return null;
            }
            o = o.shape || o.node;
            fill = o.getElementsByTagName(fillString)[0] || createNode(fillString);
            !fill.parentNode && o.appendChild(fill);
            if (dots[length]) {
                fill.on = true;
                fill.method = "none";
                fill.color = dots[0].color;
                fill.color2 = dots[dots[length] - 1].color;
                var clrs = [];
                for (var i = 0, ii = dots[length]; i < ii; i++) {
                    dots[i].offset && clrs[push](dots[i].offset + S + dots[i].color);
                }
                fill.colors && (fill.colors.value = clrs[length] ? clrs[join]() : "0% " + fill.color);
                if (type == "radial") {
                    fill.type = "gradientradial";
                    fill.focus = "100%";
                    fill.focussize = fxfy;
                    fill.focusposition = fxfy;
                } else {
                    fill.type = "gradient";
                    fill.angle = (270 - angle) % 360;
                }
            }
            return 1;
        };
        Element = function (node, group, vml) {
            var Rotation = 0,
                RotX = 0,
                RotY = 0,
                Scale = 1;
            this[0] = node;
            this.id = R._oid++;
            this.node = node;
            node.raphael = this;
            this.X = 0;
            this.Y = 0;
            this.attrs = {};
            this.Group = group;
            this.paper = vml;
            this._ = {
                tx: 0,
                ty: 0,
                rt: {deg:0},
                sx: 1,
                sy: 1
            };
            !vml.bottom && (vml.bottom = this);
            this.prev = vml.top;
            vml.top && (vml.top.next = this);
            vml.top = this;
            this.next = null;
        };
        elproto = Element[proto];
        elproto.rotate = function (deg, cx, cy) {
            if (this.removed) {
                return this;
            }
            if (deg == null) {
                if (this._.rt.cx) {
                    return [this._.rt.deg, this._.rt.cx, this._.rt.cy][join](S);
                }
                return this._.rt.deg;
            }
            deg = Str(deg)[split](separator);
            if (deg[length] - 1) {
                cx = toFloat(deg[1]);
                cy = toFloat(deg[2]);
            }
            deg = toFloat(deg[0]);
            if (cx != null) {
                this._.rt.deg = deg;
            } else {
                this._.rt.deg += deg;
            }
            cy == null && (cx = null);
            this._.rt.cx = cx;
            this._.rt.cy = cy;
            this.setBox(this.attrs, cx, cy);
            this.Group.style.rotation = this._.rt.deg;
            // gradient fix for rotation. TODO
            // var fill = (this.shape || this.node).getElementsByTagName(fillString);
            // fill = fill[0] || {};
            // var b = ((360 - this._.rt.deg) - 270) % 360;
            // !R.is(fill.angle, "undefined") && (fill.angle = b);
            return this;
        };
        elproto.setBox = function (params, cx, cy) {
            if (this.removed) {
                return this;
            }
            var gs = this.Group.style,
                os = (this.shape && this.shape.style) || this.node.style;
            params = params || {};
            for (var i in params) if (params[has](i)) {
                this.attrs[i] = params[i];
            }
            cx = cx || this._.rt.cx;
            cy = cy || this._.rt.cy;
            var attr = this.attrs,
                x,
                y,
                w,
                h;
            switch (this.type) {
                case "circle":
                    x = attr.cx - attr.r;
                    y = attr.cy - attr.r;
                    w = h = attr.r * 2;
                    break;
                case "ellipse":
                    x = attr.cx - attr.rx;
                    y = attr.cy - attr.ry;
                    w = attr.rx * 2;
                    h = attr.ry * 2;
                    break;
                case "image":
                    x = +attr.x;
                    y = +attr.y;
                    w = attr.width || 0;
                    h = attr.height || 0;
                    break;
                case "text":
                    this.textpath.v = ["m", round(attr.x), ", ", round(attr.y - 2), "l", round(attr.x) + 1, ", ", round(attr.y - 2)][join](E);
                    x = attr.x - round(this.W / 2);
                    y = attr.y - this.H / 2;
                    w = this.W;
                    h = this.H;
                    break;
                case "rect":
                case "path":
                    if (!this.attrs.path) {
                        x = 0;
                        y = 0;
                        w = this.paper.width;
                        h = this.paper.height;
                    } else {
                        var dim = pathDimensions(this.attrs.path);
                        x = dim.x;
                        y = dim.y;
                        w = dim.width;
                        h = dim.height;
                    }
                    break;
                default:
                    x = 0;
                    y = 0;
                    w = this.paper.width;
                    h = this.paper.height;
                    break;
            }
            cx = (cx == null) ? x + w / 2 : cx;
            cy = (cy == null) ? y + h / 2 : cy;
            var left = cx - this.paper.width / 2,
                top = cy - this.paper.height / 2, t;
            gs.left != (t = left + "px") && (gs.left = t);
            gs.top != (t = top + "px") && (gs.top = t);
            this.X = pathlike[has](this.type) ? -left : x;
            this.Y = pathlike[has](this.type) ? -top : y;
            this.W = w;
            this.H = h;
            if (pathlike[has](this.type)) {
                os.left != (t = -left * zoom + "px") && (os.left = t);
                os.top != (t = -top * zoom + "px") && (os.top = t);
            } else if (this.type == "text") {
                os.left != (t = -left + "px") && (os.left = t);
                os.top != (t = -top + "px") && (os.top = t);
            } else {
                gs.width != (t = this.paper.width + "px") && (gs.width = t);
                gs.height != (t = this.paper.height + "px") && (gs.height = t);
                os.left != (t = x - left + "px") && (os.left = t);
                os.top != (t = y - top + "px") && (os.top = t);
                os.width != (t = w + "px") && (os.width = t);
                os.height != (t = h + "px") && (os.height = t);
            }
        };
        elproto.hide = function () {
            !this.removed && (this.Group.style.display = "none");
            return this;
        };
        elproto.show = function () {
            !this.removed && (this.Group.style.display = "block");
            return this;
        };
        elproto.getBBox = function () {
            if (this.removed) {
                return this;
            }
            if (pathlike[has](this.type)) {
                return pathDimensions(this.attrs.path);
            }
            return {
                x: this.X + (this.bbx || 0),
                y: this.Y,
                width: this.W,
                height: this.H
            };
        };
        elproto.remove = function () {
            if (this.removed) {
                return;
            }
            tear(this, this.paper);
            this.node.parentNode.removeChild(this.node);
            this.Group.parentNode.removeChild(this.Group);
            this.shape && this.shape.parentNode.removeChild(this.shape);
            for (var i in this) {
                delete this[i];
            }
            this.removed = true;
        };
        elproto.attr = function (name, value) {
            if (this.removed) {
                return this;
            }
            if (name == null) {
                var res = {};
                for (var i in this.attrs) if (this.attrs[has](i)) {
                    res[i] = this.attrs[i];
                }
                this._.rt.deg && (res.rotation = this.rotate());
                (this._.sx != 1 || this._.sy != 1) && (res.scale = this.scale());
                res.gradient && res.fill == "none" && (res.fill = res.gradient) && delete res.gradient;
                return res;
            }
            if (value == null && R.is(name, "string")) {
                if (name == "translation") {
                    return translate.call(this);
                }
                if (name == "rotation") {
                    return this.rotate();
                }
                if (name == "scale") {
                    return this.scale();
                }
                if (name == fillString && this.attrs.fill == "none" && this.attrs.gradient) {
                    return this.attrs.gradient;
                }
                return this.attrs[name];
            }
            if (this.attrs && value == null && R.is(name, array)) {
                var ii, values = {};
                for (i = 0, ii = name[length]; i < ii; i++) {
                    values[name[i]] = this.attr(name[i]);
                }
                return values;
            }
            var params;
            if (value != null) {
                params = {};
                params[name] = value;
            }
            value == null && R.is(name, "object") && (params = name);
            if (params) {
                for (var key in this.paper.customAttributes) if (this.paper.customAttributes[has](key) && params[has](key) && R.is(this.paper.customAttributes[key], "function")) {
                    var par = this.paper.customAttributes[key].apply(this, [][concat](params[key]));
                    this.attrs[key] = params[key];
                    for (var subkey in par) if (par[has](subkey)) {
                        params[subkey] = par[subkey];
                    }
                }
                if (params.text && this.type == "text") {
                    this.node.string = params.text;
                }
                setFillAndStroke(this, params);
                if (params.gradient && (({circle: 1, ellipse: 1})[has](this.type) || Str(params.gradient).charAt() != "r")) {
                    addGradientFill(this, params.gradient);
                }
                (!pathlike[has](this.type) || this._.rt.deg) && this.setBox(this.attrs);
            }
            return this;
        };
        elproto.toFront = function () {
            !this.removed && this.Group.parentNode[appendChild](this.Group);
            this.paper.top != this && tofront(this, this.paper);
            return this;
        };
        elproto.toBack = function () {
            if (this.removed) {
                return this;
            }
            if (this.Group.parentNode.firstChild != this.Group) {
                this.Group.parentNode.insertBefore(this.Group, this.Group.parentNode.firstChild);
                toback(this, this.paper);
            }
            return this;
        };
        elproto.insertAfter = function (element) {
            if (this.removed) {
                return this;
            }
            if (element.constructor == Set) {
                element = element[element.length - 1];
            }
            if (element.Group.nextSibling) {
                element.Group.parentNode.insertBefore(this.Group, element.Group.nextSibling);
            } else {
                element.Group.parentNode[appendChild](this.Group);
            }
            insertafter(this, element, this.paper);
            return this;
        };
        elproto.insertBefore = function (element) {
            if (this.removed) {
                return this;
            }
            if (element.constructor == Set) {
                element = element[0];
            }
            element.Group.parentNode.insertBefore(this.Group, element.Group);
            insertbefore(this, element, this.paper);
            return this;
        };
        elproto.blur = function (size) {
            var s = this.node.runtimeStyle,
                f = s.filter;
            f = f.replace(blurregexp, E);
            if (+size !== 0) {
                this.attrs.blur = size;
                s.filter = f + S + ms + ".Blur(pixelradius=" + (+size || 1.5) + ")";
                s.margin = R.format("-{0}px 0 0 -{0}px", round(+size || 1.5));
            } else {
                s.filter = f;
                s.margin = 0;
                delete this.attrs.blur;
            }
        };

        theCircle = function (vml, x, y, r) {
            var g = createNode("group"),
                o = createNode("oval"),
                ol = o.style;
            g.style.cssText = "position:absolute;left:0;top:0;width:" + vml.width + "px;height:" + vml.height + "px";
            g.coordsize = coordsize;
            g.coordorigin = vml.coordorigin;
            g[appendChild](o);
            var res = new Element(o, g, vml);
            res.type = "circle";
            setFillAndStroke(res, {stroke: "#000", fill: "none"});
            res.attrs.cx = x;
            res.attrs.cy = y;
            res.attrs.r = r;
            res.setBox({x: x - r, y: y - r, width: r * 2, height: r * 2});
            vml.canvas[appendChild](g);
            return res;
        };
        function rectPath(x, y, w, h, r) {
            if (r) {
                return R.format("M{0},{1}l{2},0a{3},{3},0,0,1,{3},{3}l0,{5}a{3},{3},0,0,1,{4},{3}l{6},0a{3},{3},0,0,1,{4},{4}l0,{7}a{3},{3},0,0,1,{3},{4}z", x + r, y, w - r * 2, r, -r, h - r * 2, r * 2 - w, r * 2 - h);
            } else {
                return R.format("M{0},{1}l{2},0,0,{3},{4},0z", x, y, w, h, -w);
            }
        }
        theRect = function (vml, x, y, w, h, r) {
            var path = rectPath(x, y, w, h, r),
                res = vml.path(path),
                a = res.attrs;
            res.X = a.x = x;
            res.Y = a.y = y;
            res.W = a.width = w;
            res.H = a.height = h;
            a.r = r;
            a.path = path;
            res.type = "rect";
            return res;
        };
        theEllipse = function (vml, x, y, rx, ry) {
            var g = createNode("group"),
                o = createNode("oval"),
                ol = o.style;
            g.style.cssText = "position:absolute;left:0;top:0;width:" + vml.width + "px;height:" + vml.height + "px";
            g.coordsize = coordsize;
            g.coordorigin = vml.coordorigin;
            g[appendChild](o);
            var res = new Element(o, g, vml);
            res.type = "ellipse";
            setFillAndStroke(res, {stroke: "#000"});
            res.attrs.cx = x;
            res.attrs.cy = y;
            res.attrs.rx = rx;
            res.attrs.ry = ry;
            res.setBox({x: x - rx, y: y - ry, width: rx * 2, height: ry * 2});
            vml.canvas[appendChild](g);
            return res;
        };
        theImage = function (vml, src, x, y, w, h) {
            var g = createNode("group"),
                o = createNode("image");
            g.style.cssText = "position:absolute;left:0;top:0;width:" + vml.width + "px;height:" + vml.height + "px";
            g.coordsize = coordsize;
            g.coordorigin = vml.coordorigin;
            o.src = src;
            g[appendChild](o);
            var res = new Element(o, g, vml);
            res.type = "image";
            res.attrs.src = src;
            res.attrs.x = x;
            res.attrs.y = y;
            res.attrs.w = w;
            res.attrs.h = h;
            res.setBox({x: x, y: y, width: w, height: h});
            vml.canvas[appendChild](g);
            return res;
        };
        theText = function (vml, x, y, text) {
            var g = createNode("group"),
                el = createNode("shape"),
                ol = el.style,
                path = createNode("path"),
                ps = path.style,
                o = createNode("textpath");
            g.style.cssText = "position:absolute;left:0;top:0;width:" + vml.width + "px;height:" + vml.height + "px";
            g.coordsize = coordsize;
            g.coordorigin = vml.coordorigin;
            path.v = R.format("m{0},{1}l{2},{1}", round(x * 10), round(y * 10), round(x * 10) + 1);
            path.textpathok = true;
            ol.width = vml.width;
            ol.height = vml.height;
            o.string = Str(text);
            o.on = true;
            el[appendChild](o);
            el[appendChild](path);
            g[appendChild](el);
            var res = new Element(o, g, vml);
            res.shape = el;
            res.textpath = path;
            res.type = "text";
            res.attrs.text = text;
            res.attrs.x = x;
            res.attrs.y = y;
            res.attrs.w = 1;
            res.attrs.h = 1;
            setFillAndStroke(res, {font: availableAttrs.font, stroke: "none", fill: "#000"});
            res.setBox();
            vml.canvas[appendChild](g);
            return res;
        };
        setSize = function (width, height) {
            var cs = this.canvas.style;
            width == +width && (width += "px");
            height == +height && (height += "px");
            cs.width = width;
            cs.height = height;
            cs.clip = "rect(0 " + width + " " + height + " 0)";
            return this;
        };
        var createNode;
        doc.createStyleSheet().addRule(".rvml", "behavior:url(#default#VML)");
        try {
            !doc.namespaces.rvml && doc.namespaces.add("rvml", "urn:schemas-microsoft-com:vml");
            createNode = function (tagName) {
                return doc.createElement('<rvml:' + tagName + ' class="rvml">');
            };
        } catch (e) {
            createNode = function (tagName) {
                return doc.createElement('<' + tagName + ' xmlns="urn:schemas-microsoft.com:vml" class="rvml">');
            };
        }
        create = function () {
            var con = getContainer[apply](0, arguments),
                container = con.container,
                height = con.height,
                s,
                width = con.width,
                x = con.x,
                y = con.y;
            if (!container) {
                throw new Error("VML container not found.");
            }
            var res = new Paper,
                c = res.canvas = doc.createElement("div"),
                cs = c.style;
            x = x || 0;
            y = y || 0;
            width = width || 512;
            height = height || 342;
            width == +width && (width += "px");
            height == +height && (height += "px");
            res.width = 1e3;
            res.height = 1e3;
            res.coordsize = zoom * 1e3 + S + zoom * 1e3;
            res.coordorigin = "0 0";
            res.span = doc.createElement("span");
            res.span.style.cssText = "position:absolute;left:-9999em;top:-9999em;padding:0;margin:0;line-height:1;display:inline;";
            c[appendChild](res.span);
            cs.cssText = R.format("top:0;left:0;width:{0};height:{1};display:inline-block;position:relative;clip:rect(0 {0} {1} 0);overflow:hidden", width, height);
            if (container == 1) {
                doc.body[appendChild](c);
                cs.left = x + "px";
                cs.top = y + "px";
                cs.position = "absolute";
            } else {
                if (container.firstChild) {
                    container.insertBefore(c, container.firstChild);
                } else {
                    container[appendChild](c);
                }
            }
            plugins.call(res, res, R.fn);
            return res;
        };
        paperproto.clear = function () {
            this.canvas.innerHTML = E;
            this.span = doc.createElement("span");
            this.span.style.cssText = "position:absolute;left:-9999em;top:-9999em;padding:0;margin:0;line-height:1;display:inline;";
            this.canvas[appendChild](this.span);
            this.bottom = this.top = null;
        };
        paperproto.remove = function () {
            this.canvas.parentNode.removeChild(this.canvas);
            for (var i in this) {
                this[i] = removed(i);
            }
            return true;
        };
    }

    // rest
    // WebKit rendering bug workaround method
    var version = navigator.userAgent.match(/Version\/(.*?)\s/);
    if ((navigator.vendor == "Apple Computer, Inc.") && (version && version[1] < 4 || navigator.platform.slice(0, 2) == "iP")) {
        paperproto.safari = function () {
            var rect = this.rect(-99, -99, this.width + 99, this.height + 99).attr({stroke: "none"});
            win.setTimeout(function () {rect.remove();});
        };
    } else {
        paperproto.safari = function () {};
    }

    // Events
    var preventDefault = function () {
        this.returnValue = false;
    },
    preventTouch = function () {
        return this.originalEvent.preventDefault();
    },
    stopPropagation = function () {
        this.cancelBubble = true;
    },
    stopTouch = function () {
        return this.originalEvent.stopPropagation();
    },
    addEvent = (function () {
        if (doc.addEventListener) {
            return function (obj, type, fn, element) {
                var realName = supportsTouch && touchMap[type] ? touchMap[type] : type;
                var f = function (e) {
                    if (supportsTouch && touchMap[has](type)) {
                        for (var i = 0, ii = e.targetTouches && e.targetTouches.length; i < ii; i++) {
                            if (e.targetTouches[i].target == obj) {
                                var olde = e;
                                e = e.targetTouches[i];
                                e.originalEvent = olde;
                                e.preventDefault = preventTouch;
                                e.stopPropagation = stopTouch;
                                break;
                            }
                        }
                    }
                    return fn.call(element, e);
                };
                obj.addEventListener(realName, f, false);
                return function () {
                    obj.removeEventListener(realName, f, false);
                    return true;
                };
            };
        } else if (doc.attachEvent) {
            return function (obj, type, fn, element) {
                var f = function (e) {
                    e = e || win.event;
                    e.preventDefault = e.preventDefault || preventDefault;
                    e.stopPropagation = e.stopPropagation || stopPropagation;
                    return fn.call(element, e);
                };
                obj.attachEvent("on" + type, f);
                var detacher = function () {
                    obj.detachEvent("on" + type, f);
                    return true;
                };
                return detacher;
            };
        }
    })(),
    drag = [],
    dragMove = function (e) {
        var x = e.clientX,
            y = e.clientY,
            scrollY = doc.documentElement.scrollTop || doc.body.scrollTop,
            scrollX = doc.documentElement.scrollLeft || doc.body.scrollLeft,
            dragi,
            j = drag.length;
        while (j--) {
            dragi = drag[j];
            if (supportsTouch) {
                var i = e.touches.length,
                    touch;
                while (i--) {
                    touch = e.touches[i];
                    if (touch.identifier == dragi.el._drag.id) {
                        x = touch.clientX;
                        y = touch.clientY;
                        (e.originalEvent ? e.originalEvent : e).preventDefault();
                        break;
                    }
                }
            } else {
                e.preventDefault();
            }
            x += scrollX;
            y += scrollY;
            dragi.move && dragi.move.call(dragi.move_scope || dragi.el, x - dragi.el._drag.x, y - dragi.el._drag.y, x, y, e);
        }
    },
    dragUp = function (e) {
        R.unmousemove(dragMove).unmouseup(dragUp);
        var i = drag.length,
            dragi;
        while (i--) {
            dragi = drag[i];
            dragi.el._drag = {};
            dragi.end && dragi.end.call(dragi.end_scope || dragi.start_scope || dragi.move_scope || dragi.el, e);
        }
        drag = [];
    };
    for (var i = events[length]; i--;) {
        (function (eventName) {
            R[eventName] = Element[proto][eventName] = function (fn, scope) {
                if (R.is(fn, "function")) {
                    this.events = this.events || [];
                    this.events.push({name: eventName, f: fn, unbind: addEvent(this.shape || this.node || doc, eventName, fn, scope || this)});
                }
                return this;
            };
            R["un" + eventName] = Element[proto]["un" + eventName] = function (fn) {
                var events = this.events,
                    l = events[length];
                while (l--) if (events[l].name == eventName && events[l].f == fn) {
                    events[l].unbind();
                    events.splice(l, 1);
                    !events.length && delete this.events;
                    return this;
                }
                return this;
            };
        })(events[i]);
    }
    elproto.hover = function (f_in, f_out, scope_in, scope_out) {
        return this.mouseover(f_in, scope_in).mouseout(f_out, scope_out || scope_in);
    };
    elproto.unhover = function (f_in, f_out) {
        return this.unmouseover(f_in).unmouseout(f_out);
    };
    elproto.drag = function (onmove, onstart, onend, move_scope, start_scope, end_scope) {
        this._drag = {};
        this.mousedown(function (e) {
            (e.originalEvent || e).preventDefault();
            var scrollY = doc.documentElement.scrollTop || doc.body.scrollTop,
                scrollX = doc.documentElement.scrollLeft || doc.body.scrollLeft;
            this._drag.x = e.clientX + scrollX;
            this._drag.y = e.clientY + scrollY;
            this._drag.id = e.identifier;
            onstart && onstart.call(start_scope || move_scope || this, e.clientX + scrollX, e.clientY + scrollY, e);
            !drag.length && R.mousemove(dragMove).mouseup(dragUp);
            drag.push({el: this, move: onmove, end: onend, move_scope: move_scope, start_scope: start_scope, end_scope: end_scope});
        });
        return this;
    };
    elproto.undrag = function (onmove, onstart, onend) {
        var i = drag.length;
        while (i--) {
            drag[i].el == this && (drag[i].move == onmove && drag[i].end == onend) && drag.splice(i++, 1);
        }
        !drag.length && R.unmousemove(dragMove).unmouseup(dragUp);
    };
    paperproto.circle = function (x, y, r) {
        return theCircle(this, x || 0, y || 0, r || 0);
    };
    paperproto.rect = function (x, y, w, h, r) {
        return theRect(this, x || 0, y || 0, w || 0, h || 0, r || 0);
    };
    paperproto.ellipse = function (x, y, rx, ry) {
        return theEllipse(this, x || 0, y || 0, rx || 0, ry || 0);
    };
    paperproto.path = function (pathString) {
        pathString && !R.is(pathString, string) && !R.is(pathString[0], array) && (pathString += E);
        return thePath(R.format[apply](R, arguments), this);
    };
    paperproto.image = function (src, x, y, w, h) {
        return theImage(this, src || "about:blank", x || 0, y || 0, w || 0, h || 0);
    };
    paperproto.text = function (x, y, text) {
        return theText(this, x || 0, y || 0, Str(text));
    };
    paperproto.set = function (itemsArray) {
        arguments[length] > 1 && (itemsArray = Array[proto].splice.call(arguments, 0, arguments[length]));
        return new Set(itemsArray);
    };
    paperproto.setSize = setSize;
    paperproto.top = paperproto.bottom = null;
    paperproto.raphael = R;
    function x_y() {
        return this.x + S + this.y;
    }
    elproto.resetScale = function () {
        if (this.removed) {
            return this;
        }
        this._.sx = 1;
        this._.sy = 1;
        this.attrs.scale = "1 1";
    };
    elproto.scale = function (x, y, cx, cy) {
        if (this.removed) {
            return this;
        }
        if (x == null && y == null) {
            return {
                x: this._.sx,
                y: this._.sy,
                toString: x_y
            };
        }
        y = y || x;
        !+y && (y = x);
        var dx,
            dy,
            dcx,
            dcy,
            a = this.attrs;
        if (x != 0) {
            var bb = this.getBBox(),
                rcx = bb.x + bb.width / 2,
                rcy = bb.y + bb.height / 2,
                kx = abs(x / this._.sx),
                ky = abs(y / this._.sy);
            cx = (+cx || cx == 0) ? cx : rcx;
            cy = (+cy || cy == 0) ? cy : rcy;
            var posx = this._.sx > 0,
                posy = this._.sy > 0,
                dirx = ~~(x / abs(x)),
                diry = ~~(y / abs(y)),
                dkx = kx * dirx,
                dky = ky * diry,
                s = this.node.style,
                ncx = cx + abs(rcx - cx) * dkx * (rcx > cx == posx ? 1 : -1),
                ncy = cy + abs(rcy - cy) * dky * (rcy > cy == posy ? 1 : -1),
                fr = (x * dirx > y * diry ? ky : kx);
            switch (this.type) {
                case "rect":
                case "image":
                    var neww = a.width * kx,
                        newh = a.height * ky;
                    this.attr({
                        height: newh,
                        r: a.r * fr,
                        width: neww,
                        x: ncx - neww / 2,
                        y: ncy - newh / 2
                    });
                    break;
                case "circle":
                case "ellipse":
                    this.attr({
                        rx: a.rx * kx,
                        ry: a.ry * ky,
                        r: a.r * fr,
                        cx: ncx,
                        cy: ncy
                    });
                    break;
                case "text":
                    this.attr({
                        x: ncx,
                        y: ncy
                    });
                    break;
                case "path":
                    var path = pathToRelative(a.path),
                        skip = true,
                        fx = posx ? dkx : kx,
                        fy = posy ? dky : ky;
                    for (var i = 0, ii = path[length]; i < ii; i++) {
                        var p = path[i],
                            P0 = upperCase.call(p[0]);
                        if (P0 == "M" && skip) {
                            continue;
                        } else {
                            skip = false;
                        }
                        if (P0 == "A") {
                            p[path[i][length] - 2] *= fx;
                            p[path[i][length] - 1] *= fy;
                            p[1] *= kx;
                            p[2] *= ky;
                            p[5] = +(dirx + diry ? !!+p[5] : !+p[5]);
                        } else if (P0 == "H") {
                            for (var j = 1, jj = p[length]; j < jj; j++) {
                                p[j] *= fx;
                            }
                        } else if (P0 == "V") {
                            for (j = 1, jj = p[length]; j < jj; j++) {
                                p[j] *= fy;
                            }
                         } else {
                            for (j = 1, jj = p[length]; j < jj; j++) {
                                p[j] *= (j % 2) ? fx : fy;
                            }
                        }
                    }
                    var dim2 = pathDimensions(path);
                    dx = ncx - dim2.x - dim2.width / 2;
                    dy = ncy - dim2.y - dim2.height / 2;
                    path[0][1] += dx;
                    path[0][2] += dy;
                    this.attr({path: path});
                break;
            }
            if (this.type in {text: 1, image:1} && (dirx != 1 || diry != 1)) {
                if (this.transformations) {
                    this.transformations[2] = "scale("[concat](dirx, ",", diry, ")");
                    setAttr(this.node, "transform", this.transformations[join](S));
                    dx = (dirx == -1) ? -a.x - (neww || 0) : a.x;
                    dy = (diry == -1) ? -a.y - (newh || 0) : a.y;
                    this.attr({x: dx, y: dy});
                    a.fx = dirx - 1;
                    a.fy = diry - 1;
                } else {
                    this.node.filterMatrix = ms + ".Matrix(M11="[concat](dirx,
                        ", M12=0, M21=0, M22=", diry,
                        ", Dx=0, Dy=0, sizingmethod='auto expand', filtertype='bilinear')");
                    s.filter = (this.node.filterMatrix || E) + (this.node.filterOpacity || E);
                }
            } else {
                if (this.transformations) {
                    this.transformations[2] = E;
                    setAttr(this.node, "transform", this.transformations[join](S));
                    a.fx = 0;
                    a.fy = 0;
                } else {
                    this.node.filterMatrix = E;
                    s.filter = (this.node.filterMatrix || E) + (this.node.filterOpacity || E);
                }
            }
            a.scale = [x, y, cx, cy][join](S);
            this._.sx = x;
            this._.sy = y;
        }
        return this;
    };
    elproto.clone = function () {
        if (this.removed) {
            return null;
        }
        var attr = this.attr();
        delete attr.scale;
        delete attr.translation;
        return this.paper[this.type]().attr(attr);
    };
    var curveslengths = {},
    getPointAtSegmentLength = function (p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, length) {
        // Is this a straight line?
        // Added for huge speed improvements
        if ( p1x === c1x && p1y === c1y && c2x === p2x && c2y == p2y ) {
            var dx = p2x - p1x, dy = p2y - p1y;
            var totalLength = Math.sqrt( dx * dx + dy * dy );

            if ( length == null ) {
                return totalLength;
            } else {
                var fract = length / totalLength;
                return {
                    start: { x: p1x, y: p1y },
                    m: { x: p1x, y: p1y },
                    n: { x: p2x, y: p2y },
                    end: { x: p2x, y: p2y },
                    x: p1x + fract * dx,
                    y: p1y + fract * dy,
                    alpha: (90 - math.atan(dx / dy) * 180 / PI)
                };
            }
        }

        var len = 0,
            precision = 100,
            name = [p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y].join(),
            cache = curveslengths[name],
            old, dot;
        !cache && (curveslengths[name] = cache = {data: []});
        cache.timer && clearTimeout(cache.timer);
        cache.timer = setTimeout(function () {delete curveslengths[name];}, 2000);
        if (length != null) {
            var total = getPointAtSegmentLength(p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y);
            precision = ~~total * 10;
        }
        for (var i = 0; i < precision + 1; i++) {
            if (cache.data[length] > i) {
                dot = cache.data[i * precision];
            } else {
                dot = R.findDotsAtSegment(p1x, p1y, c1x, c1y, c2x, c2y, p2x, p2y, i / precision);
                cache.data[i] = dot;
            }
            i && (len += pow(pow(old.x - dot.x, 2) + pow(old.y - dot.y, 2), .5));
            if (length != null && len >= length) {
                return dot;
            }
            old = dot;
        }
        if (length == null) {
            return len;
        }
    },
    getLengthFactory = function (istotal, subpath) {
        return function (path, length, onlystart) {
            path = path2curve(path);
            var x, y, p, l, sp = "", subpaths = {}, point,
                len = 0;
            for (var i = 0, ii = path.length; i < ii; i++) {
                p = path[i];
                if (p[0] == "M") {
                    x = +p[1];
                    y = +p[2];
                } else {
                    l = getPointAtSegmentLength(x, y, p[1], p[2], p[3], p[4], p[5], p[6]);
                    if (len + l > length) {
                        if (subpath && !subpaths.start) {
                            point = getPointAtSegmentLength(x, y, p[1], p[2], p[3], p[4], p[5], p[6], length - len);
                            sp += ["C", point.start.x, point.start.y, point.m.x, point.m.y, point.x, point.y];
                            if (onlystart) {return sp;}
                            subpaths.start = sp;
                            sp = ["M", point.x, point.y + "C", point.n.x, point.n.y, point.end.x, point.end.y, p[5], p[6]][join]();
                            len += l;
                            x = +p[5];
                            y = +p[6];
                            continue;
                        }
                        if (!istotal && !subpath) {
                            point = getPointAtSegmentLength(x, y, p[1], p[2], p[3], p[4], p[5], p[6], length - len);
                            return {x: point.x, y: point.y, alpha: point.alpha};
                        }
                    }
                    len += l;
                    x = +p[5];
                    y = +p[6];
                }
                sp += p;
            }
            subpaths.end = sp;
            point = istotal ? len : subpath ? subpaths : R.findDotsAtSegment(x, y, p[1], p[2], p[3], p[4], p[5], p[6], 1);
            point.alpha && (point = {x: point.x, y: point.y, alpha: point.alpha});
            return point;
        };
    };
    var getTotalLength = getLengthFactory(1),
        getPointAtLength = getLengthFactory(),
        getSubpathsAtLength = getLengthFactory(0, 1);
    elproto.getTotalLength = function () {
        if (this.type != "path") {return;}
        if (this.node.getTotalLength) {
            return this.node.getTotalLength();
        }
        return getTotalLength(this.attrs.path);
    };
    elproto.getPointAtLength = function (length) {
        if (this.type != "path") {return;}
        return getPointAtLength(this.attrs.path, length);
    };
    elproto.getSubpath = function (from, to) {
        if (this.type != "path") {return;}
        if (abs(this.getTotalLength() - to) < "1e-6") {
            return getSubpathsAtLength(this.attrs.path, from).end;
        }
        var a = getSubpathsAtLength(this.attrs.path, to, 1);
        return from ? getSubpathsAtLength(a, from).end : a;
    };

    // animation easing formulas
    R.easing_formulas = {
        linear: function (n) {
            return n;
        },
        "<": function (n) {
            return pow(n, 3);
        },
        ">": function (n) {
            return pow(n - 1, 3) + 1;
        },
        "<>": function (n) {
            n = n * 2;
            if (n < 1) {
                return pow(n, 3) / 2;
            }
            n -= 2;
            return (pow(n, 3) + 2) / 2;
        },
        backIn: function (n) {
            var s = 1.70158;
            return n * n * ((s + 1) * n - s);
        },
        backOut: function (n) {
            n = n - 1;
            var s = 1.70158;
            return n * n * ((s + 1) * n + s) + 1;
        },
        elastic: function (n) {
            if (n == 0 || n == 1) {
                return n;
            }
            var p = .3,
                s = p / 4;
            return pow(2, -10 * n) * math.sin((n - s) * (2 * PI) / p) + 1;
        },
        bounce: function (n) {
            var s = 7.5625,
                p = 2.75,
                l;
            if (n < (1 / p)) {
                l = s * n * n;
            } else {
                if (n < (2 / p)) {
                    n -= (1.5 / p);
                    l = s * n * n + .75;
                } else {
                    if (n < (2.5 / p)) {
                        n -= (2.25 / p);
                        l = s * n * n + .9375;
                    } else {
                        n -= (2.625 / p);
                        l = s * n * n + .984375;
                    }
                }
            }
            return l;
        }
    };

    var animationElements = [],
        animation = function () {
            var Now = +new Date;
            for (var l = 0; l < animationElements[length]; l++) {
                var e = animationElements[l];
                if (e.stop || e.el.removed) {
                    continue;
                }
                var time = Now - e.start,
                    ms = e.ms,
                    easing = e.easing,
                    from = e.from,
                    diff = e.diff,
                    to = e.to,
                    t = e.t,
                    that = e.el,
                    set = {},
                    now;
                if (time < ms) {
                    var pos = easing(time / ms);
                    for (var attr in from) if (from[has](attr)) {
                        switch (availableAnimAttrs[attr]) {
                            case "along":
                                now = pos * ms * diff[attr];
                                to.back && (now = to.len - now);
                                var point = getPointAtLength(to[attr], now);
                                that.translate(diff.sx - diff.x || 0, diff.sy - diff.y || 0);
                                diff.x = point.x;
                                diff.y = point.y;
                                that.translate(point.x - diff.sx, point.y - diff.sy);
                                to.rot && that.rotate(diff.r + point.alpha, point.x, point.y);
                                break;
                            case nu:
                                now = +from[attr] + pos * ms * diff[attr];
                                break;
                            case "colour":
                                now = "rgb(" + [
                                    upto255(round(from[attr].r + pos * ms * diff[attr].r)),
                                    upto255(round(from[attr].g + pos * ms * diff[attr].g)),
                                    upto255(round(from[attr].b + pos * ms * diff[attr].b))
                                ][join](",") + ")";
                                break;
                            case "path":
                                now = [];
                                for (var i = 0, ii = from[attr][length]; i < ii; i++) {
                                    now[i] = [from[attr][i][0]];
                                    for (var j = 1, jj = from[attr][i][length]; j < jj; j++) {
                                        now[i][j] = +from[attr][i][j] + pos * ms * diff[attr][i][j];
                                    }
                                    now[i] = now[i][join](S);
                                }
                                now = now[join](S);
                                break;
                            case "csv":
                                switch (attr) {
                                    case "translation":
                                        var x = pos * ms * diff[attr][0] - t.x,
                                            y = pos * ms * diff[attr][1] - t.y;
                                        t.x += x;
                                        t.y += y;
                                        now = x + S + y;
                                    break;
                                    case "rotation":
                                        now = +from[attr][0] + pos * ms * diff[attr][0];
                                        from[attr][1] && (now += "," + from[attr][1] + "," + from[attr][2]);
                                    break;
                                    case "scale":
                                        now = [+from[attr][0] + pos * ms * diff[attr][0], +from[attr][1] + pos * ms * diff[attr][1], (2 in to[attr] ? to[attr][2] : E), (3 in to[attr] ? to[attr][3] : E)][join](S);
                                    break;
                                    case "clip-rect":
                                        now = [];
                                        i = 4;
                                        while (i--) {
                                            now[i] = +from[attr][i] + pos * ms * diff[attr][i];
                                        }
                                    break;
                                }
                                break;
                            default:
                              var from2 = [].concat(from[attr]);
                                now = [];
                                i = that.paper.customAttributes[attr].length;
                                while (i--) {
                                    now[i] = +from2[i] + pos * ms * diff[attr][i];
                                }
                                break;
                        }
                        set[attr] = now;
                    }
                    that.attr(set);
                    that._run && that._run.call(that);
                } else {
                    if (to.along) {
                        point = getPointAtLength(to.along, to.len * !to.back);
                        that.translate(diff.sx - (diff.x || 0) + point.x - diff.sx, diff.sy - (diff.y || 0) + point.y - diff.sy);
                        to.rot && that.rotate(diff.r + point.alpha, point.x, point.y);
                    }
                    (t.x || t.y) && that.translate(-t.x, -t.y);
                    to.scale && (to.scale += E);
                    that.attr(to);
                    animationElements.splice(l--, 1);
                }
            }
            R.svg && that && that.paper && that.paper.safari();
            animationElements[length] && setTimeout(animation);
        },
        keyframesRun = function (attr, element, time, prev, prevcallback) {
            var dif = time - prev;
            element.timeouts.push(setTimeout(function () {
                R.is(prevcallback, "function") && prevcallback.call(element);
                element.animate(attr, dif, attr.easing);
            }, prev));
        },
        upto255 = function (color) {
            return mmax(mmin(color, 255), 0);
        },
        translate = function (x, y) {
            if (x == null) {
                return {x: this._.tx, y: this._.ty, toString: x_y};
            }
            this._.tx += +x;
            this._.ty += +y;
            switch (this.type) {
                case "circle":
                case "ellipse":
                    this.attr({cx: +x + this.attrs.cx, cy: +y + this.attrs.cy});
                    break;
                case "rect":
                case "image":
                case "text":
                    this.attr({x: +x + this.attrs.x, y: +y + this.attrs.y});
                    break;
                case "path":
                    var path = pathToRelative(this.attrs.path);
                    path[0][1] += +x;
                    path[0][2] += +y;
                    this.attr({path: path});
                break;
            }
            return this;
        };
    elproto.animateWith = function (element, params, ms, easing, callback) {
        for (var i = 0, ii = animationElements.length; i < ii; i++) {
            if (animationElements[i].el.id == element.id) {
                params.start = animationElements[i].start;
            }
        }
        return this.animate(params, ms, easing, callback);
    };
    elproto.animateAlong = along();
    elproto.animateAlongBack = along(1);
    function along(isBack) {
        return function (path, ms, rotate, callback) {
            var params = {back: isBack};
            R.is(rotate, "function") ? (callback = rotate) : (params.rot = rotate);
            path && path.constructor == Element && (path = path.attrs.path);
            path && (params.along = path);
            return this.animate(params, ms, callback);
        };
    }
    function CubicBezierAtTime(t, p1x, p1y, p2x, p2y, duration) {
        var cx = 3 * p1x,
            bx = 3 * (p2x - p1x) - cx,
            ax = 1 - cx - bx,
            cy = 3 * p1y,
            by = 3 * (p2y - p1y) - cy,
            ay = 1 - cy - by;
        function sampleCurveX(t) {
            return ((ax * t + bx) * t + cx) * t;
        }
        function solve(x, epsilon) {
            var t = solveCurveX(x, epsilon);
            return ((ay * t + by) * t + cy) * t;
        }
        function solveCurveX(x, epsilon) {
            var t0, t1, t2, x2, d2, i;
            for(t2 = x, i = 0; i < 8; i++) {
                x2 = sampleCurveX(t2) - x;
                if (abs(x2) < epsilon) {
                    return t2;
                }
                d2 = (3 * ax * t2 + 2 * bx) * t2 + cx;
                if (abs(d2) < 1e-6) {
                    break;
                }
                t2 = t2 - x2 / d2;
            }
            t0 = 0;
            t1 = 1;
            t2 = x;
            if (t2 < t0) {
                return t0;
            }
            if (t2 > t1) {
                return t1;
            }
            while (t0 < t1) {
                x2 = sampleCurveX(t2);
                if (abs(x2 - x) < epsilon) {
                    return t2;
                }
                if (x > x2) {
                    t0 = t2;
                } else {
                    t1 = t2;
                }
                t2 = (t1 - t0) / 2 + t0;
            }
            return t2;
        }
        return solve(t, 1 / (200 * duration));
    }
    elproto.onAnimation = function (f) {
        this._run = f || 0;
        return this;
    };
    elproto.animate = function (params, ms, easing, callback) {
        var element = this;
        element.timeouts = element.timeouts || [];
        if (R.is(easing, "function") || !easing) {
            callback = easing || null;
        }
        if (element.removed) {
            callback && callback.call(element);
            return element;
        }
        var from = {},
            to = {},
            animateable = false,
            diff = {};
        for (var attr in params) if (params[has](attr)) {
            if (availableAnimAttrs[has](attr) || element.paper.customAttributes[has](attr)) {
                animateable = true;
                from[attr] = element.attr(attr);
                (from[attr] == null) && (from[attr] = availableAttrs[attr]);
                to[attr] = params[attr];
                switch (availableAnimAttrs[attr]) {
                    case "along":
                        var len = getTotalLength(params[attr]);
                        var point = getPointAtLength(params[attr], len * !!params.back);
                        var bb = element.getBBox();
                        diff[attr] = len / ms;
                        diff.tx = bb.x;
                        diff.ty = bb.y;
                        diff.sx = point.x;
                        diff.sy = point.y;
                        to.rot = params.rot;
                        to.back = params.back;
                        to.len = len;
                        params.rot && (diff.r = toFloat(element.rotate()) || 0);
                        break;
                    case nu:
                        diff[attr] = (to[attr] - from[attr]) / ms;
                        break;
                    case "colour":
                        from[attr] = R.getRGB(from[attr]);
                        var toColour = R.getRGB(to[attr]);
                        diff[attr] = {
                            r: (toColour.r - from[attr].r) / ms,
                            g: (toColour.g - from[attr].g) / ms,
                            b: (toColour.b - from[attr].b) / ms
                        };
                        break;
                    case "path":
                        var pathes = path2curve(from[attr], to[attr]);
                        from[attr] = pathes[0];
                        var toPath = pathes[1];
                        diff[attr] = [];
                        for (var i = 0, ii = from[attr][length]; i < ii; i++) {
                            diff[attr][i] = [0];
                            for (var j = 1, jj = from[attr][i][length]; j < jj; j++) {
                                diff[attr][i][j] = (toPath[i][j] - from[attr][i][j]) / ms;
                            }
                        }
                        break;
                    case "csv":
                        var values = Str(params[attr])[split](separator),
                            from2 = Str(from[attr])[split](separator);
                        switch (attr) {
                            case "translation":
                                from[attr] = [0, 0];
                                diff[attr] = [values[0] / ms, values[1] / ms];
                            break;
                            case "rotation":
                                from[attr] = (from2[1] == values[1] && from2[2] == values[2]) ? from2 : [0, values[1], values[2]];
                                diff[attr] = [(values[0] - from[attr][0]) / ms, 0, 0];
                            break;
                            case "scale":
                                params[attr] = values;
                                from[attr] = Str(from[attr])[split](separator);
                                diff[attr] = [(values[0] - from[attr][0]) / ms, (values[1] - from[attr][1]) / ms, 0, 0];
                            break;
                            case "clip-rect":
                                from[attr] = Str(from[attr])[split](separator);
                                diff[attr] = [];
                                i = 4;
                                while (i--) {
                                    diff[attr][i] = (values[i] - from[attr][i]) / ms;
                                }
                            break;
                        }
                        to[attr] = values;
                        break;
                    default:
                        values = [].concat(params[attr]);
                        from2 = [].concat(from[attr]);
                        diff[attr] = [];
                        i = element.paper.customAttributes[attr][length];
                        while (i--) {
                            diff[attr][i] = ((values[i] || 0) - (from2[i] || 0)) / ms;
                        }
                        break;
                }
            }
        }
        if (!animateable) {
            var attrs = [],
                lastcall;
            for (var key in params) if (params[has](key) && animKeyFrames.test(key)) {
                attr = {value: params[key]};
                key == "from" && (key = 0);
                key == "to" && (key = 100);
                attr.key = toInt(key, 10);
                attrs.push(attr);
            }
            attrs.sort(sortByKey);
            if (attrs[0].key) {
                attrs.unshift({key: 0, value: element.attrs});
            }
            for (i = 0, ii = attrs[length]; i < ii; i++) {
                keyframesRun(attrs[i].value, element, ms / 100 * attrs[i].key, ms / 100 * (attrs[i - 1] && attrs[i - 1].key || 0), attrs[i - 1] && attrs[i - 1].value.callback);
            }
            lastcall = attrs[attrs[length] - 1].value.callback;
            if (lastcall) {
                element.timeouts.push(setTimeout(function () {lastcall.call(element);}, ms));
            }
        } else {
            var easyeasy = R.easing_formulas[easing];
            if (!easyeasy) {
                easyeasy = Str(easing).match(bezierrg);
                if (easyeasy && easyeasy[length] == 5) {
                    var curve = easyeasy;
                    easyeasy = function (t) {
                        return CubicBezierAtTime(t, +curve[1], +curve[2], +curve[3], +curve[4], ms);
                    };
                } else {
                    easyeasy = function (t) {
                        return t;
                    };
                }
            }
            animationElements.push({
                start: params.start || +new Date,
                ms: ms,
                easing: easyeasy,
                from: from,
                diff: diff,
                to: to,
                el: element,
                t: {x: 0, y: 0}
            });
            R.is(callback, "function") && (element._ac = setTimeout(function () {
                callback.call(element);
            }, ms));
            animationElements[length] == 1 && setTimeout(animation);
        }
        return this;
    };
    elproto.stop = function () {
        for (var i = 0; i < animationElements.length; i++) {
            animationElements[i].el.id == this.id && animationElements.splice(i--, 1);
        }
        for (i = 0, ii = this.timeouts && this.timeouts.length; i < ii; i++) {
            clearTimeout(this.timeouts[i]);
        }
        this.timeouts = [];
        clearTimeout(this._ac);
        delete this._ac;
        return this;
    };
    elproto.translate = function (x, y) {
        return this.attr({translation: x + " " + y});
    };
    elproto[toString] = function () {
        return "Rapha\xebl\u2019s object";
    };
    R.ae = animationElements;

    // Set
    var Set = function (items) {
        this.items = [];
        this[length] = 0;
        this.type = "set";
        if (items) {
            for (var i = 0, ii = items[length]; i < ii; i++) {
                if (items[i] && (items[i].constructor == Element || items[i].constructor == Set)) {
                    this[this.items[length]] = this.items[this.items[length]] = items[i];
                    this[length]++;
                }
            }
        }
    };
    Set[proto][push] = function () {
        var item,
            len;
        for (var i = 0, ii = arguments[length]; i < ii; i++) {
            item = arguments[i];
            if (item && (item.constructor == Element || item.constructor == Set)) {
                len = this.items[length];
                this[len] = this.items[len] = item;
                this[length]++;
            }
        }
        return this;
    };
    Set[proto].pop = function () {
        delete this[this[length]--];
        return this.items.pop();
    };
    for (var method in elproto) if (elproto[has](method)) {
        Set[proto][method] = (function (methodname) {
            return function () {
                for (var i = 0, ii = this.items[length]; i < ii; i++) {
                    this.items[i][methodname][apply](this.items[i], arguments);
                }
                return this;
            };
        })(method);
    }
    Set[proto].attr = function (name, value) {
        if (name && R.is(name, array) && R.is(name[0], "object")) {
            for (var j = 0, jj = name[length]; j < jj; j++) {
                this.items[j].attr(name[j]);
            }
        } else {
            for (var i = 0, ii = this.items[length]; i < ii; i++) {
                this.items[i].attr(name, value);
            }
        }
        return this;
    };
    Set[proto].animate = function (params, ms, easing, callback) {
        (R.is(easing, "function") || !easing) && (callback = easing || null);
        var len = this.items[length],
            i = len,
            item,
            set = this,
            collector;
        callback && (collector = function () {
            !--len && callback.call(set);
        });
        easing = R.is(easing, string) ? easing : collector;
        item = this.items[--i].animate(params, ms, easing, collector);
        while (i--) {
            this.items[i] && !this.items[i].removed && this.items[i].animateWith(item, params, ms, easing, collector);
        }
        return this;
    };
    Set[proto].insertAfter = function (el) {
        var i = this.items[length];
        while (i--) {
            this.items[i].insertAfter(el);
        }
        return this;
    };
    Set[proto].getBBox = function () {
        var x = [],
            y = [],
            w = [],
            h = [];
        for (var i = this.items[length]; i--;) {
            var box = this.items[i].getBBox();
            x[push](box.x);
            y[push](box.y);
            w[push](box.x + box.width);
            h[push](box.y + box.height);
        }
        x = mmin[apply](0, x);
        y = mmin[apply](0, y);
        return {
            x: x,
            y: y,
            width: mmax[apply](0, w) - x,
            height: mmax[apply](0, h) - y
        };
    };
    Set[proto].clone = function (s) {
        s = new Set;
        for (var i = 0, ii = this.items[length]; i < ii; i++) {
            s[push](this.items[i].clone());
        }
        return s;
    };

    R.registerFont = function (font) {
        if (!font.face) {
            return font;
        }
        this.fonts = this.fonts || {};
        var fontcopy = {
                w: font.w,
                face: {},
                glyphs: {}
            },
            family = font.face["font-family"];
        for (var prop in font.face) if (font.face[has](prop)) {
            fontcopy.face[prop] = font.face[prop];
        }
        if (this.fonts[family]) {
            this.fonts[family][push](fontcopy);
        } else {
            this.fonts[family] = [fontcopy];
        }
        if (!font.svg) {
            fontcopy.face["units-per-em"] = toInt(font.face["units-per-em"], 10);
            for (var glyph in font.glyphs) if (font.glyphs[has](glyph)) {
                var path = font.glyphs[glyph];
                fontcopy.glyphs[glyph] = {
                    w: path.w,
                    k: {},
                    d: path.d && "M" + path.d[rp](/[mlcxtrv]/g, function (command) {
                            return {l: "L", c: "C", x: "z", t: "m", r: "l", v: "c"}[command] || "M";
                        }) + "z"
                };
                if (path.k) {
                    for (var k in path.k) if (path[has](k)) {
                        fontcopy.glyphs[glyph].k[k] = path.k[k];
                    }
                }
            }
        }
        return font;
    };
    paperproto.getFont = function (family, weight, style, stretch) {
        stretch = stretch || "normal";
        style = style || "normal";
        weight = +weight || {normal: 400, bold: 700, lighter: 300, bolder: 800}[weight] || 400;
        if (!R.fonts) {
            return;
        }
        var font = R.fonts[family];
        if (!font) {
            var name = new RegExp("(^|\\s)" + family[rp](/[^\w\d\s+!~.:_-]/g, E) + "(\\s|$)", "i");
            for (var fontName in R.fonts) if (R.fonts[has](fontName)) {
                if (name.test(fontName)) {
                    font = R.fonts[fontName];
                    break;
                }
            }
        }
        var thefont;
        if (font) {
            for (var i = 0, ii = font[length]; i < ii; i++) {
                thefont = font[i];
                if (thefont.face["font-weight"] == weight && (thefont.face["font-style"] == style || !thefont.face["font-style"]) && thefont.face["font-stretch"] == stretch) {
                    break;
                }
            }
        }
        return thefont;
    };
    paperproto.print = function (x, y, string, font, size, origin, letter_spacing) {
        origin = origin || "middle"; // baseline|middle
        letter_spacing = mmax(mmin(letter_spacing || 0, 1), -1);
        var out = this.set(),
            letters = Str(string)[split](E),
            shift = 0,
            path = E,
            scale;
        R.is(font, string) && (font = this.getFont(font));
        if (font) {
            scale = (size || 16) / font.face["units-per-em"];
            var bb = font.face.bbox.split(separator),
                top = +bb[0],
                height = +bb[1] + (origin == "baseline" ? bb[3] - bb[1] + (+font.face.descent) : (bb[3] - bb[1]) / 2);
            for (var i = 0, ii = letters[length]; i < ii; i++) {
                var prev = i && font.glyphs[letters[i - 1]] || {},
                    curr = font.glyphs[letters[i]];
                shift += i ? (prev.w || font.w) + (prev.k && prev.k[letters[i]] || 0) + (font.w * letter_spacing) : 0;
                curr && curr.d && out[push](this.path(curr.d).attr({fill: "#000", stroke: "none", translation: [shift, 0]}));
            }
            out.scale(scale, scale, top, height).translate(x - top, y - height);
        }
        return out;
    };

    R.format = function (token, params) {
        var args = R.is(params, array) ? [0][concat](params) : arguments;
        token && R.is(token, string) && args[length] - 1 && (token = token[rp](formatrg, function (str, i) {
            return args[++i] == null ? E : args[i];
        }));
        return token || E;
    };
    R.ninja = function () {
        oldRaphael.was ? (win.Raphael = oldRaphael.is) : delete Raphael;
        return R;
    };
    R.el = elproto;
    R.st = Set[proto];

    oldRaphael.was ? (win.Raphael = R) : (Raphael = R);
})();

},{}]},{},[2]);
