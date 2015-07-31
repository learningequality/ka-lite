(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    initSliceClone: function (goalBlocks) {
        KhanUtil.pieces = 1;
        KhanUtil.times = {};
        for (var i = 0; i < goalBlocks.length; i++) {
            KhanUtil.times[goalBlocks[i]] = 1;
        }
    },
    changePieces: function (increase) {
        if (KhanUtil.pieces === 1 && !increase) {
            return;
        }
        KhanUtil.pieces += increase ? 1 : -1;
        $('#pieces').text(KhanUtil.plural(KhanUtil.pieces, 'piece'));
        KhanUtil.currentGraph = $('#problemarea').find('#parent_block').data('graphie');
        rectchart([
            1,
            KhanUtil.pieces - 1
        ], [
            '#e00',
            '#999'
        ]);
        KhanUtil.updateGraphAndAnswer();
    },
    changeTimes: function (increase, id) {
        if (KhanUtil.times[id] === 1 && !increase) {
            return;
        }
        KhanUtil.times[id] += increase ? 1 : -1;
        $('#' + id + '_times').text(KhanUtil.plural(KhanUtil.times[id], 'time'));
        KhanUtil.updateGraphAndAnswer();
    },
    updateGraphAndAnswer: function () {
        var pieces = KhanUtil.pieces;
        _.each(KhanUtil.times, function (times, id) {
            KhanUtil.currentGraph = $('#problemarea').find('#' + id).data('graphie');
            KhanUtil.currentGraph.raphael.clear();
            KhanUtil.currentGraph.init({
                range: [
                    [
                        0,
                        1
                    ],
                    [
                        0,
                        1
                    ]
                ],
                scale: [
                    500 / pieces * times,
                    25
                ]
            });
            rectchart([
                times,
                0
            ], [
                '#e00',
                '#999'
            ]);
            $('#' + id + '_answer input').val(KhanUtil.roundTo(3, times / pieces));
        });
    }
});
},{}]},{},[1]);
