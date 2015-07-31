(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
require('../third_party/jquery.cursor-position.js');
$.extend(KhanUtil, {
    matrixInput: {
        eventsAttached: false,
        eventNamespace: 'matrix-input',
        containerEl: null,
        bracketEls: null,
        cells: null,
        LEFT_ARROW: 37,
        UP_ARROW: 38,
        RIGHT_ARROW: 39,
        DOWN_ARROW: 40,
        ENTER_KEY: 13,
        ROWS: 3,
        COLS: 3,
        maxRow: 0,
        maxCol: 0,
        contentMaxRow: 0,
        contentMaxCol: 0,
        init: function () {
            var self = this;
            this.initContainer();
            var inputs = $('.matrix-row .sol input[type=\'text\']');
            this.cells = _.map(inputs, function (input, i) {
                return {
                    el: input,
                    index: i,
                    row: self.indexToRow(i),
                    col: self.indexToCol(i),
                    val: function () {
                        return $.trim($(this.el).val());
                    },
                    clearVal: function () {
                        $(this.el).val('');
                    }
                };
            });
            this.addBrackets();
            this.bindInputEvents();
            this.resetAllMaxVals();
            this.render();
        },
        initContainer: function () {
            this.containerEl = $('#solutionarea .matrix-input');
            if (!this.containerEl[0]) {
                this.containerEl = $('#solutionarea').addClass('matrix-input');
            }
        },
        addBrackets: function (i) {
            var left = $('<div>').addClass('matrix-bracket bracket-left');
            var right = $('<div>').addClass('matrix-bracket bracket-right');
            this.containerEl.prepend(left, right);
            this.bracketEls = [
                left,
                right
            ];
        },
        removeBrackets: function () {
            _.each(this.bracketEls, function (bracketEl) {
                $(bracketEl).remove();
            });
        },
        indexToRow: function (i) {
            return Math.floor(i / this.COLS);
        },
        indexToCol: function (i) {
            return i % this.COLS;
        },
        coordToIndex: function (row, col) {
            return this.COLS * row + col;
        },
        bindInputEvents: function () {
            var self = this;
            var clickedInput = false;
            $('body').on('click.' + self.eventNamespace, function () {
                if (!clickedInput) {
                    self.resetMaxToContentMax();
                    self.render();
                }
                clickedInput = false;
            });
            _.each(this.cells, function (cell) {
                $(cell.el).on({
                    focus: function (e) {
                        self.setMaxVals(cell);
                        self.render();
                    },
                    blur: function (e) {
                        self.setMaxVals(cell);
                    },
                    click: function (e) {
                        clickedInput = true;
                    },
                    keydown: function (e) {
                        var LAST_ROW = self.ROWS - 1;
                        var LAST_INDEX = self.cells.length - 1;
                        var nextIndex = null;
                        var nextRow;
                        if (e.which === self.LEFT_ARROW) {
                            if (cell.index === 0 || !$(this).isCursorFirst()) {
                                return;
                            }
                            nextIndex = cell.index - 1;
                        } else if (e.which === self.RIGHT_ARROW) {
                            if (cell.index === LAST_INDEX || !$(this).isCursorLast()) {
                                return;
                            }
                            nextIndex = cell.index + 1;
                        } else if (e.which === self.UP_ARROW) {
                            if (cell.row === 0) {
                                return;
                            }
                            nextRow = cell.row - 1;
                            nextIndex = self.coordToIndex(nextRow, cell.col);
                        } else if (e.which === self.DOWN_ARROW) {
                            if (cell.row === LAST_ROW) {
                                return;
                            }
                            nextRow = cell.row + 1;
                            nextIndex = self.coordToIndex(nextRow, cell.col);
                        } else if (e.which === self.ENTER_KEY) {
                            self.setMaxVals(cell);
                        }
                        if (nextIndex === null) {
                            return;
                        }
                        $(self.cells[nextIndex].el).focus();
                        e.preventDefault();
                    }
                });
            });
        },
        setContentMaxRow: function (val) {
            this.contentMaxRow = Math.max(val, this.contentMaxRow);
        },
        setContentMaxCol: function (val) {
            this.contentMaxCol = Math.max(val, this.contentMaxCol);
        },
        setMaxRow: function (val) {
            this.maxRow = Math.max(val, this.contentMaxRow);
        },
        setMaxCol: function (val) {
            this.maxCol = Math.max(val, this.contentMaxCol);
        },
        resetMaxToContentMax: function () {
            this.maxRow = this.contentMaxRow;
            this.maxCol = this.contentMaxCol;
        },
        resetAllMaxVals: function () {
            this.maxRow = 0;
            this.maxCol = 0;
            this.contentMaxRow = 0;
            this.contentMaxCol = 0;
        },
        setMaxValsFromScratch: function () {
            this.resetAllMaxVals();
            var self = this;
            _.each(this.cells, function (cell) {
                if (cell.val()) {
                    self.setContentMaxRow(cell.row);
                    self.setContentMaxCol(cell.col);
                }
            });
            this.resetMaxToContentMax();
        },
        setMaxVals: function (cell) {
            var val = cell.val();
            if (val) {
                this.setContentMaxRow(cell.row);
                this.setContentMaxCol(cell.col);
            } else {
                cell.clearVal();
                if (this.contentMaxRow === cell.row || this.contentMaxCol === cell.col) {
                    this.setMaxValsFromScratch();
                }
            }
            this.setMaxRow(cell.row);
            this.setMaxCol(cell.col);
        },
        positionBrackets: function () {
            var cell = $(this.cells[0].el);
            var bracketWidth = this.bracketEls[0].width();
            var rows = this.maxRow + 1;
            var cols = this.maxCol + 1;
            var height = cell.outerHeight(true) * rows;
            var marginLeft = cell.outerWidth(true) * cols - bracketWidth;
            _.each(this.bracketEls, function ($el) {
                $el.css({ 'height': height });
            });
            this.bracketEls[1].css({ 'margin-left': marginLeft });
        },
        render: function () {
            this.positionBrackets();
        },
        cleanup: function () {
            $('body').off('.' + this.eventNamespace);
            this.removeBrackets();
        }
    }
});
$.fn['matrix-inputLoad'] = function () {
    if (KhanUtil.matrixInput.eventsAttached) {
        return;
    }
    $(Exercises).on('newProblem.matrix-input', function () {
        KhanUtil.matrixInput.init();
    });
    $(Khan).on('showGuess.matrix-input', function () {
        KhanUtil.matrixInput.setMaxValsFromScratch();
        KhanUtil.matrixInput.render();
    });
    KhanUtil.matrixInput.eventsAttached = true;
};
$.fn['matrix-inputCleanup'] = function () {
    if (!KhanUtil.matrixInput.eventsAttached) {
        return;
    }
    KhanUtil.matrixInput.cleanup();
    $(Exercises).off('newProblem.matrix-input');
    $(Khan).off('showGuess.matrix-input');
    KhanUtil.matrixInput.eventsAttached = false;
};
},{"../third_party/jquery.cursor-position.js":2}],2:[function(require,module,exports){
(function ($) {
    // from http://stackoverflow.com/questions/1891444/how-can-i-get-cursor-position-in-a-textarea?rq=1
    $.fn.getCursorPosition = function() {
        var el = $(this).get(0);
        var pos = 0;
        if ("selectionStart" in el) {
            pos = el.selectionStart;
        } else if ("selection" in document) {
            el.focus();
            var sel = document.selection.createRange();
            var selLength = document.selection.createRange().text.length;
            sel.moveStart("character", -el.value.length);
            pos = sel.text.length - selLength;
        }
        return pos;
    };

    $.fn.isCursorFirst = function() {
        var pos = $(this).getCursorPosition();
        return pos === 0;
    };

    $.fn.isCursorLast = function() {
        var pos = $(this).getCursorPosition();
        var last = $(this).val().length;
        return pos === last;
    };
})(jQuery);

},{}]},{},[1]);
