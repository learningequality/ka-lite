/*
 * Point Utils
 * A point is an array of two numbers e.g. [0, 0].
 */
define(function(require) {

var kvector = require("./kvector.js");
var knumber = require("./knumber.js");

var kpoint = KhanUtil.kpoint = {

    // Rotate point (around origin unless a center is specified)
    rotateRad: function(point, theta, center) {
        if (center === undefined) {
            return kvector.rotateRad(point, theta);
        } else {
            return kvector.add(
                center,
                kvector.rotateRad(
                    kvector.subtract(point, center),
                    theta
                )
            );
        }
    },

    rotateDeg: function(point, theta, center) {
        if (center === undefined) {
            return kvector.rotateDeg(point, theta);
        } else {
            return kvector.add(
                center,
                kvector.rotateDeg(
                    kvector.subtract(point, center),
                    theta
                )
            );
        }
    },

    // Distance between two points
    distanceToPoint: function(point1, point2) {
        return kvector.length(kvector.subtract(point1, point2));
    },

    // Distance between point and line
    distanceToLine: function(point, line) {
        var lv = kvector.subtract(line[1], line[0]);
        var pv = kvector.subtract(point, line[0]);
        var projectedPv = kvector.projection(pv, lv);
        var distancePv = kvector.subtract(projectedPv, pv);
        return kvector.length(distancePv);
    },

    // Reflect point over line
    reflectOverLine: function(point, line) {
        var lv = kvector.subtract(line[1], line[0]);
        var pv = kvector.subtract(point, line[0]);
        var projectedPv = kvector.projection(pv, lv);
        var reflectedPv = kvector.subtract(kvector.scale(projectedPv, 2), pv);
        return kvector.add(line[0], reflectedPv);
    },

    /**
     * Compares two points, returning -1, 0, or 1, for use with
     * Array.prototype.sort
     *
     * Note: This technically doesn't satisfy the total-ordering
     * requirements of Array.prototype.sort unless equalityTolerance
     * is 0. In some cases very close points that compare within a
     * few equalityTolerances could appear in the wrong order.
     */
    compare: function(point1, point2, equalityTolerance) {
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
    // Check if a value is a point
    is: kvector.is,

    // Add and subtract vector(s)
    addVector: kvector.add,
    addVectors: kvector.add,
    subtractVector: kvector.subtract,
    equal: kvector.equal,

    // Convert from cartesian to polar and back
    polarRadFromCart: kvector.polarRadFromCart,
    polarDegFromCart: kvector.polarDegFromCart,
    cartFromPolarRad: kvector.cartFromPolarRad,
    cartFromPolarDeg: kvector.cartFromPolarDeg,

    // Rounding
    round: kvector.round,
    roundTo: kvector.roundTo,
    floorTo: kvector.floorTo,
    ceilTo: kvector.ceilTo
});

return kpoint;

});
