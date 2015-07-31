(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    getCipherMessage: function (num) {
        return [
            $._('i have learned all kinds of different things from using khan academy'),
            $._('the world is filled with secrets and mysteries just waiting to be discovered'),
            $._('when a message contains a single character by itself, it is most likely either the letter i or a'),
            $._('words which have repeating letters like too and all can also give a hint to what the secret message is'),
            $._('you have just cracked a caesar cipher and obtained the title of code breaker')
        ][num - 1];
    },
    applyCaesar: function (msg, shift) {
        var cipher = '', lc = 'abcdefghijklmnopqrstuvwxyz', uc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        for (var i = 0, len = msg.length; i < len; i++) {
            if (msg[i] >= 'a' && msg[i] <= 'z') {
                cipher = cipher + lc[(lc.indexOf(msg[i]) + shift) % 26];
            } else if (msg[i] >= 'A' && msg[i] <= 'Z') {
                cipher = cipher + uc[(uc.indexOf(msg[i]) + shift) % 26];
            } else {
                cipher = cipher + msg[i];
            }
        }
        return cipher;
    },
    applyVigenere: function (msg, key) {
        var cipher = '', shift = 0, count = 0, lc = 'abcdefghijklmnopqrstuvwxyz', uc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', k = key.toLowerCase();
        for (var i = 0, len = msg.length, keyLen = k.length; i < len; i++) {
            shift = lc.indexOf(k[count % keyLen]);
            if (msg[i] >= 'a' && msg[i] <= 'z') {
                cipher = cipher + lc[(lc.indexOf(msg[i]) + shift) % 26];
                count++;
            } else if (msg[i] >= 'A' && msg[i] <= 'Z') {
                cipher = cipher + uc[(uc.indexOf(msg[i]) + shift) % 26];
                count++;
            } else {
                cipher = cipher + msg[i];
            }
        }
        return cipher;
    },
    normEnglishLetterFreq: function (scale) {
        var freq = [
            0.08167,
            0.01492,
            0.02782,
            0.04253,
            0.12702,
            0.02228,
            0.02015,
            0.06094,
            0.06966,
            0.00154,
            0.00772,
            0.04024,
            0.02406,
            0.06749,
            0.07507,
            0.01929,
            0.00095,
            0.05987,
            0.06327,
            0.09056,
            0.02758,
            0.00978,
            0.0236,
            0.0015,
            0.01974,
            0.00074
        ];
        for (var i = 0, len = freq.length; i < len; i++) {
            freq[i] = freq[i] * scale;
        }
        return freq;
    },
    normCipherLetterFreq: function (cipher, scale) {
        var msg = cipher.toLowerCase(), freq = [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0
            ], count = 0, lc = 'abcdefghijklmnopqrstuvwxyz';
        for (var i = 0, len = msg.length; i < len; i++) {
            if (msg[i] >= 'a' && msg[i] <= 'z') {
                freq[lc.indexOf(msg[i])]++;
                count++;
            }
        }
        for (var i = 0, len = freq.length; i < len; i++) {
            freq[i] = freq[i] / count * scale;
        }
        return freq;
    }
});
},{}]},{},[1]);
