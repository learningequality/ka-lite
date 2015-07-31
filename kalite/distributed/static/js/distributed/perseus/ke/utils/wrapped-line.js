(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
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
},{}],2:[function(require,module,exports){
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
},{"./knumber.js":1,"./kvector.js":3}],3:[function(require,module,exports){
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
},{"./knumber.js":1}],4:[function(require,module,exports){
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
},{}],5:[function(require,module,exports){
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
},{}],6:[function(require,module,exports){
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
},{"./kvector.js":3,"./objective_.js":4,"./transform-helpers.js":5}],7:[function(require,module,exports){
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
},{"./kpoint.js":2,"./kvector.js":3,"./transform-helpers.js":5,"./wrapped-defaults.js":6}]},{},[7]);
