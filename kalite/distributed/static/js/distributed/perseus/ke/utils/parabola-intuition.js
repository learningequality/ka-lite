(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    doParabolaInteraction: function (func, vertex, directrix) {
        var graph = KhanUtil.currentGraph;
        var vertexLine = KhanUtil.bogusShape;
        var directrixLine = KhanUtil.bogusShape;
        var lineEndcap = KhanUtil.bogusShape;
        var highlighted = false;
        func.onMove = function (coordX, coordY) {
            vertexLine.remove();
            directrixLine.remove();
            lineEndcap.remove();
            graph.style({
                strokeWidth: 1.5,
                stroke: KhanUtil.GREEN,
                opacity: 0
            });
            var vertexDistance = KhanUtil.getDistance([
                coordX,
                coordY
            ], vertex.coord);
            vertexLine = graph.line([
                coordX,
                coordY
            ], vertex.coord);
            if (directrix.coordA[1] < coordY) {
                directrixLine = graph.line([
                    coordX,
                    coordY
                ], [
                    coordX,
                    coordY - vertexDistance
                ]);
                lineEndcap = graph.line([
                    coordX - 0.05,
                    coordY - vertexDistance
                ], [
                    coordX + 0.05,
                    coordY - vertexDistance
                ]);
            } else {
                directrixLine = graph.line([
                    coordX,
                    coordY
                ], [
                    coordX,
                    coordY + vertexDistance
                ]);
                lineEndcap = graph.line([
                    coordX - 0.05,
                    coordY + vertexDistance
                ], [
                    coordX + 0.05,
                    coordY + vertexDistance
                ]);
            }
            vertexLine.toBack();
            directrixLine.toBack();
            if (!highlighted) {
                vertexLine.animate({ opacity: 1 }, 100);
                directrixLine.animate({ opacity: 1 }, 100);
                lineEndcap.animate({ opacity: 1 }, 100);
            } else {
                vertexLine.attr({ opacity: 1 });
                directrixLine.attr({ opacity: 1 });
                lineEndcap.attr({ opacity: 1 });
            }
            highlighted = true;
        };
        func.onLeave = function (coordX, coordY) {
            vertexLine.animate({ opacity: 0 }, 100);
            directrixLine.animate({ opacity: 0 }, 100);
            lineEndcap.animate({ opacity: 0 }, 100);
            highlighted = false;
        };
    },
    doHyperbolaInteraction: function (func, focus1, focus2) {
        var graph = KhanUtil.currentGraph;
        var focusLine1 = KhanUtil.bogusShape;
        var focusLine2 = KhanUtil.bogusShape;
        var highlighted = false;
        func.onMove = function (coordX, coordY) {
            focusLine1.remove();
            focusLine2.remove();
            graph.style({
                strokeWidth: 1.5,
                stroke: KhanUtil.GREEN,
                opacity: 0
            });
            focusLine1 = graph.line([
                coordX,
                coordY
            ], focus1.coord);
            graph.style({ stroke: KhanUtil.RED });
            focusLine2 = graph.line([
                coordX,
                coordY
            ], focus2.coord);
            focusLine1.toBack();
            focusLine2.toBack();
            if (!highlighted) {
                focusLine1.animate({ opacity: 1 }, 100);
                focusLine2.animate({ opacity: 1 }, 100);
                $('#problemarea div.focus-instructions').hide();
                $('#problemarea div.focus-distances').show();
            } else {
                focusLine1.attr({ opacity: 1 });
                focusLine2.attr({ opacity: 1 });
            }
            highlighted = true;
            this.writeDistances(coordX, coordY);
        };
        func.onLeave = function (coordX, coordY) {
            focusLine1.animate({ opacity: 0 }, 100);
            focusLine2.animate({ opacity: 0 }, 100);
            $('#problemarea div.focus-instructions').show();
            $('#problemarea div.focus-distances').hide();
            highlighted = false;
        };
    },
    doEllipseInteraction: function (ellipse, focus1, focus2) {
        var graph = KhanUtil.currentGraph;
        var focusLine1 = KhanUtil.bogusShape;
        var focusLine2 = KhanUtil.bogusShape;
        var highlighted = false;
        ellipse.onMove = function (coordX, coordY) {
            focusLine1.remove();
            focusLine2.remove();
            graph.style({
                strokeWidth: 1.5,
                stroke: KhanUtil.GREEN,
                opacity: 0
            });
            focusLine1 = graph.line([
                coordX,
                coordY
            ], focus1.coord);
            graph.style({ stroke: KhanUtil.RED });
            focusLine2 = graph.line([
                coordX,
                coordY
            ], focus2.coord);
            focusLine1.toBack();
            focusLine2.toBack();
            if (!highlighted) {
                focusLine1.animate({ opacity: 1 }, 100);
                focusLine2.animate({ opacity: 1 }, 100);
                $('#problemarea div.focus-instructions').hide();
                $('#problemarea div.focus-distances').show();
            } else {
                focusLine1.attr({ opacity: 1 });
                focusLine2.attr({ opacity: 1 });
            }
            highlighted = true;
            this.writeDistances(coordX, coordY);
        };
        ellipse.onLeave = function (coordX, coordY) {
            focusLine1.animate({ opacity: 0 }, 100);
            focusLine2.animate({ opacity: 0 }, 100);
            $('#problemarea div.focus-instructions').show();
            $('#problemarea div.focus-distances').hide();
            highlighted = false;
        };
    }
});
},{}]},{},[1]);
