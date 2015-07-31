(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
function findChildOrAdd(elem, className) {
    var $child = $(elem).find('.' + className);
    if ($child.length === 0) {
        return $('<span>').addClass(className).appendTo($(elem));
    } else {
        return $child;
    }
}
function doCallback(elem, callback) {
    var tries = 0;
    (function check() {
        var height = elem.scrollHeight;
        if (height > 18 || tries >= 10) {
            callback();
        } else {
            tries++;
            setTimeout(check, 100);
        }
    }());
}
$.extend(KhanUtil, {
    processMath: function (elem, text, force, callback) {
        var $elem = $(elem);
        if ($elem.attr('data-math-formula') == null || force) {
            var $katexHolder = findChildOrAdd($elem, 'katex-holder');
            var $mathjaxHolder = findChildOrAdd($elem, 'mathjax-holder');
            var script = $mathjaxHolder.find('script[type=\'math/tex\']')[0];
            if (text == null) {
                if ($elem.attr('data-math-formula')) {
                    text = $elem.attr('data-math-formula');
                } else if (script) {
                    text = script.text || script.textContent;
                }
            }
            text = text != null ? text + '' : '';
            if (KhanUtil.cleanMath) {
                text = KhanUtil.cleanMath(text);
            }
            $elem.attr('data-math-formula', text);
            if (Exercises.useKatex) {
                try {
                    katex.render(text, $katexHolder[0]);
                    if ($elem.attr('data-math-type') === 'mathjax') {
                        var jax = MathJax.Hub.getJaxFor(script);
                        if (jax) {
                            var e = jax.SourceElement();
                            if (e.previousSibling && e.previousSibling.className) {
                                jax.Remove();
                            }
                        }
                    }
                    $elem.attr('data-math-type', 'katex');
                    if (callback) {
                        doCallback(elem, callback);
                    }
                    return;
                } catch (err) {
                    if (err.__proto__ !== katex.ParseError.prototype) {
                        throw err;
                    }
                }
            }
            $elem.attr('data-math-type', 'mathjax');
            if (!script) {
                $mathjaxHolder.append('<script type=\'math/tex\'>' + text.replace(/<\//g, '< /') + '</script>');
            } else {
                if ('text' in script) {
                    script.text = text;
                } else {
                    script.textContent = text;
                }
            }
            if (typeof MathJax !== 'undefined') {
                MathJax.Hub.Queue([
                    'Reprocess',
                    MathJax.Hub,
                    $mathjaxHolder[0]
                ]);
                MathJax.Hub.Queue(function () {
                    KhanUtil.debugLog('MathJax done typesetting (' + text + ')');
                });
                if (callback) {
                    MathJax.Hub.Queue(function () {
                        var cb = MathJax.Callback(function () {
                        });
                        doCallback(elem, function () {
                            callback();
                            cb();
                        });
                        return cb;
                    });
                }
            }
        }
    },
    processAllMath: function (elem, force) {
        var $elem = $(elem);
        $elem.filter('code').add($elem.find('code')).each(function () {
            var $this = $(this);
            var text = $this.attr('data-math-formula');
            if (text == null) {
                text = $this.text();
                $this.empty();
            }
            KhanUtil.processMath(this, text, force);
        });
    },
    cleanupMath: function (elem) {
        var $elem = $(elem);
        if ($elem.attr('data-math-formula')) {
            if (typeof MathJax !== 'undefined') {
                var jax = MathJax.Hub.getJaxFor($elem.find('script')[0]);
                if (jax) {
                    var e = jax.SourceElement();
                    if (e.previousSibling && e.previousSibling.className) {
                        jax.Remove();
                    }
                }
            }
            $elem.text($elem.attr('data-math-formula'));
            $elem.attr('data-math-formula', null);
            $elem.attr('data-math-type', null);
        }
        return elem;
    },
    retrieveMathFormula: function (elem) {
        return $(elem).attr('data-math-formula');
    }
});
$.fn.tex = function () {
    KhanUtil.processAllMath(this, false);
    return this;
};
$.fn.texCleanup = function () {
    this.filter('code').add(this.find('code')).each(function () {
        KhanUtil.cleanupMath(this);
    });
    return this;
};
},{}]},{},[1]);
