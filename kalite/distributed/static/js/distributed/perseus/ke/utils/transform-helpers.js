(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
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
},{}]},{},[1]);
