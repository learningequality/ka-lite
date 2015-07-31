(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.fn['qhintsLoad'] = function () {
    var checkAnswer = function (parent, source) {
        var feedback = parent.find('.qhint-feedback');
        if (feedback.length) {
            return;
        }
        feedback = $('<p>', { 'class': 'qhint-feedback' });
        var answer = $(parent.find('.qhint-answer')).text();
        var input = parent.find('.qhint-input');
        var userInput = '';
        if (source) {
            var type = source.attr('type');
            if (type === 'text' || type === 'submit') {
                userInput = $(parent.find('input:text')).val();
            } else if (type === 'button') {
                userInput = source.val();
            } else if (source.is('a')) {
                userInput = source.text();
            }
        }
        input.hide();
        if (!source) {
            feedback.text(answer);
        } else if (userInput === answer) {
            feedback.text($._('Correct! The answer is %(answer)s.', { answer: answer })).addClass('correct');
        } else {
            feedback.text($._('Incorrect. The answer is %(answer)s.', { answer: answer })).addClass('incorrect');
        }
        parent.append(feedback);
    };
    var handleCheck = function (e) {
        var parent = $(e.currentTarget).parents('.qhint');
        checkAnswer(parent, $(e.currentTarget));
    };
    var selectors = '.qhint input:submit, .qhint input:button, .qhint a.qhint-button';
    $('body').on('click', selectors, handleCheck);
    $('body').on('keydown', '.qhint input:text', function (e) {
        if (e.keyCode === 13) {
            handleCheck(e);
        }
    });
    $(Khan).on('hintUsed', function () {
        var lastQhElem = $('.qhint').last();
        if (lastQhElem.length) {
            checkAnswer(lastQhElem, null);
        }
    });
};
},{}]},{},[1]);
