(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    coinFlips: function (n) {
        if (n === 0) {
            return [[
                    '',
                    0
                ]];
        } else {
            var preceding = KhanUtil.coinFlips(n - 1);
            var andAHead = $.map(preceding, function (_arg, i) {
                var seq = _arg[0];
                var h = _arg[1];
                return [[
                        $._('H') + seq,
                        h + 1
                    ]];
            });
            var andATail = $.map(preceding, function (_arg, i) {
                var seq = _arg[0];
                var h = _arg[1];
                return [[
                        $._('T') + seq,
                        h
                    ]];
            });
            return andAHead.concat(andATail);
        }
    },
    choose: function (n, k) {
        if (typeof k === 'number') {
            if (k * 2 > n) {
                return KhanUtil.choose(n, n - k);
            } else if (k > 0.5) {
                return KhanUtil.choose(n, k - 1) * (n - k + 1) / k;
            } else if (Math.abs(k) <= 0.5) {
                return 1;
            } else {
                return 0;
            }
        } else {
            var sum = 0;
            $.each(k, function (ind, elem) {
                sum += KhanUtil.choose(n, elem);
            });
            return sum;
        }
    }
});
},{}]},{},[1]);
