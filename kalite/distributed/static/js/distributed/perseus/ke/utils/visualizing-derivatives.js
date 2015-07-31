(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    PiecewiseFunction: function (options) {
        options = $.extend(true, {
            INTERVAL_WIDTH: 2,
            fnArray: [],
            rangeArray: [],
            _paths: {}
        }, options);
        $.extend(this, options);
        _.bindAll(this);
        this.length = function () {
            return this.fnArray.length;
        };
        this.width = function () {
            var n = this.length();
            return this.rangeArray[n - 1][1] - this.rangeArray[0][0];
        };
        this.toTextArray = function (fnArray) {
            if (!fnArray) {
                fnArray = this.fnArray;
            }
            return _.map(fnArray, function (fn) {
                return fn.text();
            });
        };
        this._shiftArray = function () {
            var w = this.INTERVAL_WIDTH;
            return _.map(this.rangeArray, function (range, i) {
                return Math.floor(range[0] / w) * w;
            });
        };
        this._shiftFnArray = function () {
            var shiftArray = this._shiftArray();
            return _.map(this.fnArray, function (fn, i) {
                return fn.scale(1, -shiftArray[i]);
            });
        };
        this.derivative = function (fnArray) {
            if (!fnArray) {
                fnArray = this.fnArray;
            }
            return _.map(fnArray, function (fn, i) {
                return fn.derivative();
            });
        };
        this.translate = function (dx, dy) {
            if (dx) {
                this.rangeArray = _.map(this.rangeArray, function (range) {
                    return _.map(range, function (x) {
                        return x + dx;
                    });
                });
            }
            if (dy) {
                this.fnArray = _.map(this.fnArray, function (fn) {
                    var result = fn.add(dy);
                    return result;
                });
            }
        };
        this.calibrate = function () {
            var dx = this.rangeArray[0][0];
            var w = this.INTERVAL_WIDTH;
            var dy = this.fnArray[0].evalOf(0);
            _.each(this.fnArray, function (fn) {
                var start = fn.evalOf(0);
                var end = fn.evalOf(w);
                dy = Math.min(dy, start, end);
            });
            this.translate(-dx + 2, -dy);
        };
        this.slice = function (startIndex, endIndex) {
            if (startIndex >= endIndex) {
                return null;
            }
            var crop = function (array) {
                return array.slice(startIndex, endIndex);
            };
            return new KhanUtil.PiecewiseFunction({
                fnArray: crop(this.fnArray),
                rangeArray: crop(this.rangeArray)
            });
        };
        this.concat = function (piecewiseFn) {
            var fnArray = this.fnArray.concat(piecewiseFn.fnArray);
            var offset = piecewiseFn.rangeArray[0][0];
            var start = this.rangeArray[this.rangeArray.length - 1][1];
            var shiftedRangeArray = _.map(piecewiseFn.rangeArray, function (range) {
                return _.map(range, function (x) {
                    return x - offset + start;
                });
            });
            var rangeArray = this.rangeArray.concat(shiftedRangeArray);
            return new KhanUtil.PiecewiseFunction({
                fnArray: fnArray,
                rangeArray: rangeArray
            });
        };
        this.matches = function (piecewiseFunction, useDerivative) {
            var original = this.fnArray;
            var other = piecewiseFunction.fnArray;
            if (useDerivative) {
                original = this.derivative();
                other = piecewiseFunction.derivative();
            }
            original = this.toTextArray(original);
            other = this.toTextArray(other);
            var n = other.length;
            var diff = original.length - n;
            if (diff < 0) {
                return null;
            }
            var matches = [];
            _.times(diff + 1, function (i) {
                if (_.isEqual(original.slice(i, i + n), other)) {
                    matches.push(i);
                }
            });
            return matches;
        };
        this.trimRangeArrayEnds = function (offset) {
            if (offset === 0) {
                return;
            }
            var n = this.length();
            var offsetAmt = this.INTERVAL_WIDTH * offset;
            this.rangeArray[0][0] += offsetAmt;
            this.rangeArray[n - 1][1] += offsetAmt - this.INTERVAL_WIDTH;
        };
        this._makePlotArray = function (fnArray) {
            if (!fnArray) {
                fnArray = this.fnArray;
            }
            return _.map(fnArray, function (fn, i) {
                return function (x) {
                    return fn.evalOf(x);
                };
            });
        };
        this._plotEndpoints = function (color, plotDerivative, omitEnds) {
            var shiftedFnArray = this._shiftFnArray();
            var antiderivFnArray;
            if (plotDerivative) {
                antiderivFnArray = shiftedFnArray;
                shiftedFnArray = this.derivative(shiftedFnArray);
            }
            var emptyEndpoints = [];
            var filledEndpoints = [];
            var derivEndpoints = [];
            var prevX = null;
            var prevY = null;
            var prevOrigY = null;
            var n = this.rangeArray.length;
            _.each(this.rangeArray, function (range, i) {
                var fn = shiftedFnArray[i], origFn;
                if (plotDerivative) {
                    origFn = antiderivFnArray[i];
                }
                _.each(range, function (x, j) {
                    var y = fn.evalOf(x);
                    var origY = plotDerivative ? origFn.evalOf(x) : null;
                    if (i > 0 && j === 0) {
                        if (y !== prevY || x !== prevX) {
                            filledEndpoints.push([
                                prevX,
                                prevY
                            ]);
                            emptyEndpoints.push([
                                x,
                                y
                            ]);
                        } else {
                            if (origY !== prevOrigY || x !== prevX) {
                                derivEndpoints.push([
                                    x,
                                    y
                                ]);
                            }
                        }
                    }
                    if (i === 0 && j === 0 && !omitEnds) {
                        emptyEndpoints.push([
                            x,
                            y
                        ]);
                    }
                    if (i === n - 1 && j === 1 && !omitEnds) {
                        filledEndpoints.push([
                            x,
                            y
                        ]);
                    }
                    prevX = x;
                    prevY = y;
                    prevOrigY = origY;
                });
            });
            if (plotDerivative) {
                emptyEndpoints = derivEndpoints.concat(emptyEndpoints).concat(filledEndpoints);
                filledEndpoints = [];
            }
            var self = this;
            this._paths['emptyEndpoints'] = this.graphie.style({
                stroke: color,
                strokeWidth: 3,
                fill: '#FFFFFF'
            }, function () {
                return self.graphie.plotEndpointCircles(emptyEndpoints);
            });
            this._paths['filledEndpoints'] = this.graphie.style({
                stroke: color,
                strokeWidth: 3,
                fill: color
            }, function () {
                return self.graphie.plotEndpointCircles(filledEndpoints);
            });
        };
        this._plotSegments = function (color, plotDerivative) {
            var shiftedFnArray = this._shiftFnArray();
            if (plotDerivative) {
                shiftedFnArray = this.derivative(shiftedFnArray);
            }
            var plotArray = this._makePlotArray(shiftedFnArray);
            var self = this;
            this._paths['segments'] = this.graphie.style({
                stroke: color,
                strokeWidth: 3
            }, function () {
                return self.graphie.plotPiecewise(plotArray, self.rangeArray);
            });
        };
        this.plot = function (options) {
            options = $.extend(true, {
                color: KhanUtil.GREEN,
                plotDerivative: false,
                omitEnds: false
            }, options);
            this.graphie = options.graphie || KhanUtil.currentGraph;
            this._plotSegments(options.color, options.plotDerivative);
            this._plotEndpoints(options.color, options.plotDerivative, options.omitEnds);
        };
        this.translatePlot = function (dx, dy) {
            var scaled = this.graphie.scaleVector([
                dx,
                dy
            ]);
            _.each(this._paths, function (pathSet) {
                pathSet.translate(scaled[0], scaled[1]);
            });
        };
        this.hide = function (speed) {
            if (this.hidden) {
                return;
            }
            speed = speed || 100;
            _.each(this._paths, function (pathSet) {
                if (pathSet.length === 0) {
                    return;
                }
                pathSet.animate({
                    'fill-opacity': 0,
                    'opacity': 0
                }, speed);
            });
            this.hidden = true;
        };
        this.show = function (speed) {
            if (!this.hidden) {
                return;
            }
            speed = speed || 100;
            _.each(this._paths, function (pathSet) {
                if (pathSet.length === 0) {
                    return;
                }
                pathSet.animate({
                    'fill-opacity': 1,
                    'opacity': 1
                }, speed);
            });
            this.hidden = false;
        };
        this.toFront = function () {
            _.each(this._paths, function (pathSet) {
                pathSet.toFront();
            });
        };
        this.cleanup = function () {
            _.each(this._paths, function (pathSet) {
                pathSet.remove();
            });
            this._paths = {};
        };
    },
    PiecewiseFunctionGenerator: {
        _init: function () {
            _.bindAll(KhanUtil.PiecewiseFunctionGenerator);
        }(),
        _isInRange: function (ylims, val) {
            return !(val <= ylims[0] || val >= ylims[1]);
        },
        _scramble: function (n) {
            var newIndices = [];
            _.times(n, function (i) {
                var newIndex = KhanUtil.randRangeExclude(0, n - 1, newIndices);
                newIndices.push(newIndex);
            });
            return newIndices;
        },
        curveTypes: {
            'line': {
                params: {
                    m: [
                        -1,
                        -0.5,
                        0,
                        0.5,
                        1
                    ]
                },
                generate: function (m, b) {
                    var coefs = [
                        b,
                        m
                    ];
                    return new KhanUtil.Polynomial(0, 1, coefs);
                }
            },
            'curve': {
                params: {
                    isLeftCurve: [
                        true,
                        false
                    ],
                    m: [
                        -1,
                        1
                    ]
                },
                generate: function (isLeftCurve, m, b, intervalWidth) {
                    b = isLeftCurve ? b - m * intervalWidth : b;
                    var a = isLeftCurve ? intervalWidth : 0;
                    m = m / intervalWidth;
                    var coefs = [
                        Math.pow(a, 2) * m + b,
                        -2 * a * m,
                        m
                    ];
                    return new KhanUtil.Polynomial(0, 2, coefs);
                }
            }
        },
        makeCombinations: function () {
            var makeParamSets = function (curveTypes) {
                var paramSets = [];
                _.each(curveTypes, function (curveType, key) {
                    var paramSet = [[key]];
                    _.each(curveType.params, function (val) {
                        paramSet.push(val);
                    });
                    paramSets.push(paramSet);
                });
                return paramSets;
            };
            var addParam = function (currList, paramSet, paramIndex) {
                if (paramIndex === paramSet.length) {
                    combinations.push(currList);
                    return;
                }
                var params = paramSet[paramIndex];
                for (var i = 0; i < params.length; i++) {
                    currList.push(params[i]);
                    addParam(currList.slice(), paramSet, paramIndex + 1);
                    currList.pop();
                }
            };
            var makeCombinations = function () {
                var paramSets = makeParamSets(self.curveTypes);
                _.each(paramSets, function (paramSet) {
                    addParam([], paramSet, 0);
                });
            };
            var self = this;
            var combinations = [];
            makeCombinations();
            return combinations;
        },
        _randomY: function (ylims, excludes) {
            return KhanUtil.randRangeExclude(ylims[0], ylims[1], ylims.concat(excludes));
        },
        generate: function (options) {
            options = $.extend(true, {
                INTERVAL_WIDTH: 2,
                YLIMS: [],
                numSegments: 1,
                startVal: null,
                prevSegment: null,
                breakIndex: null
            }, options);
            if (!this.combinations) {
                this.combinations = this.makeCombinations();
            }
            var self = this;
            var YLIMS = options.YLIMS;
            var INTERVAL_WIDTH = options.INTERVAL_WIDTH;
            var endVal = function (segment) {
                return segment.evalOf(options.INTERVAL_WIDTH);
            };
            var createSegment = function (startVal, prevSegment) {
                if (startVal == null) {
                    if (prevSegment == null) {
                        startVal = self._randomY(YLIMS);
                    } else {
                        startVal = endVal(prevSegment);
                    }
                }
                var indices = self._scramble(self.combinations.length);
                for (var j = 0; j < indices.length; j++) {
                    var params = self.combinations[indices[j]].slice();
                    var curveType = self.curveTypes[params[0]];
                    params.push(startVal);
                    params.push(INTERVAL_WIDTH);
                    var segment = curveType['generate'].apply(null, params.slice(1));
                    var y = endVal(segment);
                    if (!self._isInRange(YLIMS, y)) {
                        continue;
                    }
                    if (prevSegment) {
                        var y0 = prevSegment.evalOf(0);
                        var s0 = prevSegment.subtract(y0).text();
                        var s1 = segment.subtract(startVal).text();
                        if (s0 === s1) {
                            continue;
                        }
                    }
                    return segment;
                }
                return null;
            };
            var makePiecewiseGraph = function () {
                var segments = [];
                var start = options.startVal;
                var prev = options.prevSegment;
                while (segments.length < options.numSegments) {
                    var len = segments.length;
                    if (options.breakIndex && len === options.breakIndex) {
                        start = self._randomY(YLIMS, [start]);
                    }
                    var segment = createSegment(start, prev);
                    if (!segment) {
                        segments = [];
                        prev = options.prevSegment;
                        start = options.startVal;
                    }
                    segments.push(segment);
                    prev = segment;
                    start = null;
                }
                return segments;
            };
            var fnArray = makePiecewiseGraph();
            var rangeArray = [];
            _.each(fnArray, function (fn, i) {
                var x = i * options.INTERVAL_WIDTH;
                rangeArray.push([
                    x,
                    x + options.INTERVAL_WIDTH
                ]);
            });
            return new KhanUtil.PiecewiseFunction({
                fnArray: fnArray,
                rangeArray: rangeArray
            });
        }
    },
    VisualizingDerivativesProblem: function (options) {
        options = $.extend(true, {
            XLIMS: [
                0,
                14
            ],
            YLIMS: [
                -2,
                4
            ],
            GRAPH_LIMS: [
                [],
                []
            ],
            INTERVAL_WIDTH: 2,
            problem: null,
            graph: null,
            nIntervals: 7,
            nProblemIntervals: 1,
            offset: 0.5,
            breakIndex: 3,
            noSolution: false,
            moveDerivative: true,
            fnColor: KhanUtil.BLUE,
            derivColor: KhanUtil.RED
        }, options);
        $.extend(this, options);
        this._setAxisLims = function () {
            var width = this.INTERVAL_WIDTH;
            var n = this.nIntervals;
            this.XLIMS = [
                0,
                width * n
            ];
            this.YLIMS = [
                -width,
                2 * width
            ];
            var pad = function (lims, padAmt) {
                return [
                    lims[0] - padAmt,
                    lims[1] + padAmt
                ];
            };
            this.GRAPH_LIMS = [
                pad(this.XLIMS, width),
                pad(this.YLIMS, 1)
            ];
        };
        this._invalidParams = function (piecewiseFn, startIndex, nIntervals) {
            var outOfBounds = startIndex + nIntervals > piecewiseFn.length();
            if (!piecewiseFn || startIndex === null || nIntervals === 0 || outOfBounds) {
                return true;
            }
            return false;
        };
        this.chooseProblemStart = function (totalIntervals, nIntervals, offset) {
            var upperBound = totalIntervals - (nIntervals + Math.ceil(offset));
            return KhanUtil.randRange(0, upperBound);
        };
        this.matchesToProblemRanges = function (matches, nIntervals, offset) {
            var w = this.INTERVAL_WIDTH;
            return _.map(matches, function (matchIndex) {
                var startIndex = matchIndex + offset;
                var endIndex = startIndex + nIntervals;
                return _.map([
                    startIndex,
                    endIndex
                ], function (x) {
                    return w * x;
                });
            });
        };
        this.generateProblem = function (piecewiseFn, startIndex, nIntervals, offset) {
            nIntervals += offset === 0 ? 0 : 1;
            if (this._invalidParams(piecewiseFn, startIndex, nIntervals)) {
                return null;
            }
            var endIndex = startIndex + nIntervals;
            var problem = piecewiseFn.slice(startIndex, endIndex);
            problem.trimRangeArrayEnds(offset);
            return problem;
        };
        this.generateBogusProblem = function (piecewiseFn, startIndex, nIntervals, offset) {
            nIntervals += offset === 0 ? 0 : 1;
            if (this._invalidParams(piecewiseFn, startIndex, nIntervals)) {
                return null;
            }
            var generator = KhanUtil.PiecewiseFunctionGenerator;
            var bogusProblem;
            var loopCount = 0;
            var validBogus = false;
            while (!validBogus) {
                if (nIntervals === 1) {
                    bogusProblem = generator.generate({
                        nIntervals: 1,
                        INTERVAL_WIDTH: this.INTERVAL_WIDTH,
                        YLIMS: this.YLIMS
                    });
                } else {
                    var nValidIntervals = KhanUtil.randRange(1, nIntervals - 1);
                    var nBogusIntervals = nIntervals - nValidIntervals;
                    var endIndex = startIndex + nValidIntervals;
                    var prefixFn = piecewiseFn.slice(startIndex, endIndex);
                    var n = prefixFn.length();
                    var prevSegment = prefixFn.fnArray[n - 1];
                    bogusProblem = generator.generate({
                        numSegments: nBogusIntervals,
                        prevSegment: prevSegment,
                        INTERVAL_WIDTH: this.INTERVAL_WIDTH,
                        YLIMS: this.YLIMS
                    });
                    bogusProblem = prefixFn.concat(bogusProblem);
                }
                var matches = piecewiseFn.matches(bogusProblem, true);
                if (!matches.length) {
                    validBogus = true;
                }
                if (loopCount > 50) {
                    return null;
                }
                loopCount++;
            }
            bogusProblem.trimRangeArrayEnds(offset);
            return bogusProblem;
        };
        this.initSlidingWindow = function (options) {
            this.graphie.addMouseLayer();
            var problem = options.problem;
            var xlims = this.GRAPH_LIMS[0];
            var ylims = this.GRAPH_LIMS[1];
            var xmin = xlims[0] + 1;
            var xmax = xlims[1] - 1;
            var ymin = ylims[0];
            var ymax = ylims[1];
            var height = ymax - ymin;
            var slidingWindow = this.graphie.addRectGraph({
                x: xmin,
                y: ymin,
                width: problem.width(),
                height: height,
                normalStyle: {
                    area: {
                        'fill-opacity': 0.08,
                        fill: options.color
                    },
                    edges: { 'stroke-width': 0 },
                    points: { opacity: 0 }
                },
                hoverStyle: {
                    area: {
                        'fill-opacity': 0.14,
                        fill: options.color
                    },
                    points: { opacity: 0 }
                },
                fixed: {
                    edges: [
                        true,
                        true,
                        true,
                        true
                    ],
                    points: [
                        true,
                        true,
                        true,
                        true
                    ]
                },
                constraints: {
                    constrainX: false,
                    constrainY: true,
                    xmin: xmin,
                    xmax: xmax
                },
                onMove: function (dx, dy) {
                    problem.translatePlot(dx, dy);
                    problem.toFront();
                },
                snapX: 1
            });
            var speed = 20;
            slidingWindow.doHide = function () {
                slidingWindow.hide(speed);
                problem.hide(speed);
                options.onHide();
            };
            slidingWindow.doShow = function () {
                slidingWindow.show(speed);
                problem.show(speed);
                options.onShow();
            };
            slidingWindow.toFront();
            problem.toFront();
            var xOffset = xmin + -problem.rangeArray[0][0];
            problem.translatePlot(xOffset, 0);
            slidingWindow.startRange = [
                xmin,
                xmin + problem.width()
            ];
            this.slidingWindow = slidingWindow;
        };
        this.init = function () {
            var generator = KhanUtil.PiecewiseFunctionGenerator;
            this._setAxisLims();
            this.graph = generator.generate({
                numSegments: this.nIntervals,
                breakIndex: this.breakIndex,
                INTERVAL_WIDTH: this.INTERVAL_WIDTH,
                YLIMS: this.YLIMS
            });
            var n = this.nProblemIntervals;
            var offset = this.offset;
            var start = this.chooseProblemStart(this.graph.length(), n, offset);
            if (this.noSolution) {
                this.problem = this.generateBogusProblem(this.graph, start, n, offset);
                if (this.problem === null) {
                    this.init();
                    return;
                }
            } else {
                this.problem = this.generateProblem(this.graph, start, n, offset);
            }
            var matches = this.graph.matches(this.problem, true);
            this.problemRanges = this.matchesToProblemRanges(matches, n, offset);
        };
        var initRectAutoscaledGraph = function (range, options) {
            var graph = KhanUtil.currentGraph;
            var xlims = range[0];
            var ylims = range[1];
            var xrange = xlims[1] - xlims[0];
            var yrange = ylims[1] - ylims[0];
            var xpixels = 480;
            options = $.extend({
                tickOpacity: 0.6,
                labelOpacity: 0.6,
                xpixels: xpixels,
                ypixels: xpixels * yrange / xrange,
                xdivisions: xrange,
                ydivisions: yrange,
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
                options.xpixels / xrange,
                options.ypixels / yrange
            ];
            options.gridStep = [
                xrange / options.xdivisions,
                yrange / options.ydivisions
            ];
            graph.xpixels = options.xpixels;
            graph.ypixels = options.ypixels;
            graph.range = options.range;
            graph.scale = options.scale;
            graph.graphInit(options);
        };
        this.render = function (options) {
            initRectAutoscaledGraph(this.GRAPH_LIMS, {});
            this.graphie = KhanUtil.currentGraph;
            var windowColor = this.derivColor;
            if (this.moveDerivative) {
                this.graph.plot({
                    color: this.fnColor,
                    graphie: this.graphie
                });
                this.problem.plot({
                    color: this.derivColor,
                    plotDerivative: true,
                    omitEnds: false,
                    graphie: this.graphie
                });
            } else {
                this.graph.plot({
                    color: this.derivColor,
                    plotDerivative: true,
                    graphie: this.graphie
                });
                this.problem.plot({
                    color: this.fnColor,
                    omitEnds: true,
                    graphie: this.graphie
                });
                windowColor = this.fnColor;
            }
            var checkboxIdentifier = '.sol.no-solution :checkbox';
            this.initSlidingWindow({
                problem: this.problem,
                color: windowColor,
                onHide: function () {
                    $(checkboxIdentifier).attr('checked', true);
                },
                onShow: function () {
                    $(checkboxIdentifier).attr('checked', false);
                }
            });
            this.bindNoSolutionHide(checkboxIdentifier);
            return this.slidingWindow;
        };
        this.resetCurrentGraph = function () {
            KhanUtil.currentGraph = this.graphie;
        };
        this.hints = function () {
            var hints = [];
            this.hintproblems = [];
            var moveDeriv = this.moveDerivative;
            var self = this;
            _.each(this.problem.fnArray, function (fn, i) {
                var nth = i > 0 ? $._('next') : $._('first');
                fn = fn.derivative();
                var nCoefs = fn.coefs.length;
                var hint;
                if (nCoefs === 1) {
                    var val = '<code>' + fn.coefs[0] + '</code>';
                    if (moveDeriv) {
                        hint = $._('The %(nth)s section of the derivative has a constant ' + 'value of %(val)s, so it corresponds to an original function with ' + 'a constant <b>slope</b> of %(val)s.', {
                            nth: nth,
                            val: val
                        });
                    } else {
                        hint = $._('The %(nth)s section of the antiderivative has a constant ' + 'slope of %(val)s, so it corresponds to an original function ' + 'that has a constant value of %(val)s.', {
                            nth: nth,
                            val: val
                        });
                    }
                } else if (nCoefs === 2) {
                    var inc;
                    var val = fn.evalOf(0) + fn.evalOf(self.INTERVAL_WIDTH);
                    if (val >= 0) {
                        if (fn.coefs[1] > 0) {
                            inc = $._('increasing and positive');
                        } else {
                            inc = $._('decreasing and positive');
                        }
                    } else {
                        if (fn.coefs[1] > 0) {
                            inc = $._('increasing and negative');
                        } else {
                            inc = $._('decreasing and negative');
                        }
                    }
                    if (moveDeriv) {
                        hint = $._('The %(nth)s section of the derivative is %(inc)s, ' + 'so it corresponds to an original function whose ' + '<b>slope</b> is %(inc)s.', {
                            nth: nth,
                            inc: inc
                        });
                    } else {
                        hint = $._('The %(nth)s section of the antiderivative has a ' + '%(inc)s slope, so it corresponds to an original ' + 'function that is %(inc)s.', {
                            nth: nth,
                            inc: inc
                        });
                    }
                }
                var hintproblem = self.problem.slice(i, i + 1);
                hintproblem.calibrate();
                self.hintproblems.push(hintproblem);
                hints.push('<p>' + hint + '</p><div class=\'clearfix\'> <div class=\'graphie vis-deriv-hint-graph\' id=\'orig' + i + '\'>   PROBLEM.showHint(' + i + ', ' + moveDeriv + ');</div>' + '<div class=\'graphie vis-deriv-hint-graph\' id=\'orig' + i + '\'> PROBLEM.showHint(' + i + ', ' + !moveDeriv + ');</div> </div>');
            });
            var lastHint;
            if (this.noSolution) {
                lastHint = $._('Because these sections do not appear next ' + 'to each other in the graph of <code>f(x)</code>, ' + 'there is no solution.');
                hints.push('<p>' + lastHint + '</p>');
                hints.push('<div class=\'graphie\'> PROBLEM.showNoAnswer(); </div>');
            } else {
                var solnText = this.problemRanges.map(function (range) {
                    return '<code>x \\in [' + range.join(', ') + ']</code>';
                }).join(' and ');
                var fnVar = moveDeriv ? 'f\'(x)' : 'F(x)';
                lastHint = $._('The function in the window corresponds to ' + '<code>%(fnVar)s</code> where %(solution)s.', {
                    fnVar: fnVar,
                    solution: solnText
                });
                var firstAnswer = this.problemRanges[0][0];
                hints.push('<p>' + lastHint + '</p>');
                hints.push('<div class=\'graphie\'> PROBLEM.showAnswer(' + firstAnswer + '); </div>');
            }
            return hints;
        };
        var initHintGraph = function (range, options) {
            var graph = KhanUtil.currentGraph;
            var xlims = range[0];
            var ylims = range[1];
            var xrange = xlims[1] - xlims[0];
            var yrange = ylims[1] - ylims[0];
            var xpixels = 480 / 18 * Math.abs(range[0][1] - range[0][0]);
            options = $.extend({
                xpixels: xpixels,
                ypixels: xpixels * yrange / xrange,
                xdivisions: xrange,
                ydivisions: yrange,
                labels: true,
                unityLabels: true,
                range: range
            }, options);
            options.scale = [
                options.xpixels / xrange,
                options.ypixels / yrange
            ];
            options.gridStep = [
                xrange / options.xdivisions,
                yrange / options.ydivisions
            ];
            graph.xpixels = options.xpixels;
            graph.ypixels = options.ypixels;
            graph.range = options.range;
            graph.scale = options.scale;
            graph.graphInit(options);
            return graph;
        };
        this.showHint = function (i, deriv) {
            var segment = this.hintproblems[i];
            var hintGraphie;
            if (deriv) {
                hintGraphie = initHintGraph([
                    [
                        1,
                        5
                    ],
                    [
                        -3,
                        3
                    ]
                ], {
                    axisOpacity: 1,
                    labelOpacity: 0.01,
                    tickOpacity: 0.01
                });
                segment.plot({
                    color: this.derivColor,
                    plotDerivative: true,
                    omitEnds: false,
                    graphie: hintGraphie
                });
            } else {
                hintGraphie = initHintGraph([
                    [
                        1,
                        5
                    ],
                    [
                        -3,
                        3
                    ]
                ], {
                    axisOpacity: 0.01,
                    labelOpacity: 0.01,
                    tickOpacity: 0.01
                });
                segment.plot({
                    color: this.fnColor,
                    omitEnds: true,
                    graphie: hintGraphie
                });
            }
            this.resetCurrentGraph();
        };
        this.showAnswer = function (firstAnswer) {
            this.slidingWindow.doShow();
            this.slidingWindow.moveTo(firstAnswer, 0);
            this.resetCurrentGraph();
        };
        this.showNoAnswer = function () {
            this.slidingWindow.doHide();
            this.resetCurrentGraph();
        };
        this.bindNoSolutionHide = function (checkboxIdentifier) {
            var slidingHidden = false;
            var sliding = this.slidingWindow;
            $('body').on('click', checkboxIdentifier, function () {
                slidingHidden = !slidingHidden;
                if (slidingHidden) {
                    sliding.doHide();
                } else {
                    sliding.doShow();
                }
            });
        };
        this.init();
    }
});
},{}]},{},[1]);
