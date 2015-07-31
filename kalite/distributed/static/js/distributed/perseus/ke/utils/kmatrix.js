(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    expr: function (expr, compute) {
        if (typeof expr === 'object') {
            var op = expr[0], args = expr.slice(1), table = compute ? KhanUtil.computeOperators : KhanUtil.formatOperators;
            return table[op].apply(this, args);
        } else {
            return compute ? expr : expr.toString();
        }
    },
    exprType: function (expr) {
        if (typeof expr === 'object') {
            if (expr[0] === 'color') {
                return KhanUtil.exprType(expr[2]);
            }
            return expr[0];
        } else {
            return typeof expr;
        }
    },
    exprIsNegated: function (expr) {
        switch (KhanUtil.exprType(expr)) {
        case 'color':
            return KhanUtil.exprIsNegated(expr[2]);
        case '/':
            return KhanUtil.exprIsNegated(expr[1]);
        case '+':
        case '-':
            return true;
        case 'number':
            return expr < 0;
        case 'string':
            return expr.charAt(0) === '-';
        default:
            return false;
        }
    },
    exprIsShort: function (expr) {
        switch (KhanUtil.exprType(expr)) {
        case 'color':
            return KhanUtil.exprIsShort(expr[2]);
        case '+':
        case '-':
        case '*':
        case '/':
        case 'frac':
            return false;
        case '^':
            return KhanUtil.exprType(expr[1]) !== 'number' || expr[1] < 0;
        case 'number':
        case 'sqrt':
            return true;
        default:
            return expr.length <= 1;
        }
    },
    exprParenthesize: function (expr) {
        return KhanUtil.exprIsShort(expr) ? KhanUtil.expr(expr) : '(' + KhanUtil.expr(expr) + ')';
    },
    formatOperators: {
        'color': function (color, arg) {
            return '\\color{' + color + '}{' + KhanUtil.expr(arg) + '}';
        },
        '+': function () {
            var args = [].slice.call(arguments, 0);
            var terms = $.grep(args, function (term, i) {
                return term != null;
            });
            terms = _.filter(terms, function (term) {
                return '' + KhanUtil.expr(term) !== '0';
            });
            terms = $.map(terms, function (term, i) {
                var parenthesize;
                switch (KhanUtil.exprType(term)) {
                case '+':
                    parenthesize = true;
                    break;
                case '-':
                    parenthesize = term.length > 2;
                    break;
                default:
                    parenthesize = false;
                }
                term = KhanUtil.expr(term);
                if (parenthesize) {
                    term = '(' + term + ')';
                }
                if (term.charAt(0) !== '-' || parenthesize) {
                    term = '+' + term;
                }
                return term;
            });
            var joined = terms.join('');
            if (joined.charAt(0) === '+') {
                return joined.slice(1);
            } else {
                return joined;
            }
        },
        '-': function () {
            if (arguments.length === 1) {
                return KhanUtil.expr([
                    '*',
                    -1,
                    arguments[0]
                ]);
            } else {
                var args = [].slice.call(arguments, 0);
                var terms = $.map(args, function (term, i) {
                    var negate = KhanUtil.exprIsNegated(term);
                    var parenthesize;
                    switch (KhanUtil.exprType(term)) {
                    case '+':
                    case '-':
                        parenthesize = true;
                        break;
                    default:
                        parenthesize = false;
                    }
                    term = KhanUtil.expr(term);
                    if (negate && i > 0 || parenthesize) {
                        term = '(' + term + ')';
                    }
                    return term;
                });
                var joined = terms.join('-');
                return joined;
            }
        },
        '*': function () {
            var rest = Array.prototype.slice.call(arguments, 1);
            rest.unshift('*');
            if (arguments[0] === 0) {
                return 0;
            } else if (arguments[0] === 1 && rest.length > 1) {
                return KhanUtil.expr(rest);
            } else if (arguments[0] === -1 && rest.length > 1) {
                var form = KhanUtil.expr(rest);
                if (KhanUtil.exprIsNegated(rest[1])) {
                    return '-(' + form + ')';
                } else {
                    return '-' + form;
                }
            }
            if (arguments.length > 1) {
                var args = [].slice.call(arguments, 0);
                var parenthesizeRest = KhanUtil.exprType(arguments[0]) === 'number' && KhanUtil.exprType(arguments[1]) === 'number';
                var factors = $.map(args, function (factor, i) {
                    var parenthesize;
                    switch (KhanUtil.exprType(factor)) {
                    case 'number':
                        if (i > 0) {
                            parenthesize = true;
                        }
                        break;
                    default:
                        parenthesize = !KhanUtil.exprIsShort(factor);
                        break;
                    }
                    parenthesizeRest = parenthesizeRest || parenthesize;
                    factor = KhanUtil.expr(factor);
                    if (parenthesizeRest) {
                        factor = '(' + factor + ')';
                    }
                    return factor;
                });
                return factors.join('');
            } else {
                return KhanUtil.expr(arguments[0]);
            }
        },
        'times': function (left, right) {
            var parenthesizeLeft = !KhanUtil.exprIsShort(left);
            var parenthesizeRight = !KhanUtil.exprIsShort(right);
            left = KhanUtil.expr(left);
            right = KhanUtil.expr(right);
            left = parenthesizeLeft ? '(' + left + ')' : left;
            right = parenthesizeRight ? '(' + right + ')' : right;
            return left + ' \\times ' + right;
        },
        'dot': function (left, right) {
            var parenthesizeLeft = !KhanUtil.exprIsShort(left);
            var parenthesizeRight = !KhanUtil.exprIsShort(right);
            left = KhanUtil.expr(left);
            right = KhanUtil.expr(right);
            left = parenthesizeLeft ? '(' + left + ')' : left;
            right = parenthesizeRight ? '(' + right + ')' : right;
            return left + ' \\cdot ' + right;
        },
        '/': function (num, den) {
            var parenthesizeNum = !KhanUtil.exprIsShort(num);
            var parenthesizeDen = !KhanUtil.exprIsShort(den);
            num = KhanUtil.expr(num);
            den = KhanUtil.expr(den);
            num = parenthesizeNum ? '(' + num + ')' : num;
            den = parenthesizeDen ? '(' + den + ')' : den;
            return num + '/' + den;
        },
        'frac': function (num, den) {
            return '\\dfrac{' + KhanUtil.expr(num) + '}{' + KhanUtil.expr(den) + '}';
        },
        '^': function (base, pow) {
            if (pow === 0) {
                return '';
            } else if (pow === 1) {
                return KhanUtil.expr(base);
            }
            var parenthesizeBase, trigFunction;
            switch (KhanUtil.exprType(base)) {
            case '+':
            case '-':
            case '*':
            case '/':
            case '^':
            case 'ln':
                parenthesizeBase = true;
                break;
            case 'number':
                parenthesizeBase = base < 0;
                break;
            case 'sin':
            case 'cos':
            case 'tan':
            case 'csc':
            case 'sec':
            case 'cot':
                parenthesizeBase = false;
                trigFunction = true;
                break;
            default:
                parenthesizeBase = false;
                trigFunction = false;
            }
            base = KhanUtil.expr(base);
            if (parenthesizeBase) {
                base = '(' + base + ')';
            }
            pow = KhanUtil.expr(pow);
            if (trigFunction) {
                return base.replace(/\\(\S+?)\{/, function (match, word) {
                    return '\\' + word + '^{' + pow + '} {';
                });
            } else {
                return base + '^{' + pow + '}';
            }
        },
        'sqrt': function (arg) {
            return '\\sqrt{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'sin': function (arg) {
            return '\\sin{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'cos': function (arg) {
            return '\\cos{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'tan': function (arg) {
            return '\\tan{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'sec': function (arg) {
            return '\\sec{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'csc': function (arg) {
            return '\\sec{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'cot': function (arg) {
            return '\\sec{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        'ln': function (arg) {
            return '\\ln{' + KhanUtil.exprParenthesize(arg) + '}';
        },
        '+-': function () {
            if (arguments.length === 1) {
                return '\\pm ' + KhanUtil.exprParenthesize(arguments[0]);
            } else {
                var args = [].slice.call(arguments, 0);
                return $.map(args, function (term, i) {
                    return KhanUtil.expr(term);
                }).join(' \\pm ');
            }
        }
    },
    computeOperators: {
        'color': function (color, arg) {
            return KhanUtil.expr(arg, true);
        },
        '+': function () {
            var args = [].slice.call(arguments, 0);
            var sum = 0;
            $.each(args, function (i, term) {
                sum += KhanUtil.expr(term, true);
            });
            return sum;
        },
        '-': function () {
            if (arguments.length === 1) {
                return -KhanUtil.expr(arguments[0], true);
            } else {
                var args = [].slice.call(arguments, 0);
                var sum = 0;
                $.each(args, function (i, term) {
                    sum += (i === 0 ? 1 : -1) * KhanUtil.expr(term, true);
                });
                return sum;
            }
        },
        '*': function () {
            var args = [].slice.call(arguments, 0);
            var prod = 1;
            $.each(args, function (i, term) {
                prod *= KhanUtil.expr(term, true);
            });
            return prod;
        },
        '/': function () {
            var args = [].slice.call(arguments, 0);
            var prod = 1;
            $.each(args, function (i, term) {
                var e = KhanUtil.expr(term, true);
                prod *= i === 0 ? e : 1 / e;
            });
            return prod;
        },
        '^': function (base, pow) {
            return Math.pow(KhanUtil.expr(base, true), KhanUtil.expr(pow, true));
        },
        'sqrt': function (arg) {
            return Math.sqrt(KhanUtil.expr(arg, true));
        },
        '+-': function () {
            return NaN;
        }
    },
    exprStripColor: function (expr) {
        if (typeof expr !== 'object') {
            return expr;
        } else if (expr[0] === 'color') {
            return KhanUtil.exprStripColor(expr[2]);
        } else {
            return $.map(expr, function (el, i) {
                return [i === 0 ? el : KhanUtil.exprStripColor(el)];
            });
        }
    },
    exprSimplifyAssociative: function (expr) {
        if (typeof expr !== 'object') {
            return expr;
        }
        var simplified = $.map(expr.slice(1), function (x) {
            return [KhanUtil.exprSimplifyAssociative(x)];
        });
        var flattenOneLevel = function (e) {
            switch (expr[0]) {
            case '+':
                if (e[0] === '+') {
                    return e.slice(1);
                }
                break;
            case '*':
                if (e[0] === '*') {
                    return e.slice(1);
                }
                break;
            }
            return [e];
        };
        var ret = $.map(simplified, flattenOneLevel);
        ret.unshift(expr[0]);
        return ret;
    }
});
KhanUtil.computeOperators['frac'] = KhanUtil.computeOperators['/'];
},{}],2:[function(require,module,exports){
require('./expressions.js');
var kmatrix = KhanUtil.kmatrix = {
    deepZipWith: function (depth, fn) {
        var arrays = [].slice.call(arguments, 2);
        var hasNullValue = _.any(arrays, function (array) {
            if (array === null) {
                return true;
            }
        });
        if (hasNullValue) {
            return null;
        }
        if (depth === 0) {
            return fn.apply(null, arrays);
        } else {
            return _.map(_.zip.apply(_, arrays), function (els) {
                return kmatrix.deepZipWith.apply(this, [
                    depth - 1,
                    fn
                ].concat(els));
            });
        }
    },
    matrixCopy: function (mat) {
        return $.extend(true, [], mat);
    },
    matrixMap: function (fn, mat) {
        return _.map(mat, function (row, i) {
            return _.map(row, function (elem, j) {
                return fn(elem, i, j);
            });
        });
    },
    maskMatrix: function (mat, excludeList) {
        var result = [];
        _.times(mat.r, function (i) {
            var row = [];
            _.times(mat.c, function (j) {
                if (KhanUtil.contains(excludeList, [
                        i + 1,
                        j + 1
                    ])) {
                    row.push(mat[i][j]);
                } else {
                    row.push('?');
                }
            });
            result.push(row);
        });
        return result;
    },
    printMatrix: function (fn) {
        var args = Array.prototype.slice.call(arguments);
        var mat = kmatrix.deepZipWith.apply(this, [2].concat(args));
        if (!mat) {
            return null;
        }
        var table = _.map(mat, function (row, i) {
            return row.join(' & ');
        }).join(' \\\\ ');
        var prefix = '\\left[\\begin{array}';
        var suffix = '\\end{array}\\right]';
        var alignment = '{';
        var cols = mat[0].length;
        _(cols).times(function () {
            alignment += 'r';
        });
        alignment += '}';
        return prefix + alignment + table + suffix;
    },
    printSimpleMatrix: function (mat, color) {
        return kmatrix.printMatrix(function (item) {
            if (color) {
                return KhanUtil.colorMarkup(item, color);
            }
            return item;
        }, mat);
    },
    printFractionMatrix: function (mat, color) {
        return kmatrix.printMatrix(function (item) {
            item = KhanUtil.decimalFraction(item, true);
            if (color) {
                return KhanUtil.colorMarkup(item, color);
            }
            return item;
        }, mat);
    },
    printSimpleMatrixDet: function (mat, color) {
        return kmatrix.printSimpleMatrix(mat, color).replace('left[', 'left|').replace('right]', 'right|');
    },
    printColoredDimMatrix: function (mat, colors, isRow) {
        var matrix = kmatrix.matrixMap(function (item, i, j) {
            var color = colors[isRow ? i : j];
            return KhanUtil.colorMarkup(item, color);
        }, mat);
        return kmatrix.printSimpleMatrix(matrix);
    },
    makeMultHintMatrix: function (a, b, rowColors, colColors) {
        var c = [];
        _.times(a.r, function () {
            c.push([]);
        });
        _.times(a.r, function (i) {
            var c1 = rowColors[i];
            _.times(b.c, function (j) {
                var c2 = colColors[j];
                var temp = '';
                _.times(a.c, function (k) {
                    if (k > 0) {
                        temp += '+';
                    }
                    var elem1 = KhanUtil.colorMarkup(a[i][k], c1);
                    var elem2 = KhanUtil.colorMarkup(b[k][j], c2);
                    temp += elem1 + '\\cdot' + elem2;
                });
                c[i][j] = temp;
            });
        });
        return kmatrix.makeMatrix(c);
    },
    makeMatrix: function (mat) {
        mat.r = mat.length;
        mat.c = mat[0].length;
        return mat;
    },
    cropMatrix: function (mat, rowIndex, colIndex) {
        var cropped = kmatrix.matrixCopy(mat);
        cropped.splice(rowIndex, 1);
        _.each(cropped, function (row) {
            row.splice(colIndex, 1);
        });
        return cropped;
    },
    matrix2x2DetHint: function (mat) {
        var operator = typeof mat[0][0] === 'string' ? ' \\times ' : ' \\cdot ';
        var termA = '(' + mat[0][0] + operator + mat[1][1] + ')';
        var termB = '(' + mat[0][1] + operator + mat[1][0] + ')';
        return termA + '-' + termB;
    },
    matrix3x3DetHint: function (mat, isIntermediate) {
        var tex = '';
        _.times(mat.c, function (j) {
            var hintMat = kmatrix.cropMatrix(mat, 0, j);
            var sign = j % 2 ? '-' : '+';
            sign = j === 0 ? '' : sign;
            var multiplier = mat[0][j];
            var term;
            if (isIntermediate) {
                term = kmatrix.printSimpleMatrixDet(hintMat);
            } else {
                term = kmatrix.matrix2x2DetHint(hintMat);
                term = KhanUtil.exprParenthesize(term);
            }
            tex += sign + multiplier + term;
        });
        return tex;
    },
    matrixMult: function (a, b) {
        a = kmatrix.makeMatrix(a);
        b = kmatrix.makeMatrix(b);
        var c = [];
        _.times(a.r, function () {
            c.push([]);
        });
        _.times(a.r, function (i) {
            _.times(b.c, function (j) {
                var temp = 0;
                _.times(a.c, function (k) {
                    temp += a[i][k] * b[k][j];
                });
                c[i][j] = temp;
            });
        });
        return kmatrix.makeMatrix(c);
    },
    matrixMinors: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        if (!mat.r || !mat.c) {
            return null;
        }
        var rr = kmatrix.matrixMap(function (input, row, elem) {
            return kmatrix.cropMatrix(mat, row, elem);
        }, mat);
        return rr;
    },
    matrixTranspose: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        var r = mat.c;
        var c = mat.r;
        if (!r || !c) {
            return null;
        }
        var matT = [];
        _.times(r, function (i) {
            var row = [];
            _.times(c, function (j) {
                row.push(mat[j][i]);
            });
            matT.push(row);
        });
        return kmatrix.makeMatrix(matT);
    },
    matrixDet: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        if (mat.r !== mat.c) {
            return null;
        }
        var a, b, c, d, e, f, g, h, k, det;
        if (mat.r === 2) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[1][0];
            d = mat[1][1];
            det = a * d - b * c;
        } else if (mat.r === 3) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[0][2];
            d = mat[1][0];
            e = mat[1][1];
            f = mat[1][2];
            g = mat[2][0];
            h = mat[2][1];
            k = mat[2][2];
            det = a * (e * k - f * h) - b * (k * d - f * g) + c * (d * h - e * g);
        }
        return det;
    },
    matrixAdj: function (mat) {
        mat = kmatrix.makeMatrix(mat);
        var a, b, c, d, e, f, g, h, k;
        var adj;
        if (mat.r === 2) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[1][0];
            d = mat[1][1];
            adj = [
                [
                    d,
                    -b
                ],
                [
                    -c,
                    a
                ]
            ];
        } else if (mat.r === 3) {
            a = mat[0][0];
            b = mat[0][1];
            c = mat[0][2];
            d = mat[1][0];
            e = mat[1][1];
            f = mat[1][2];
            g = mat[2][0];
            h = mat[2][1];
            k = mat[2][2];
            var A = e * k - f * h;
            var B = -(d * k - f * g);
            var C = d * h - e * g;
            var D = -(b * k - c * h);
            var E = a * k - c * g;
            var F = -(a * h - b * g);
            var G = b * f - c * e;
            var H = -(a * f - c * d);
            var K = a * e - b * d;
            adj = [
                [
                    A,
                    D,
                    G
                ],
                [
                    B,
                    E,
                    H
                ],
                [
                    C,
                    F,
                    K
                ]
            ];
        }
        if (adj) {
            adj = kmatrix.makeMatrix(adj);
        }
        return adj;
    },
    matrixInverse: function (mat, precision) {
        var det = kmatrix.matrixDet(mat);
        if (!det) {
            return null;
        }
        var adj = kmatrix.matrixAdj(mat);
        if (!adj) {
            return null;
        }
        var inv = kmatrix.deepZipWith(2, function (val) {
            val = val / det;
            if (precision) {
                val = KhanUtil.roundTo(precision, val);
            }
            return val;
        }, adj);
        inv = kmatrix.makeMatrix(inv);
        return inv;
    },
    matrixPad: function (mat, rows, cols, padVal) {
        if (!mat) {
            return null;
        }
        mat = kmatrix.makeMatrix(mat);
        var matP = kmatrix.matrixCopy(mat);
        var finalCols = Math.max(cols, mat.c);
        if (padVal === undefined) {
            padVal = '';
        }
        var dcols = cols - matP.c;
        if (dcols > 0) {
            _.times(matP.r, function (i) {
                _.times(dcols, function () {
                    matP[i].push(padVal);
                });
            });
        }
        var drows = rows - matP.r;
        if (drows > 0) {
            _.times(drows, function () {
                var row = [];
                _.times(finalCols, function () {
                    row.push(padVal);
                });
                matP.push(row);
            });
        }
        return kmatrix.makeMatrix(matP);
    },
    arrayToColumn: function (arr) {
        var col = [];
        _.each(arr, function (e) {
            col.push([e]);
        });
        return kmatrix.makeMatrix(col);
    },
    columnToArray: function (col) {
        var arr = [];
        _.each(col, function (e) {
            arr.push(e[0]);
        });
        return arr;
    }
};
_.each(kmatrix, function (func, name) {
    KhanUtil[name] = func;
});
module.exports = kmatrix;
},{"./expressions.js":1}]},{},[2]);
