(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    spin: function (content) {
        var startingBracePos = -1;
        var nestingLevel = 0;
        for (var i = 0; i < content.length; i++) {
            if (content.charAt(i) === '{') {
                if (startingBracePos === -1) {
                    startingBracePos = i;
                } else {
                    nestingLevel++;
                }
            } else if (content.charAt(i) === '}' && startingBracePos !== -1) {
                if (nestingLevel === 0) {
                    var spun = KhanUtil.spin(content.substring(startingBracePos + 1, i));
                    content = content.substring(0, startingBracePos) + spun + content.substring(i + 1);
                    i -= i - startingBracePos - spun.length + 1;
                    startingBracePos = -1;
                } else {
                    nestingLevel--;
                }
            }
        }
        return KhanUtil.randFromArray(content.split('|'));
    }
});
$.fn.spin = function () {
    this.find('.spin').each(function () {
        var spun = KhanUtil.spin($(this).html());
        $(this).html(spun);
    });
};
},{}]},{},[1]);
