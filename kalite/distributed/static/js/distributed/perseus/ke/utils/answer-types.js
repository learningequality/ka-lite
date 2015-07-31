(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var MAXERROR_EPSILON = Math.pow(2, -42);
var extractRawCode = function (elem) {
    var $elem = $(elem).clone(true);
    var code = $elem.find('code');
    if (code.length) {
        $.each(code, function (i, elem) {
            $(elem).replaceWith('<code><script type="math/tex">' + KhanUtil.retrieveMathFormula(elem) + '</script></code>');
        });
    }
    return $elem.html();
};
function getTextSquish(elem) {
    return $(elem).text().replace(/\s+/g, '');
}
function checkIfAnswerEmpty(guess) {
    return $.trim(guess) === '' || guess instanceof Array && $.trim(guess.join('').replace(/,/g, '')) === '';
}
function addExamplesToInput($input, examples) {
    if ($input.data('qtip')) {
        $input.qtip('destroy', true);
    }
    var $examples = $('<ul class="examples" style="display: none"></ul>');
    _.each(examples, function (example) {
        $examples.append('<li>' + example + '</li>');
    });
    $input.qtip({
        content: {
            text: $examples.remove(),
            prerender: true
        },
        style: { classes: 'qtip-light leaf-tooltip' },
        position: {
            my: 'top left',
            at: 'bottom left'
        },
        show: {
            delay: 0,
            effect: { length: 0 },
            event: 'focus'
        },
        hide: {
            delay: 0,
            event: 'blur'
        },
        events: {
            render: function () {
                $examples.children().runModules();
            }
        }
    });
}
Khan.answerTypes = $.extend(Khan.answerTypes, {
    text: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var input;
            if (window.Modernizr && Modernizr.touchevents) {
                input = $('<input type="text" autocapitalize="off">');
            } else {
                input = $('<input type="text">');
            }
            $(solutionarea).append(input);
            return {
                validator: Khan.answerTypes.text.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return input.val();
                },
                solution: $.trim(solutionText),
                showGuess: function (guess) {
                    input.val(guess === undefined ? '' : guess);
                }
            };
        },
        createValidatorFunctional: function (correct, options) {
            options = $.extend({ correctCase: 'required' }, options);
            correct = $.trim(correct);
            return function (guess) {
                var fallback = options.fallback != null ? '' + options.fallback : '';
                guess = $.trim(guess) || fallback;
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                if (guess.toLowerCase() === correct.toLowerCase()) {
                    if (correct === guess || options.correctCase === 'optional') {
                        score.correct = true;
                    } else {
                        if (guess === guess.toLowerCase()) {
                            score.message = $._('Your answer is almost correct, but ' + 'must be in capital letters.');
                        } else if (guess === guess.toUpperCase()) {
                            score.message = $._('Your answer is almost correct, but ' + 'must not be in capital letters.');
                        } else {
                            score.message = $._('Your answer is almost correct, but ' + 'must be in the correct case.');
                        }
                    }
                }
                return score;
            };
        }
    },
    predicate: {
        defaultForms: 'integer, proper, improper, mixed, decimal',
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var options = $.extend({
                simplify: 'required',
                ratio: false,
                forms: Khan.answerTypes.predicate.defaultForms
            }, solutionData);
            var acceptableForms = options.forms.split(/\s*,\s*/);
            if (options.inexact === undefined) {
                options.maxError = 0;
            }
            options.maxError = +options.maxError + MAXERROR_EPSILON;
            var $input = $('<input type="text" autocapitalize="off">');
            $(solutionarea).append($input);
            var exampleForms = {
                integer: $._('an integer, like <code>6</code>'),
                proper: function () {
                    if (options.simplify === 'optional') {
                        return $._('a <em>proper</em> fraction, like ' + '<code>1/2</code> or <code>6/10</code>');
                    } else {
                        return $._('a <em>simplified proper</em> ' + 'fraction, like <code>3/5</code>');
                    }
                }(),
                improper: function () {
                    if (options.simplify === 'optional') {
                        return $._('an <em>improper</em> fraction, like ' + '<code>10/7</code> or <code>14/8</code>');
                    } else {
                        return $._('a <em>simplified improper</em> ' + 'fraction, like <code>7/4</code>');
                    }
                }(),
                pi: $._('a multiple of pi, like <code>12\\ \\text{pi}</code> ' + 'or <code>2/3\\ \\text{pi}</code>'),
                log: $._('an expression, like <code>\\log(100)</code>'),
                percent: $._('a percent, like <code>%(NUM)s\\%</code>', { NUM: KhanUtil.localeToFixed(12.34, 2) }),
                mixed: $._('a mixed number, like <code>1\\ 3/4</code>'),
                decimal: function () {
                    if (options.inexact === undefined) {
                        return $._('an <em>exact</em> decimal, like ' + '<code>%(NUM)s</code>', { NUM: KhanUtil.localeToFixed(0.75, 2) });
                    } else {
                        return $._('a decimal, like <code>%(NUM)s</code>', { NUM: KhanUtil.localeToFixed(0.75, 2) });
                    }
                }()
            };
            var examples = [];
            $.each(acceptableForms, function (i, form) {
                if (exampleForms[form] != null) {
                    examples.push(exampleForms[form]);
                }
            });
            if (options.forms !== Khan.answerTypes.predicate.defaultForms) {
                addExamplesToInput($input, examples);
            }
            return {
                validator: Khan.answerTypes.predicate.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return $input.val();
                },
                solution: $.trim(solutionText),
                showGuess: function (guess) {
                    $input.val(guess === undefined ? '' : guess);
                }
            };
        },
        createValidatorFunctional: function (predicate, options) {
            options = $.extend({
                simplify: 'required',
                ratio: false,
                forms: Khan.answerTypes.predicate.defaultForms
            }, options);
            var acceptableForms;
            if (!_.isArray(options.forms)) {
                acceptableForms = options.forms.split(/\s*,\s*/);
            } else {
                acceptableForms = options.forms;
            }
            if (options.inexact === undefined) {
                options.maxError = 0;
            }
            options.maxError = +options.maxError + MAXERROR_EPSILON;
            if (_.contains(acceptableForms, 'percent')) {
                acceptableForms = _.without(acceptableForms, 'percent');
                acceptableForms.push('percent');
            }
            predicate = _.isFunction(predicate) ? predicate : KhanUtil.tmpl.getVAR(predicate);
            var fractionTransformer = function (text) {
                text = text.replace(/\u2212/, '-').replace(/([+-])\s+/g, '$1').replace(/(^\s*)|(\s*$)/gi, '');
                var match = text.match(/^([+-]?\d+)\s*\/\s*([+-]?\d+)$/);
                var parsedInt = parseInt(text, 10);
                if (match) {
                    var num = parseFloat(match[1]), denom = parseFloat(match[2]);
                    var simplified = denom > 0 && (options.ratio || match[2] !== '1') && KhanUtil.getGCD(num, denom) === 1;
                    return [{
                            value: num / denom,
                            exact: simplified
                        }];
                } else if (!isNaN(parsedInt) && '' + parsedInt === text) {
                    return [{
                            value: parsedInt,
                            exact: true
                        }];
                }
                return [];
            };
            var forms = {
                integer: function (text) {
                    var decimal = forms.decimal(text);
                    var rounded = forms.decimal(text, 1);
                    if (decimal[0].value != null && decimal[0].value === rounded[0].value || decimal[1].value != null && decimal[1].value === rounded[1].value) {
                        return decimal;
                    }
                    return [];
                },
                proper: function (text) {
                    return $.map(fractionTransformer(text), function (o) {
                        if (Math.abs(o.value) < 1) {
                            return [o];
                        } else {
                            return [];
                        }
                    });
                },
                improper: function (text) {
                    return $.map(fractionTransformer(text), function (o) {
                        if (Math.abs(o.value) >= 1) {
                            return [o];
                        } else {
                            return [];
                        }
                    });
                },
                pi: function (text) {
                    var match, possibilities = [];
                    text = text.replace(/\u2212/, '-');
                    if (match = text.match(/^([+-]?)\s*(\\?pi|p|\u03c0|\\?tau|t|\u03c4|pau)$/i)) {
                        possibilities = [{
                                value: parseFloat(match[1] + '1'),
                                exact: true
                            }];
                    } else if (match = text.match(/^([+-]?\s*\d+\s*(?:\/\s*[+-]?\s*\d+)?)\s*\*?\s*(\\?pi|p|\u03c0|\\?tau|t|\u03c4|pau)$/i)) {
                        possibilities = fractionTransformer(match[1]);
                    } else if (match = text.match(/^([+-]?)\s*(\d+)\s*([+-]?\d+)\s*\/\s*([+-]?\d+)\s*\*?\s*(\\?pi|p|\u03c0|\\?tau|t|\u03c4|pau)$/i)) {
                        var sign = parseFloat(match[1] + '1'), integ = parseFloat(match[2]), num = parseFloat(match[3]), denom = parseFloat(match[4]);
                        var simplified = num < denom && KhanUtil.getGCD(num, denom) === 1;
                        possibilities = [{
                                value: sign * (integ + num / denom),
                                exact: simplified
                            }];
                    } else if (match = text.match(/^([+-]?\s*\d+)\s*\*?\s*(\\?pi|p|\u03c0|\\?tau|t|\u03c4|pau)\s*(?:\/\s*([+-]?\s*\d+))?$/i)) {
                        possibilities = fractionTransformer(match[1] + '/' + match[3]);
                    } else if (match = text.match(/^([+-]?)\s*\*?\s*(\\?pi|p|\u03c0|\\?tau|t|\u03c4|pau)\s*(?:\/\s*([+-]?\d+))?$/i)) {
                        possibilities = fractionTransformer(match[1] + '1/' + match[3]);
                    } else if (text === '0') {
                        possibilities = [{
                                value: 0,
                                exact: true
                            }];
                    } else if (match = text.match(/^(.+)\s*\*?\s*(\\?pi|p|\u03c0|\\?tau|t|\u03c4|pau)$/i)) {
                        possibilities = forms.decimal(match[1]);
                    } else {
                        possibilities = _.reduce(Khan.answerTypes.predicate.defaultForms.split(/\s*,\s*/), function (memo, form) {
                            return memo.concat(forms[form](text));
                        }, []);
                        $.each(possibilities, function (ix, possibility) {
                            possibility.piApprox = true;
                        });
                        return possibilities;
                    }
                    var multiplier = Math.PI;
                    if (text.match(/\\?tau|t|\u03c4/)) {
                        multiplier = Math.PI * 2;
                    }
                    if (text.match(/pau/)) {
                        multiplier = Math.PI * 1.5;
                    }
                    $.each(possibilities, function (ix, possibility) {
                        possibility.value *= multiplier;
                    });
                    return possibilities;
                },
                coefficient: function (text) {
                    var possibilities = [];
                    text = text.replace(/\u2212/, '-');
                    if (text === '') {
                        possibilities = [{
                                value: 1,
                                exact: true
                            }];
                    } else if (text === '-') {
                        possibilities = [{
                                value: -1,
                                exact: true
                            }];
                    }
                    return possibilities;
                },
                log: function (text) {
                    var match, possibilities = [];
                    text = text.replace(/\u2212/, '-');
                    text = text.replace(/[ \(\)]/g, '');
                    if (match = text.match(/^log\s*(\S+)\s*$/i)) {
                        possibilities = forms.decimal(match[1]);
                    } else if (text === '0') {
                        possibilities = [{
                                value: 0,
                                exact: true
                            }];
                    }
                    return possibilities;
                },
                percent: function (text) {
                    text = $.trim(text);
                    var hasPercentSign = false;
                    if (text.indexOf('%') === text.length - 1) {
                        text = $.trim(text.substring(0, text.length - 1));
                        hasPercentSign = true;
                    }
                    var transformed = forms.decimal(text);
                    $.each(transformed, function (ix, t) {
                        t.exact = hasPercentSign;
                        t.value = t.value / 100;
                    });
                    return transformed;
                },
                mixed: function (text) {
                    var match = text.replace(/\u2212/, '-').replace(/([+-])\s+/g, '$1').match(/^([+-]?)(\d+)\s+(\d+)\s*\/\s*(\d+)$/);
                    if (match) {
                        var sign = parseFloat(match[1] + '1'), integ = parseFloat(match[2]), num = parseFloat(match[3]), denom = parseFloat(match[4]);
                        var simplified = num < denom && KhanUtil.getGCD(num, denom) === 1;
                        return [{
                                value: sign * (integ + num / denom),
                                exact: simplified
                            }];
                    }
                    return [];
                },
                decimal: function (text, precision) {
                    if (precision == null) {
                        precision = 10000000000;
                    }
                    var normal = function (text) {
                        text = $.trim(text);
                        var match = text.replace(/\u2212/, '-').replace(/([+-])\s+/g, '$1').match(/^([+-]?(?:\d{1,3}(?:[, ]?\d{3})*\.?|\d{0,3}(?:[, ]?\d{3})*\.(?:\d{3}[, ]?)*\d{1,3}))$/);
                        var badLeadingZero = text.match(/^0[0,]*,/);
                        if (match && !badLeadingZero) {
                            var x = parseFloat(match[1].replace(/[, ]/g, ''));
                            if (options.inexact === undefined) {
                                x = Math.round(x * precision) / precision;
                            }
                            return x;
                        }
                    };
                    var commas = function (text) {
                        text = text.replace(/([\.,])/g, function (_, c) {
                            return c === '.' ? ',' : '.';
                        });
                        return normal(text);
                    };
                    return [
                        {
                            value: normal(text),
                            exact: true
                        },
                        {
                            value: commas(text),
                            exact: true
                        }
                    ];
                }
            };
            return function (guess) {
                var fallback = options.fallback != null ? '' + options.fallback : '';
                guess = $.trim(guess) || fallback;
                var score = {
                    empty: guess === '',
                    correct: false,
                    message: null,
                    guess: guess
                };
                $.each(acceptableForms, function (i, form) {
                    var transformed = forms[form](guess);
                    for (var j = 0, l = transformed.length; j < l; j++) {
                        var val = transformed[j].value;
                        var exact = transformed[j].exact;
                        var piApprox = transformed[j].piApprox;
                        if (predicate(val, options.maxError)) {
                            if (exact || options.simplify === 'optional') {
                                score.correct = true;
                                score.message = options.message || null;
                                score.empty = false;
                            } else if (form === 'percent') {
                                score.empty = true;
                                score.message = $._('Your answer is almost correct, ' + 'but it is missing a ' + '<code>\\%</code> at the end.');
                            } else {
                                if (options.simplify !== 'enforced') {
                                    score.empty = true;
                                }
                                score.message = $._('Your answer is almost correct, ' + 'but it needs to be simplified.');
                            }
                            return false;
                        } else if (piApprox && predicate(val, Math.abs(val * 0.001))) {
                            score.empty = true;
                            score.message = $._('Your answer is close, but you may ' + 'have approximated pi. Enter your ' + 'answer as a multiple of pi, like ' + '<code>12\\ \\text{pi}</code> or ' + '<code>2/3\\ \\text{pi}</code>');
                        }
                    }
                });
                if (score.correct === false) {
                    var interpretedGuess = false;
                    _.each(forms, function (form) {
                        if (_.any(form(guess), function (t) {
                                return t.value != null && !_.isNaN(t.value);
                            })) {
                            interpretedGuess = true;
                        }
                    });
                    if (!interpretedGuess) {
                        score.empty = true;
                        score.message = $._('We could not understand your answer. ' + 'Please check your answer for extra text or symbols.');
                        return score;
                    }
                }
                return score;
            };
        }
    },
    number: {
        convertToPredicate: function (correct, options) {
            var correctFloat = parseFloat($.trim(correct));
            return [
                function (guess, maxError) {
                    return Math.abs(guess - correctFloat) < maxError;
                },
                $.extend({}, options, { type: 'predicate' })
            ];
        },
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var args = Khan.answerTypes.number.convertToPredicate(solutionText, solutionData);
            return Khan.answerTypes.predicate.setupFunctional(solutionarea, args[0], args[1]);
        },
        createValidatorFunctional: function (correct, options) {
            return Khan.answerTypes.predicate.createValidatorFunctional.apply(Khan.answerTypes.predicate, Khan.answerTypes.number.convertToPredicate(correct, options));
        }
    },
    decimal: numberAnswerType('decimal'),
    rational: numberAnswerType('integer, proper, improper, mixed'),
    improper: numberAnswerType('integer, proper, improper'),
    mixed: numberAnswerType('integer, proper, mixed'),
    regex: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var input;
            if (window.Modernizr && Modernizr.touchevents) {
                input = $('<input type="text" autocapitalize="off">');
            } else {
                input = $('<input type="text">');
            }
            $(solutionarea).append(input);
            return {
                validator: Khan.answerTypes.regex.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return input.val();
                },
                solution: $.trim(solutionText),
                showGuess: function (guess) {
                    input.val(guess === undefined ? '' : guess);
                }
            };
        },
        createValidatorFunctional: function (regex, options) {
            var flags = '';
            if (options.caseInsensitive != null) {
                flags += 'i';
            }
            regex = new RegExp($.trim(regex), flags);
            return function (guess) {
                var fallback = options.fallback != null ? '' + options.fallback : '';
                guess = $.trim(guess) || fallback;
                return {
                    empty: false,
                    correct: guess.match(regex) != null,
                    message: null,
                    guess: guess
                };
            };
        }
    },
    radical: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var options = $.extend({ simplify: 'required' }, solutionData);
            var inte = $('<input type="text" autocapitalize="off">');
            var rad = $('<input type="text" autocapitalize="off">');
            var examples = options.simplify === 'required' ? [$._('a simplified radical, like <code>\\sqrt{2}</code> ' + 'or <code>3\\sqrt{5}</code>')] : [$._('a radical, like <code>\\sqrt{8}</code> or ' + '<code>2\\sqrt{2}</code>')];
            addExamplesToInput(inte, examples);
            addExamplesToInput(rad, examples);
            $('<div class=\'radical\'>').append($('<span>').append(inte)).append('<span class="surd">&radic;</span>').append($('<span>').append(rad).addClass('overline')).appendTo(solutionarea);
            var ansSquared = parseFloat(solutionText);
            var ans = KhanUtil.splitRadical(ansSquared);
            return {
                validator: Khan.answerTypes.radical.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return [
                        $.trim(inte.val()),
                        $.trim(rad.val())
                    ];
                },
                solution: ans,
                showGuess: function (guess) {
                    inte.val(guess ? guess[0] : '');
                    rad.val(guess ? guess[1] : '');
                }
            };
        },
        createValidatorFunctional: function (ansSquared, options) {
            options = $.extend({ simplify: 'required' }, options);
            ansSquared = parseFloat(ansSquared);
            var ans = KhanUtil.splitRadical(ansSquared);
            return function (guess) {
                if (guess[0].length === 0 && guess[1].length === 0) {
                    return {
                        empty: true,
                        correct: false,
                        message: null,
                        guess: guess
                    };
                }
                guess[0] = guess[0].length > 0 ? guess[0] : '1';
                guess[1] = guess[1].length > 0 ? guess[1] : '1';
                var inteGuess = parseFloat(guess[0]);
                var radGuess = parseFloat(guess[1]);
                var correct = Math.abs(inteGuess) * inteGuess * radGuess === ansSquared;
                var simplified = inteGuess === ans[0] && radGuess === ans[1];
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                if (correct) {
                    if (simplified || options.simplify === 'optional') {
                        score.correct = true;
                    } else {
                        score.message = $._('Your answer is almost correct, but it ' + 'needs to be simplified.');
                    }
                }
                return score;
            };
        }
    },
    cuberoot: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var options = $.extend({ simplify: 'required' }, solutionData);
            var inte = $('<input type="text" autocapitalize="off">');
            var rad = $('<input type="text" autocapitalize="off">');
            var examples = options.simplify === 'required' ? [$._('a simplified radical, like <code>\\sqrt[3]{2}</code> ' + 'or <code>3\\sqrt[3]{5}</code>')] : [$._('a radical, like <code>\\sqrt[3]{8}</code> or ' + '<code>2\\sqrt[3]{2}</code>')];
            addExamplesToInput(inte, examples);
            addExamplesToInput(rad, examples);
            $('<div class=\'radical\'>').append($('<span>').append(inte)).append('<span class="surd" style="vertical-align: 6px;"><code>\\sqrt[3]{}</code></span>').append($('<span>').append(rad).addClass('overline')).appendTo(solutionarea).tex();
            var ansCubed = parseFloat(solutionText);
            var ans = KhanUtil.splitCube(ansCubed);
            return {
                validator: Khan.answerTypes.cuberoot.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return [
                        inte.val(),
                        rad.val()
                    ];
                },
                solution: ans,
                showGuess: function (guess) {
                    inte.val(guess ? guess[0] : '');
                    rad.val(guess ? guess[1] : '');
                }
            };
        },
        createValidatorFunctional: function (ansCubed, options) {
            options = $.extend({ simplify: 'required' }, options);
            ansCubed = parseFloat(ansCubed);
            var ans = KhanUtil.splitCube(ansCubed);
            return function (guess) {
                if (guess[0].length === 0 && guess[1].length === 0) {
                    return {
                        empty: true,
                        correct: false,
                        message: null,
                        guess: guess
                    };
                }
                guess[0] = guess[0].length > 0 ? guess[0] : '1';
                guess[1] = guess[1].length > 0 ? guess[1] : '1';
                var inteGuess = parseFloat(guess[0]);
                var radGuess = parseFloat(guess[1]);
                var correct = Math.abs(inteGuess) * inteGuess * inteGuess * radGuess === ansCubed;
                var simplified = inteGuess === ans[0] && radGuess === ans[1];
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                if (correct) {
                    if (simplified || options.simplify === 'optional') {
                        score.correct = true;
                    } else {
                        score.message = $._('Your answer is almost correct, but it ' + 'needs to be simplified.');
                    }
                }
                return score;
            };
        }
    },
    multiple: {
        setup: function (solutionarea, solution) {
            $(solutionarea).append($(solution).clone(true).texCleanup().contents().runModules());
            var answerDataArray = [];
            $(solutionarea).find('.sol').each(function (idx) {
                var type = $(this).data('type');
                type = type != null ? type : 'number';
                var sol = $(solution).find('.sol').eq(idx);
                var solarea = $(this).empty();
                var answerData = Khan.answerTypes[type].setup(solarea, sol);
                answerDataArray.push(answerData);
            });
            return {
                validator: Khan.answerTypes.multiple.createValidator(solution),
                answer: function () {
                    var answer = [];
                    $.each(answerDataArray, function (i, answerData) {
                        answer.push(answerData.answer());
                    });
                    return answer;
                },
                solution: function () {
                    $.map(answerDataArray, function (answerData) {
                        return answerData.solution;
                    });
                }(),
                showGuess: function (guess) {
                    $.each(answerDataArray, function (i, answerData) {
                        if (guess !== undefined) {
                            answerData.showGuess(guess[i]);
                        } else {
                            answerData.showGuess();
                        }
                    });
                },
                showCustomGuess: function (guess) {
                    $.each(answerDataArray, function (i, answerData) {
                        if (!_.isFunction(answerData.showCustomGuess)) {
                            return;
                        }
                        if (guess !== undefined) {
                            answerData.showCustomGuess(guess[i]);
                        } else {
                            answerData.showCustomGuess();
                        }
                    });
                }
            };
        },
        createValidator: function (solution) {
            var validators = [];
            $(solution).find('.sol').each(function () {
                var sol = $(this);
                var type = sol.data('type');
                type = type != null ? type : 'number';
                var validator = Khan.answerTypes[type].createValidator(sol);
                validators.push(validator);
            });
            return function (guess) {
                var score = {
                    empty: true,
                    correct: true,
                    message: null,
                    guess: guess
                };
                var blockGradingMessage = null;
                if (checkIfAnswerEmpty(guess)) {
                    score.empty = true;
                    score.correct = false;
                    return score;
                }
                $.each(guess, function (i, g) {
                    var pass = validators[i](g);
                    if (pass.message && pass.empty) {
                        blockGradingMessage = pass.message;
                    } else {
                        score.empty = score.empty && pass.empty;
                        score.correct = score.correct && pass.correct;
                        score.message = score.message || pass.message;
                    }
                });
                if (score.correct && blockGradingMessage != null) {
                    return {
                        empty: true,
                        correct: false,
                        message: blockGradingMessage,
                        guess: guess
                    };
                } else {
                    score.empty = false;
                    return score;
                }
            };
        }
    },
    set: {
        setup: function (solutionarea, solution) {
            $(solutionarea).append($(solution).find('.input-format').clone(true).texCleanup().contents().runModules());
            var inputArray = [];
            var showGuessArray = [];
            $(solutionarea).find('.entry').each(function () {
                var input = $(this), type = $(this).data('type');
                type = type != null ? type : 'number';
                var sol = input.clone(true), solarea = input.empty();
                var validator = Khan.answerTypes[type].setup(solarea, sol);
                inputArray.push(validator.answer);
                showGuessArray.push(validator.showGuess);
            });
            var solutionArray = [];
            $(solution).find('.set-sol').clone(true).each(function () {
                var type = $(this).data('type');
                type = type != null ? type : 'number';
                var solarea = $('<div>');
                var validator = Khan.answerTypes[type].setup(solarea, $(this));
                solutionArray.push(validator.solution);
            });
            return {
                validator: Khan.answerTypes.set.createValidator(solution),
                answer: function () {
                    var answer = [];
                    $.each(inputArray, function (i, getAns) {
                        answer.push(getAns());
                    });
                    return answer;
                },
                solution: solution,
                showGuess: function (guess) {
                    $.each(showGuessArray, function (i, showGuess) {
                        if (guess === undefined) {
                            showGuess();
                        } else {
                            showGuess(guess[i]);
                        }
                    });
                }
            };
        },
        createValidator: function (solution) {
            var validatorArray = [];
            $(solution).find('.set-sol').clone(true).each(function () {
                var type = $(this).data('type');
                type = type != null ? type : 'number';
                var validator = Khan.answerTypes[type].createValidator($(this));
                validatorArray.push(validator);
            });
            return function (guess) {
                var score = {
                    empty: validatorArray.length === 0 ? false : true,
                    correct: true,
                    message: null,
                    guess: guess
                };
                var blockGradingMessage = null;
                var unusedValidators = validatorArray.slice(0);
                $.each(guess, function (i, g) {
                    var correct = false;
                    $.each(unusedValidators, function (i, validator) {
                        var pass = validator(g);
                        if (pass.empty && pass.message) {
                            unusedValidators.splice(i, 1);
                            blockGradingMessage = pass.message;
                            correct = true;
                            return false;
                        }
                        if (pass.correct) {
                            correct = pass.correct;
                            unusedValidators.splice(i, 1);
                            return false;
                        }
                        if (!pass.correct && pass.message) {
                            correct = pass.message;
                        }
                    });
                    if (!checkIfAnswerEmpty(g) && !checkIfAnswerEmpty(correct)) {
                        score.empty = false;
                    }
                    if (!correct && $.trim([g].join('')) !== '') {
                        score.correct = false;
                        return false;
                    }
                    if (typeof correct === 'string') {
                        score.message = correct;
                        score.correct = false;
                    }
                });
                if (validatorArray.length > guess.length) {
                    if (unusedValidators.length > validatorArray.length - guess.length) {
                        score.correct = false;
                    }
                } else if (unusedValidators.length > 0) {
                    score.correct = false;
                }
                if (score.correct && blockGradingMessage != null) {
                    return {
                        empty: true,
                        correct: false,
                        message: blockGradingMessage,
                        guess: guess
                    };
                } else {
                    return score;
                }
            };
        }
    },
    radio: {
        setup: function (solutionarea, solution) {
            var $list = $('<ul></ul>');
            $(solutionarea).append($list);
            var $choices = $(solution).siblings('.choices');
            var $choicesClone = $choices.clone(true).texCleanup();
            var $solutionClone = $(solution).clone(true).texCleanup();
            var solutionText = $solutionClone.text();
            var isCategory = !!$choices.data('category');
            var possibleChoices;
            if (isCategory) {
                var correctText = getTextSquish($solutionClone);
                possibleChoices = _.map($choicesClone.children().get(), function (elem) {
                    if (getTextSquish(elem) === correctText) {
                        return $solutionClone[0];
                    } else {
                        return elem;
                    }
                });
            } else {
                possibleChoices = $solutionClone.get().concat(KhanUtil.shuffle($choicesClone.children().get()));
            }
            var numChoices = +$choices.data('show') || possibleChoices.length;
            var showNone = !!$choices.data('none');
            var shownChoices = _.uniq(possibleChoices, false, function (elem) {
                return getTextSquish(elem);
            });
            var addNoneChoice = showNone && shownChoices.length === numChoices - 1;
            if (shownChoices.length < numChoices && !addNoneChoice) {
                return false;
            } else if (shownChoices.length > numChoices) {
                shownChoices = shownChoices.slice(0, numChoices);
            }
            if (!isCategory) {
                shownChoices = KhanUtil.shuffle(shownChoices);
            }
            var correctIndex;
            _.each(shownChoices, function (choice, i) {
                if (choice === $solutionClone[0]) {
                    correctIndex = i;
                }
            });
            var noneIsCorrect = showNone && correctIndex === numChoices - 1;
            if (showNone) {
                var $none = $('<span>').html($._('None of the above'));
                $none.data('noneOfTheAbove', true);
                if (noneIsCorrect) {
                    $list.data('realAnswer', $('<span>').addClass('value').append($solutionClone.clone(true).contents()));
                }
                var noneIndex = shownChoices.length - 1;
                if (addNoneChoice) {
                    noneIndex = shownChoices.length;
                }
                shownChoices.splice(noneIndex, 1, $('<span>').append($none));
            }
            var wrappedChoices = _.map(shownChoices, function (choice, i) {
                return $('<li><label></label></li>').find('label').append([
                    $('<input type="radio" name="solution">').val(i),
                    $('<span class="value"></span>').append($(choice).contents())
                ]).end();
            });
            $list.append(wrappedChoices).runModules();
            return {
                validator: Khan.answerTypes.radio.createValidator({
                    solution: solution,
                    index: correctIndex,
                    noneIsCorrect: noneIsCorrect
                }),
                answer: function () {
                    var $choice = $list.find('input:checked');
                    if ($choice.length === 0) {
                        return null;
                    }
                    var $choiceVal = $choice.siblings('.value');
                    var $choiceNoneChild = $choiceVal.children().eq(0);
                    return {
                        isNone: $choiceNoneChild.data('noneOfTheAbove'),
                        value: extractRawCode($choiceVal),
                        index: +$choice.val()
                    };
                },
                solution: solutionText,
                showGuess: function (guess) {
                    if (guess == null) {
                        $(solutionarea).find('input:checked').attr('checked', false);
                    } else {
                        $list.children().filter(function () {
                            return guess.index === $(this).find('input').val();
                        }).find('input').attr('checked', true);
                    }
                }
            };
        },
        createValidator: function (solution) {
            var correct = extractRawCode(solution.solution || solution);
            function showReal() {
                var $list = $('#solutionarea').find('ul');
                var $choice = $list.children().filter(function () {
                    return $(this).find('span.value > span').data('noneOfTheAbove');
                }).find('input');
                $choice.next().fadeOut('fast', function () {
                    var $real = $list.data('realAnswer');
                    $(this).replaceWith($real);
                    $real.tex().fadeIn('fast');
                });
            }
            return function (guess) {
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                if (guess == null) {
                    score.empty = true;
                    return score;
                }
                if (guess.index) {
                    if (guess.isNone && solution.noneIsCorrect) {
                        showReal();
                        score.correct = true;
                    } else {
                        score.correct = guess.index === solution.index;
                    }
                } else {
                    if (guess.isNone && $('#solutionarea').find('ul').data('real-answer') != null) {
                        showReal();
                        score.correct = true;
                    } else if ($.trim(guess.value).replace(/\r\n?|\n/g, '') === $.trim(correct.replace(/\r\n?|\n/g, ''))) {
                        score.correct = true;
                    } else {
                        score.correct = false;
                    }
                }
                return score;
            };
        }
    },
    list: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var input = $('<select></select>');
            $(solutionarea).append(input);
            var choices = $.tmpl.getVAR(solutionData.choices);
            $.each(choices, function (index, value) {
                input.append('<option value="' + value + '">' + value + '</option>');
            });
            return {
                validator: Khan.answerTypes.list.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return input.val();
                },
                solution: $.trim(solutionText),
                showGuess: function (guess) {
                    input.val(guess === undefined ? '' : guess);
                }
            };
        },
        createValidatorFunctional: function (correct, options) {
            correct = $.trim(correct);
            return function (guess) {
                guess = $.trim(guess);
                return {
                    empty: false,
                    correct: correct === guess,
                    message: null,
                    guess: guess
                };
            };
        }
    },
    custom: {
        setup: function (solutionarea, solution) {
            solution.find('.instruction').appendTo(solutionarea).runModules();
            var guessCode = solution.find('.guess').text();
            var showCustomGuessCode = solution.find('.show-guess').text();
            var showGuessCode = solution.find('.show-guess-solutionarea').text();
            return {
                validator: Khan.answerTypes.custom.createValidator(solution),
                answer: function () {
                    return KhanUtil.tmpl.getVAR(guessCode, KhanUtil.currentGraph);
                },
                solution: $.trim($(solution).text()),
                showCustomGuess: function (guess) {
                    var code = '(function() { ' + 'var guess = ' + JSON.stringify(guess) + ';' + showCustomGuessCode + '})()';
                    KhanUtil.tmpl.getVAR(code, KhanUtil.currentGraph);
                },
                showGuess: function (guess) {
                    var code = '(function() { ' + 'var guess = ' + JSON.stringify(guess) + ';' + showGuessCode + '})()';
                    KhanUtil.tmpl.getVAR(code, KhanUtil.currentGraph);
                }
            };
        },
        createValidator: function (solution) {
            var validatorCode = $(solution).find('.validator-function').text();
            var validator = function (guess) {
                var code = '(function() { ' + 'var guess = ' + JSON.stringify(guess) + ';' + validatorCode + '})()';
                return KhanUtil.tmpl.getVAR(code, KhanUtil.currentGraph);
            };
            return function (guess) {
                var pass = validator(guess);
                if (typeof pass === 'object') {
                    return pass;
                } else {
                    return {
                        empty: pass === '',
                        correct: pass === true,
                        message: typeof pass === 'string' ? pass : null,
                        guess: guess
                    };
                }
            };
        }
    },
    primeFactorization: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var $input;
            if (window.Modernizr && Modernizr.touchevents) {
                $input = $('<input type="text" autocapitalize="off">');
            } else {
                $input = $('<input type="text">');
            }
            $input.addClass('prime-factorization');
            $(solutionarea).append($input);
            var examples = [
                $._('a product of prime factors, like <code>2 \\times 3</code>'),
                $._('a single prime number, like <code>5</code>')
            ];
            addExamplesToInput($input, examples);
            return {
                validator: Khan.answerTypes.primeFactorization.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return $input.val();
                },
                solution: $.trim(solutionText),
                showGuess: function (guess) {
                    $input.val(guess === undefined ? '' : guess);
                }
            };
        },
        createValidatorFunctional: function (correct, options) {
            correct = $.trim(correct);
            return function (guess) {
                guess = guess.split(' ').join('').toLowerCase();
                guess = guess.replace(/{|}/g, '');
                guess = guess.split(/x|\*|\u00d7|\\times|\\cdot/);
                var terms = [];
                for (var i = 0; i < guess.length; i++) {
                    var t = guess[i].split('^');
                    if (t.length > 1) {
                        for (var j = 0; j < t[1]; j++) {
                            terms.push(t[0]);
                        }
                    } else {
                        terms.push(guess[i]);
                    }
                }
                guess = KhanUtil.sortNumbers(terms).join('x');
                return {
                    empty: guess === '',
                    correct: guess === correct,
                    message: null,
                    guess: guess
                };
            };
        }
    },
    checkbox: {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            var input = $('<input type="checkbox">');
            $(solutionarea).append(input);
            return {
                validator: Khan.answerTypes.checkbox.createValidatorFunctional(solutionText, solutionData),
                answer: function () {
                    return input.is(':checked') || '';
                },
                solution: $.trim(solutionText),
                showGuess: function (guess) {
                    input.attr('checked', guess === undefined ? false : guess);
                }
            };
        },
        createValidatorFunctional: function (correct, options) {
            correct = $.trim(correct) === 'true';
            return function (guess) {
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                if (!!correct === !!guess) {
                    score.correct = true;
                } else if (!guess) {
                    score.empty = true;
                } else {
                    score.correct = false;
                }
                return score;
            };
        }
    },
    expression: {
        setup: function (solutionarea, solution) {
            var options = this._parseOptions($(solution).data());
            var $tex = $('<span class="tex"/>');
            var $input = $('<input type="text">');
            var $error = $('<div class="error-div" style="display: none;"/>');
            $(solutionarea).append($('<span class="expression"/>').append($('<span class="output"/>').append($tex), $('<span class="input"/>').append($input, $error.append($('<i class="icon-exclamation-sign error-icon"/>')))));
            var errorTimeout = null;
            var lastParsedTex = '';
            var update = function () {
                clearTimeout(errorTimeout);
                var result = KAS.parse($input.val(), options);
                if (result.parsed) {
                    hideError();
                    $tex.css({ opacity: 1 });
                    var tex = result.expr.asTex(options);
                    if (tex !== lastParsedTex) {
                        $tex.empty().append($('<code>').text(tex)).tex();
                        lastParsedTex = tex;
                    }
                } else {
                    errorTimeout = setTimeout(showError, 2000);
                    $tex.css({ opacity: 0.5 });
                }
            };
            var showError = function () {
                if (!$error.is(':visible')) {
                    $error.show();
                    $input.addClass('error');
                }
            };
            var hideError = function () {
                if ($error.is(':visible')) {
                    $error.hide();
                    $input.removeClass('error');
                }
            };
            $input.on('input propertychange', update);
            $input.on('keydown', function (event) {
                var input = $input[0];
                var start = input.selectionStart;
                var end = input.selectionEnd;
                var supported = start !== undefined;
                if (supported && event.which === 8) {
                    var val = input.value;
                    if (start === end && val.slice(start - 1, start + 1) === '()') {
                        event.preventDefault();
                        input.value = val.slice(0, start - 1) + val.slice(start + 1);
                        input.selectionStart = start - 1;
                        input.selectionEnd = end - 1;
                        update();
                    }
                }
            });
            $input.on('keypress', function (event) {
                var input = $input[0];
                var start = input.selectionStart;
                var end = input.selectionEnd;
                var supported = start !== undefined;
                if (supported && event.which === 40) {
                    var val = input.value;
                    event.preventDefault();
                    if (start === end) {
                        var insertMatched = _.any([
                            ' ',
                            ')',
                            ''
                        ], function (c) {
                            return val.charAt(start) === c;
                        });
                        input.value = val.slice(0, start) + (insertMatched ? '()' : '(') + val.slice(end);
                    } else {
                        input.value = val.slice(0, start) + '(' + val.slice(start, end) + ')' + val.slice(end);
                    }
                    input.selectionStart = start + 1;
                    input.selectionEnd = end + 1;
                    update();
                } else if (supported && event.which === 41) {
                    var val = input.value;
                    if (start === end && val.charAt(start) === ')') {
                        event.preventDefault();
                        input.selectionStart = start + 1;
                        input.selectionEnd = end + 1;
                        update();
                    }
                }
            });
            var explicitMul = $._('For <code>2\\cdot2</code>, enter <strong>2*2</strong>');
            if (options.times) {
                explicitMul = explicitMul.replace(/\\cdot/g, '\\times');
            }
            var examples = [
                explicitMul,
                $._('For <code>3y</code>, enter <strong>3y</strong> or <strong>3*y</strong>'),
                $._('For <code>\\dfrac{1}{x}</code>, enter <strong>1/x</strong>'),
                $._('For <code>x^{y}</code>, enter <strong>x^y</strong>'),
                $._('For <code>\\sqrt{x}</code>, enter <strong>sqrt(x)</strong>'),
                $._('For <code>\\pi</code>, enter <strong>pi</strong>'),
                $._('For <code>\\sin \\theta</code>, enter <strong>sin(theta)</strong>'),
                $._('For <code>\\le</code> or <code>\\ge</code>, enter <strong><=</strong> or <strong>>=</strong>'),
                $._('For <code>\\neq</code>, enter <strong>=/=</strong>')
            ];
            addExamplesToInput($input, examples);
            return {
                validator: Khan.answerTypes.expression.createValidator(solution),
                answer: function () {
                    return $input.val();
                },
                solution: solution,
                showGuess: function (guess) {
                    $input.val(guess === undefined ? '' : guess);
                }
            };
        },
        parseSolution: function (solutionString, options) {
            var solution = KAS.parse(solutionString, options);
            if (!solution.parsed) {
                throw new Error('The provided solution (' + solutionString + ') didn\'t parse.');
            } else if (options.simplified && !solution.expr.isSimplified()) {
                throw new Error('The provided solution (' + solutionString + ') isn\'t fully expanded and simplified.');
            } else {
                solution = solution.expr;
            }
            return solution;
        },
        _parseOptions: function (solutionData) {
            var form = solutionData.form !== undefined ? solutionData.form : solutionData.sameForm;
            var notFalseOrNil = function (x) {
                return x != null && x !== false;
            };
            var options = {
                form: notFalseOrNil(form),
                simplify: notFalseOrNil(solutionData.simplify),
                times: notFalseOrNil(solutionData.times)
            };
            if (_.isString(solutionData.functions)) {
                options.functions = _.compact(solutionData.functions.split(/[ ,]+/));
            } else if (_.isArray(solutionData.functions)) {
                options.functions = _.compact(solutionData.functions);
            }
            return options;
        },
        createValidator: function (solution) {
            var $solution = $(solution);
            var validatorArray = [];
            var createValidatorFunctional = this.createValidatorFunctional;
            var parseOptions = this._parseOptions;
            $(solution).find('.set-sol').each(function () {
                var options = parseOptions($(this).data());
                validatorArray.push(createValidatorFunctional($(this).text(), options));
            });
            if (validatorArray.length === 0) {
                var options = parseOptions($solution.data());
                validatorArray.push(createValidatorFunctional($solution.text(), options));
            }
            return function (guess) {
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                $.each(validatorArray, function (i, validator) {
                    var result = validator(guess);
                    if (result.correct) {
                        score.correct = true;
                        score.message = null;
                        return false;
                    }
                    if (result.message) {
                        score.message = result.message;
                    }
                    if (result.empty) {
                        score.empty = true;
                    }
                });
                return score;
            };
        },
        createValidatorFunctional: function (solution, options) {
            return function (guess) {
                var score = {
                    empty: false,
                    correct: false,
                    message: null,
                    guess: guess
                };
                if (!guess) {
                    score.empty = true;
                    return score;
                }
                var answer = KAS.parse(guess, options);
                if (!answer.parsed) {
                    score.empty = true;
                    return score;
                }
                if (typeof solution === 'string') {
                    solution = Khan.answerTypes.expression.parseSolution(solution, options);
                }
                var result = KAS.compare(answer.expr, solution, options);
                if (result.equal) {
                    score.correct = true;
                } else if (result.message) {
                    score.message = result.message;
                } else {
                    var answerX = KAS.parse(guess.replace(/[xX]/g, '*'), options);
                    if (answerX.parsed) {
                        var resultX = KAS.compare(answerX.expr, solution, options);
                        if (resultX.equal) {
                            score.empty = true;
                            score.message = 'I\'m a computer. I only ' + 'understand multiplication if you use an ' + 'asterisk (*) as the multiplication sign.';
                        } else if (resultX.message) {
                            score.message = resultX.message + ' Also, ' + 'I\'m a computer. I only ' + 'understand multiplication if you use an ' + 'asterisk (*) as the multiplication sign.';
                        }
                    }
                }
                return score;
            };
        }
    }
});
function numberAnswerType(forms) {
    return {
        setupFunctional: function (solutionarea, solutionText, solutionData) {
            return Khan.answerTypes.number.setupFunctional(solutionarea, solutionText, $.extend({}, solutionData, { forms: forms }));
        },
        createValidatorFunctional: function (correct, options) {
            return Khan.answerTypes.number.createValidatorFunctional(correct, $.extend({}, options, { forms: forms }));
        }
    };
}
_.each(Khan.answerTypes, function (info, type) {
    if (!('setup' in info)) {
        info.setup = function (solutionarea, solution) {
            var $solution = $(solution);
            return info.setupFunctional(solutionarea, $solution.text(), $solution.data());
        };
    }
    if (!('createValidator' in info)) {
        info.createValidator = function (solution) {
            var $solution = $(solution);
            return info.createValidatorFunctional($solution.text(), $solution.data());
        };
    }
});
},{}]},{},[1]);
