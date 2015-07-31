(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var getSubHints = function (id, title, subHints) {
    var str = '[<a href=\'#\' class=\'show-subhint\' data-subhint=\'' + id + '\'>' + title + '</a>]</p>';
    str += '<div class=\'subhint\' id=\'' + id + '\'>';
    for (var iHint = 0; iHint < subHints.length; iHint++) {
        str += '<p>' + subHints[iHint] + '</p>';
    }
    str += '</div>';
    return str;
};
$(document).on('click', 'a.show-subhint', function (event) {
    var subhint = $('#' + $(this).data('subhint'));
    var visibleText = $(this).data('visible-text') || $(this).text();
    var hiddenText = $(this).data('hidden-text') || 'Hide explanation';
    $(this).data({
        'visible-text': visibleText,
        'hidden-text': hiddenText
    });
    if (subhint.is(':visible')) {
        $(this).text(visibleText);
    } else {
        $(Exercises).trigger('subhintExpand', [$(this).data('subhint')]);
        $(this).text(hiddenText);
    }
    var $el = $('#' + $(this).data('subhint'));
    $el.toggle(200, function () {
        $el.find('code').each(function (i, code) {
            KhanUtil.processMath(code, null, true);
        });
    });
    return false;
});
$(document).on('mouseenter mouseleave', 'a.show-definition', function (event) {
    $('#' + $(this).data('definition')).toggle(200);
    return false;
});
$(document).on('click', 'a.show-definition', function (e) {
    e.preventDefault();
});
$.extend(KhanUtil, { getSubHints: getSubHints });
},{}]},{},[1]);
