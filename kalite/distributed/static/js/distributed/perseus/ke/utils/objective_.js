(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
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
},{}]},{},[1]);
