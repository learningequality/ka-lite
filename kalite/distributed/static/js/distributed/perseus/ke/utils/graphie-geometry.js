(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var table = '00000000 77073096 EE0E612C 990951BA 076DC419 706AF48F E963A535 ' + '9E6495A3 0EDB8832 79DCB8A4 E0D5E91E 97D2D988 09B64C2B 7EB17CBD ' + 'E7B82D07 90BF1D91 1DB71064 6AB020F2 F3B97148 84BE41DE 1ADAD47D ' + '6DDDE4EB F4D4B551 83D385C7 136C9856 646BA8C0 FD62F97A 8A65C9EC ' + '14015C4F 63066CD9 FA0F3D63 8D080DF5 3B6E20C8 4C69105E D56041E4 ' + 'A2677172 3C03E4D1 4B04D447 D20D85FD A50AB56B 35B5A8FA 42B2986C ' + 'DBBBC9D6 ACBCF940 32D86CE3 45DF5C75 DCD60DCF ABD13D59 26D930AC ' + '51DE003A C8D75180 BFD06116 21B4F4B5 56B3C423 CFBA9599 B8BDA50F ' + '2802B89E 5F058808 C60CD9B2 B10BE924 2F6F7C87 58684C11 C1611DAB ' + 'B6662D3D 76DC4190 01DB7106 98D220BC EFD5102A 71B18589 06B6B51F ' + '9FBFE4A5 E8B8D433 7807C9A2 0F00F934 9609A88E E10E9818 7F6A0DBB ' + '086D3D2D 91646C97 E6635C01 6B6B51F4 1C6C6162 856530D8 F262004E ' + '6C0695ED 1B01A57B 8208F4C1 F50FC457 65B0D9C6 12B7E950 8BBEB8EA ' + 'FCB9887C 62DD1DDF 15DA2D49 8CD37CF3 FBD44C65 4DB26158 3AB551CE ' + 'A3BC0074 D4BB30E2 4ADFA541 3DD895D7 A4D1C46D D3D6F4FB 4369E96A ' + '346ED9FC AD678846 DA60B8D0 44042D73 33031DE5 AA0A4C5F DD0D7CC9 ' + '5005713C 270241AA BE0B1010 C90C2086 5768B525 206F85B3 B966D409 ' + 'CE61E49F 5EDEF90E 29D9C998 B0D09822 C7D7A8B4 59B33D17 2EB40D81 ' + 'B7BD5C3B C0BA6CAD EDB88320 9ABFB3B6 03B6E20C 74B1D29A EAD54739 ' + '9DD277AF 04DB2615 73DC1683 E3630B12 94643B84 0D6D6A3E 7A6A5AA8 ' + 'E40ECF0B 9309FF9D 0A00AE27 7D079EB1 F00F9344 8708A3D2 1E01F268 ' + '6906C2FE F762575D 806567CB 196C3671 6E6B06E7 FED41B76 89D32BE0 ' + '10DA7A5A 67DD4ACC F9B9DF6F 8EBEEFF9 17B7BE43 60B08ED5 D6D6A3E8 ' + 'A1D1937E 38D8C2C4 4FDFF252 D1BB67F1 A6BC5767 3FB506DD 48B2364B ' + 'D80D2BDA AF0A1B4C 36034AF6 41047A60 DF60EFC3 A867DF55 316E8EEF ' + '4669BE79 CB61B38C BC66831A 256FD2A0 5268E236 CC0C7795 BB0B4703 ' + '220216B9 5505262F C5BA3BBE B2BD0B28 2BB45A92 5CB36A04 C2D7FFA7 ' + 'B5D0CF31 2CD99E8B 5BDEAE1D 9B64C2B0 EC63F226 756AA39C 026D930A ' + '9C0906A9 EB0E363F 72076785 05005713 95BF4A82 E2B87A14 7BB12BAE ' + '0CB61B38 92D28E9B E5D5BE0D 7CDCEFB7 0BDBDF21 86D3D2D4 F1D4E242 ' + '68DDB3F8 1FDA836E 81BE16CD F6B9265B 6FB077E1 18B74777 88085AE6 ' + 'FF0F6A70 66063BCA 11010B5C 8F659EFF F862AE69 616BFFD3 166CCF45 ' + 'A00AE278 D70DD2EE 4E048354 3903B3C2 A7672661 D06016F7 4969474D ' + '3E6E77DB AED16A4A D9D65ADC 40DF0B66 37D83BF0 A9BCAE53 DEBB9EC5 ' + '47B2CF7F 30B5FFE9 BDBDF21C CABAC28A 53B39330 24B4A3A6 BAD03605 ' + 'CDD70693 54DE5729 23D967BF B3667A2E C4614AB8 5D681B02 2A6F2B94 ' + 'B40BBE37 C30C8EA1 5A05DF1B 2D02EF8D';
var crc32 = function (str, crc) {
    if (crc == null) {
        crc = 0;
    }
    var n = 0;
    var x = 0;
    crc = crc ^ -1;
    for (var i = 0, iTop = str.length; i < iTop; i++) {
        n = (crc ^ str.charCodeAt(i)) & 255;
        x = '0x' + table.substr(n * 9, 8);
        crc = crc >>> 8 ^ x;
    }
    return Math.abs(crc ^ -1);
};
module.exports = crc32;
},{}],2:[function(require,module,exports){
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
},{}],3:[function(require,module,exports){
require('./graphie.js');
var kline = require('./kline.js');
var kmatrix = require('./kmatrix.js');
window.rotatePoint = function (p, deg, c) {
    c = c || [
        0,
        0
    ];
    var rad = KhanUtil.toRadians(deg), cos = Math.cos(rad), sin = Math.sin(rad), cx = c[0], cy = c[1], px = p[0], py = p[1], x = cx + (px - cx) * cos - (py - cy) * sin, y = cy + (px - cx) * sin + (py - cy) * cos;
    return [
        KhanUtil.roundTo(9, x),
        KhanUtil.roundTo(9, y)
    ];
};
$.extend(KhanUtil, {
    rightAngleBox: function (path1, path2, style) {
        var graph = KhanUtil.currentGraph;
        var size = 0.5;
        var intersection = findIntersection(path1, path2), path = [intersection], curr = graph.cartToPolar(intersection)[1], offset;
        for (var i = 1; i < 4; i++) {
            offset = graph.polar(size, curr);
            path.push([
                path[i - 1][0] - offset[0],
                path[i - 1][1] - offset[1]
            ]);
            curr -= 90;
        }
        path.push(intersection);
        return graph.path(path, style);
    },
    parallel: function (path, num, style) {
        var graph = KhanUtil.currentGraph;
        var point = kline.midpoint(path);
        graph.path([
            path[0],
            point
        ], $.extend(style, { arrows: '->' }));
    },
    congruent: function (path, num, style) {
        var graph = KhanUtil.currentGraph;
        var spacing = 5, scale = 5;
        for (var i = 0; i < num; i++) {
            var sPath = _.map(path, graph.scalePoint), sPoint = kline.midpoint(sPath), angle = Math.atan((sPath[0][1] - sPath[1][1]) / (sPath[0][0] - sPath[1][0])), perpangle = angle + Math.PI / 2;
            var sMarkPath = [
                [
                    sPoint[0] + Math.cos(angle) * spacing * i + Math.cos(perpangle) * scale,
                    sPoint[1] + Math.sin(angle) * spacing * i + Math.sin(perpangle) * scale
                ],
                [
                    sPoint[0] + Math.cos(angle) * spacing * i - Math.cos(perpangle) * scale,
                    sPoint[1] + Math.sin(angle) * spacing * i - Math.sin(perpangle) * scale
                ]
            ];
            graph.path(_.map(sMarkPath, graph.unscalePoint), style);
        }
    }
});
window.lineLength = function (line) {
    var a = line[0];
    var b = line[1];
    return Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]));
};
window.clearArray = function (arr, i) {
    return $.map(arr, function (el, index) {
        if ($.inArray(index, i) !== -1) {
            return el;
        } else {
            return '';
        }
    });
};
window.mergeArray = function (ar1, ar2) {
    var i = 0;
    for (i = 0; i < ar1.length; i++) {
        if (ar1[i] === '') {
            ar1[i] = ar2[i];
        }
    }
    return ar1;
};
window.isPointOnLineSegment = function (l, p, precision) {
    precision = precision || 0.1;
    if (Math.abs(l[1][0] - l[0][0]) < precision) {
        return Math.abs(p[0] - l[0][0]) < precision && p[1] <= Math.max(l[1][1], l[0][1]) + precision && p[1] >= Math.min(l[1][1], l[0][1]) - precision;
    }
    var m = (l[1][1] - l[0][1]) / (l[1][0] - l[0][0]);
    var k = l[0][1] - m * l[0][0];
    return Math.abs(m * p[0] + k - p[1]) < precision;
};
window.areIntersecting = function (pol1, pol2) {
    var i, k = 0;
    for (i = 0; i < pol1.length; i++) {
        for (k = 0; k < pol2.length; k++) {
            if (findIntersection(pol1[i], pol2[k])[2]) {
                return true;
            }
        }
    }
    return false;
};
window.findIntersection = function (a, b) {
    var tY = [
        0,
        a[0][1],
        a[1][1],
        b[0][1],
        b[1][1]
    ];
    var tX = [
        0,
        a[0][0],
        a[1][0],
        b[0][0],
        b[1][0]
    ];
    var denominator = (tY[4] - tY[3]) * (tX[2] - tX[1]) - (tX[4] - tX[3]) * (tY[2] - tY[1]);
    var ua = ((tX[4] - tX[3]) * (tY[1] - tY[3]) - (tY[4] - tY[3]) * (tX[1] - tX[3])) / denominator;
    var ub = ((tX[2] - tX[1]) * (tY[1] - tY[3]) - (tY[2] - tY[1]) * (tX[1] - tX[3])) / denominator;
    var isContained = ua >= -0.01 && ua <= 1.01 && ub >= -0.01 && ub <= 1.01;
    return [
        tX[1] + ua * (tX[2] - tX[1]),
        tY[1] + ua * (tY[2] - tY[1]),
        isContained
    ];
};
window.degToRad = function (deg) {
    return deg * Math.PI / 180;
};
window.lineEquation = function (line) {
    var m = (line[1][1] - line[0][1]) / (line[1][0] - line[0][0]);
    var k = line[0][1] - m * line[0][0];
    return [
        m,
        k
    ];
};
window.lineSegmentFromLine = function (start, line, amount) {
    var eq = lineEquation(line);
    var m = eq[0];
    var angle = Math.atan(m);
    return [
        start,
        [
            start[0] + Math.cos(angle) * amount,
            start[1] + Math.sin(angle) * amount
        ]
    ];
};
window.parallelLine = function (line, point) {
    var dif = [
        point[0] - line[0][0],
        point[1] - line[0][1]
    ];
    return [
        point,
        [
            line[1][0] + dif[0],
            line[1][1] + dif[1]
        ]
    ];
};
window.movePoint = function (p, a) {
    return [
        p[0] + a[0],
        p[1] + a[1]
    ];
};
window.bisectAngle = function (line1, line2, scale) {
    var intPoint = findIntersection(line1, line2);
    var l1 = [];
    var l2 = [];
    if (line1[1][0] - line1[0][0] >= 0) {
        l1 = lineSegmentFromLine(intPoint, line1, scale);
    } else {
        l1 = lineSegmentFromLine(intPoint, line1, -scale);
    }
    if (line2[1][0] - line2[0][0] >= 0) {
        l2 = lineSegmentFromLine(intPoint, line2, scale);
    } else {
        l2 = lineSegmentFromLine(intPoint, line2, -scale);
    }
    return [
        intPoint,
        parallelLine(l1, l2[1])[1]
    ];
};
window.vectorProduct = function (line1, line2) {
    var x1 = line1[1][0] - line1[0][0];
    var x2 = line2[1][0] - line2[0][0];
    var y1 = line1[1][1] - line1[0][1];
    var y2 = line2[1][1] - line2[0][1];
    return x1 * y2 - x2 * y1;
};
window.reverseLine = function (line) {
    return [
        line[1],
        line[0]
    ];
};
window.Triangle = function (center, angles, scale, labels, points) {
    var fromPoints = false;
    if (points) {
        fromPoints = true;
    }
    this.labels = labels;
    if (fromPoints) {
        this.points = points;
        this.sides = [
            [
                this.points[0],
                this.points[1]
            ],
            [
                this.points[1],
                this.points[2]
            ],
            [
                this.points[2],
                this.points[0]
            ]
        ];
        this.sideLengths = $.map(this.sides, lineLength);
        this.angles = anglesFromSides(this.sideLengths);
    } else {
        this.angles = angles;
    }
    this.radAngles = $.map(angles, degToRad);
    this.scale = scale || 3;
    this.cosines = $.map(this.radAngles, Math.cos);
    this.sines = $.map(this.radAngles, Math.sin);
    this.x = center[0];
    this.y = center[1];
    this.rotation = 0;
    var a = Math.sqrt(2 * this.scale * this.sines[1] / (this.sines[0] * this.sines[2]));
    var b = a * this.sines[2] / this.sines[1];
    if (!fromPoints) {
        this.points = [
            [
                this.x,
                this.y
            ],
            [
                b + this.x,
                this.y
            ],
            [
                this.cosines[0] * a + this.x,
                this.sines[0] * a + this.y
            ]
        ];
    }
    this.sides = [
        [
            this.points[0],
            this.points[1]
        ],
        [
            this.points[1],
            this.points[2]
        ],
        [
            this.points[2],
            this.points[0]
        ]
    ];
    this.sideLengths = $.map(this.sides, lineLength);
    this.niceSideLengths = $.map(this.sideLengths, function (x) {
        return parseFloat(x.toFixed(1));
    });
    this.set = '';
    this.niceAngles = $.map(this.angles, function (x) {
        return x + '^{\\circ}';
    });
    this.labelObjects = {
        'sides': [],
        'angles': [],
        'points': [],
        'name': []
    };
    this.angleScale = function (ang) {
        if (ang > 150) {
            return 0.8;
        } else if (ang > 140) {
            return 0.7;
        } else if (ang > 130) {
            return 0.6;
        } else if (ang > 90) {
            return 0.5;
        } else if (ang > 40) {
            return 0.6;
        } else if (ang > 25) {
            return 0.7;
        }
        return 0.8;
    };
    this.draw = function () {
        this.set = this.set || KhanUtil.currentGraph.raphael.set();
        this.set.push(KhanUtil.currentGraph.path(this.points.concat([this.points[0]])));
        return this.set;
    };
    this.color = 'black';
    this.createLabel = function (p, v) {
        this.set = this.set || KhanUtil.currentGraph.raphael.set();
        this.set.push(KhanUtil.currentGraph.label(p, v, 'center', { color: this.color }));
    };
    this.boxOut = function (pol, amount) {
        var shouldMove = areIntersecting(pol, this.sides);
        while (areIntersecting(pol, this.sides)) {
            this.translate(amount);
        }
        if (shouldMove) {
            this.translate(amount);
        }
    };
    this.boundingRange = function (margin) {
        margin = margin || 0;
        var X = $.map(this.points, function (p) {
            return p[0];
        });
        var Y = $.map(this.points, function (p) {
            return p[1];
        });
        return [
            [
                _.min(X) - margin,
                _.max(X) + margin
            ],
            [
                _.min(Y) - margin,
                _.max(Y) + margin
            ]
        ];
    };
    this.findCenterPoints = function () {
        var Ax = this.points[0][0];
        var Ay = this.points[0][1];
        var Bx = this.points[1][0];
        var By = this.points[1][1];
        var Cx = this.points[2][0];
        var Cy = this.points[2][1];
        var D = 2 * (Ax * (By - Cy) + Bx * (Cy - Ay) + Cx * (Ay - By));
        var a = this.sideLengths[1];
        var b = this.sideLengths[2];
        var c = this.sideLengths[0];
        var P = a + b + c;
        var x1 = (a * Ax + b * Bx + c * Cx) / P;
        var y1 = (a * Ay + b * By + c * Cy) / P;
        var x = ((Ay * Ay + Ax * Ax) * (By - Cy) + (By * By + Bx * Bx) * (Cy - Ay) + (Cy * Cy + Cx * Cx) * (Ay - By)) / D;
        var y = ((Ay * Ay + Ax * Ax) * (Cx - Bx) + (By * By + Bx * Bx) * (Ax - Cx) + (Cy * Cy + Cx * Cx) * (Bx - Ax)) / D;
        this.circumCenter = [
            x,
            y
        ];
        this.centroid = [
            1 / 3 * (Ax + Bx + Cx),
            1 / 3 * (Ay + By + Cy)
        ];
        this.inCenter = [
            x1,
            y1
        ];
    };
    this.findCenterPoints();
    this.findRadii = function () {
        this.semiperimeter = (this.sideLengths[0] + this.sideLengths[1] + this.sideLengths[2]) / 2;
        this.inradius = this.scale / this.semiperimeter;
        this.circumradius = this.sideLengths[0] * this.sideLengths[1] * this.sideLengths[2] / (4 * this.semiperimeter * this.inradius);
    };
    this.rotationCenter = this.centroid;
    this.rotate = function (amount) {
        amount = amount * Math.PI / 180;
        var tr = this;
        this.points = $.map(this.points, function (el, i) {
            return [tr.rotatePoint(el, amount)];
        });
        this.genSides();
        this.findCenterPoints();
    };
    this.genSides = function () {
        this.sides = [];
        var x = 0;
        for (x = 0; x < this.points.length; x++) {
            this.sides.push([
                this.points[x],
                this.points[(x + 1) % this.points.length]
            ]);
        }
    };
    this.translate = function (amount) {
        this.points = $.map(this.points, function (el, i) {
            return [movePoint(el, amount)];
        });
        this.genSides();
        this.findCenterPoints();
    };
    this.rotatePoint = function (pos, theta) {
        theta = theta || this.rotation;
        return [
            this.rotationCenter[0] + (pos[0] - this.rotationCenter[0]) * Math.cos(theta) + (pos[1] - this.rotationCenter[1]) * Math.sin(theta),
            this.rotationCenter[1] + -1 * ((pos[0] - this.rotationCenter[0]) * Math.sin(theta)) + (pos[1] - this.rotationCenter[1]) * Math.cos(theta)
        ];
    };
    this.drawLabels = function () {
        var i = 0;
        var s = KhanUtil.currentGraph.scaleVector([
            1,
            1
        ])[0];
        if ('points' in this.labels) {
            for (i = this.angles.length - 1; i >= 0; i--) {
                var n = (i + 1) % this.angles.length;
                var coord = bisectAngle(reverseLine(this.sides[n]), this.sides[i], 12 / s)[1];
                this.labelObjects.points.push(this.createLabel(coord, this.labels.points[n]));
            }
        }
        if ('angles' in this.labels) {
            for (i = this.angles.length - 1; i >= 0; i--) {
                var n = (i + 1) % this.angles.length;
                var coord = bisectAngle(this.sides[n], reverseLine(this.sides[i]), this.angleScale(this.angles[n]) * 45 / s)[1];
                this.labelObjects.angles.push(this.createLabel(coord, this.labels.angles[n]));
            }
        }
        if ('sides' in this.labels) {
            for (i = 0; i < this.sides.length; i++) {
                var midPoint = kline.midpoint(this.sides[i]);
                var t = lineLength([
                    this.sides[i][1],
                    midPoint
                ]);
                var d = 15 / s;
                var x3 = midPoint[0] + (this.sides[i][1][1] - midPoint[1]) / t * d;
                var y3 = midPoint[1] - (this.sides[i][1][0] - midPoint[0]) / t * d;
                this.labelObjects.sides.push(this.createLabel([
                    x3,
                    y3
                ], this.labels.sides[i]));
            }
        }
        if ('name' in this.labels) {
            this.labelObjects['name'] = this.createLabel(bisectAngle(reverseLine(this.sides[2]), this.sides[1], 0.3)[1], this.labels.name);
        }
        if ('c' in this.labels) {
            this.createLabel([
                (this.points[0][0] + this.points[1][0]) / 2,
                (this.points[0][1] + this.points[1][1]) / 2 - 0.4
            ], labels.c);
        }
        if ('a' in this.labels) {
            this.createLabel([
                (this.points[1][0] + this.points[2][0]) / 2 + 0.4,
                (this.points[1][1] + this.points[2][1]) / 2
            ], labels.a);
        }
        if ('b' in this.labels) {
            this.createLabel([
                (this.points[0][0] + this.points[2][0]) / 2 - 0.4,
                (this.points[0][1] + this.points[2][1]) / 2
            ], labels.b);
        }
        return this.set;
    };
};
window.Quadrilateral = function (center, angles, sideRatio, labels, size) {
    this.sideRatio = sideRatio;
    this.angles = angles;
    this.radAngles = $.map(angles, degToRad);
    this.scale = 1;
    this.rotation = 0;
    this.x = center[0];
    this.y = center[1];
    this.rotationCenter = [
        center[0],
        center[1]
    ];
    this.set = '';
    this.size = size || 10;
    this.cosines = $.map(this.radAngles, Math.cos);
    this.sines = $.map(this.radAngles, Math.sin);
    this.labels = labels || {};
    this.sides = [];
    this.generatePoints = function () {
        var once = false;
        while (!once || this.isCrossed() || this.sideTooShort()) {
            var len = Math.sqrt(2 * this.scale * this.scale * this.sideRatio * this.sideRatio - 2 * this.sideRatio * this.scale * this.scale * this.sideRatio * this.cosines[3]);
            once = true;
            var tX = [
                0,
                this.scale * this.sideRatio * this.cosines[0],
                len * Math.cos((this.angles[0] - (180 - this.angles[3]) / 2) * Math.PI / 180),
                this.scale,
                this.scale + Math.cos((180 - this.angles[1]) * Math.PI / 180)
            ];
            var tY = [
                0,
                this.scale * this.sideRatio * this.sines[0],
                len * Math.sin((this.angles[0] - (180 - this.angles[3]) / 2) * Math.PI / 180),
                0,
                Math.sin((180 - this.angles[1]) * Math.PI / 180)
            ];
            var denominator = (tY[4] - tY[3]) * (tX[2] - tX[1]) - (tX[4] - tX[3]) * (tY[2] - tY[1]);
            var ua = ((tX[4] - tX[3]) * (tY[1] - tY[3]) - (tY[4] - tY[3]) * (tX[1] - tX[3])) / denominator;
            this.points = [
                [
                    this.x,
                    this.y
                ],
                [
                    this.x + this.scale * this.sideRatio * this.cosines[0],
                    this.y + this.scale * this.sideRatio * this.sines[0]
                ],
                [
                    this.x + tX[1] + ua * (tX[2] - tX[1]),
                    this.y + tY[1] + ua * (tY[2] - tY[1])
                ],
                [
                    this.x + this.scale,
                    this.y
                ]
            ];
            this.sides = [
                [
                    this.points[0],
                    this.points[3]
                ],
                [
                    this.points[3],
                    this.points[2]
                ],
                [
                    this.points[2],
                    this.points[1]
                ],
                [
                    this.points[1],
                    this.points[0]
                ]
            ];
            this.sideLengths = $.map(this.sides, lineLength);
            this.niceSideLengths = $.map(this.sideLengths, function (x) {
                return parseFloat(x.toFixed(1));
            });
            if (vectorProduct([
                    this.points[0],
                    this.points[1]
                ], [
                    this.points[0],
                    this.points[2]
                ]) > 0) {
                this.sideRatio -= 0.3;
            }
            if (vectorProduct([
                    this.points[0],
                    this.points[3]
                ], [
                    this.points[0],
                    this.points[2]
                ]) < 0) {
                this.sideRatio += 0.3;
            }
            var tooShort = this.sideTooShort();
            if (tooShort) {
                if (tooShort.whichSide % 2 === 0) {
                    this.sideRatio -= 0.05;
                } else {
                    this.sideRatio += 0.05;
                }
            }
        }
    };
    this.sideTooShort = function () {
        if (this.sideRatio === 1) {
            return false;
        }
        var shortestSide = _.min(this.sideLengths);
        var allSides = _.reduce(this.sideLengths, function (acc, n) {
            return acc + n;
        }, 0);
        return shortestSide / allSides < 0.12 && { whichSide: _.indexOf(this.sideLengths, shortestSide) };
    };
    this.isCrossed = function () {
        return vectorProduct([
            this.points[0],
            this.points[1]
        ], [
            this.points[0],
            this.points[2]
        ]) > 0 || vectorProduct([
            this.points[0],
            this.points[3]
        ], [
            this.points[0],
            this.points[2]
        ]) < 0;
    };
    this.genSides = function () {
        this.sides = [
            [
                this.points[0],
                this.points[3]
            ],
            [
                this.points[3],
                this.points[2]
            ],
            [
                this.points[2],
                this.points[1]
            ],
            [
                this.points[1],
                this.points[0]
            ]
        ];
    };
    this.generatePoints();
    var area = 0.5 * vectorProduct([
        this.points[0],
        this.points[2]
    ], [
        this.points[3],
        this.points[1]
    ]);
    this.scale = this.scale * Math.sqrt(this.size / area);
    this.generatePoints();
    area = 0.5 * vectorProduct([
        this.points[0],
        this.points[2]
    ], [
        this.points[3],
        this.points[1]
    ]);
};
Quadrilateral.prototype = new Triangle([
    0,
    0
], [
    30,
    30,
    30
], 3, '');
window.anglesFromSides = function (sides) {
    var c = sides[0];
    var a = sides[1];
    var b = sides[2];
    var gamma = Math.round(Math.acos((a * a + b * b - c * c) / (2 * a * b)) * 180 / Math.PI);
    var beta = Math.round(Math.acos((a * a + c * c - b * b) / (2 * a * c)) * 180 / Math.PI);
    var alpha = Math.round(Math.acos((b * b + c * c - a * a) / (2 * b * c)) * 180 / Math.PI);
    return [
        alpha,
        beta,
        gamma
    ];
};
window.randomTriangleAngles = {
    triangle: function () {
        var a, b, c;
        a = KhanUtil.randRange(30, 120);
        b = KhanUtil.randRange(30, 150 - a);
        c = 180 - a - b;
        return [
            a,
            b,
            c
        ];
    },
    scalene: function () {
        var a, b, c;
        do {
            a = KhanUtil.randRange(30, 120);
            b = KhanUtil.randRange(30, 150 - a);
            c = 180 - a - b;
        } while (a === b || a === c || b === c);
        return [
            a,
            b,
            c
        ];
    },
    isosceles: function () {
        var a = KhanUtil.randRangeExclude(25, 75, [60]);
        var c = 180 - 2 * a;
        return KhanUtil.shuffle([
            a,
            a,
            c
        ]);
    },
    equilateral: function () {
        return [
            60,
            60,
            60
        ];
    }
};
window.randomQuadAngles = {
    square: function () {
        return [
            90,
            90,
            90,
            90
        ];
    },
    rectangle: function () {
        return [
            90,
            90,
            90,
            90
        ];
    },
    rhombus: function () {
        var angA, angB;
        do {
            angA = KhanUtil.randRange(30, 150);
            angB = 180 - angA;
        } while (Math.abs(angA - angB) < 5);
        return [
            angA,
            angB,
            angA,
            angB
        ];
    },
    parallelogram: function () {
        var angA, angB;
        do {
            angA = KhanUtil.randRange(30, 150);
            angB = 180 - angA;
        } while (angA === angB);
        return [
            angA,
            angB,
            angA,
            angB
        ];
    },
    trapezoid: function () {
        var angA, angB, angC, angD;
        do {
            angA = KhanUtil.randRange(30, 150);
            angB = 180 - angA;
            angC = KhanUtil.randRange(30, 150);
            angD = 180 - angC;
        } while (Math.abs(angA - angC) < 6 || angA + angC === 180);
        return [
            angA,
            angC,
            angD,
            angB
        ];
    },
    isoscelesTrapezoid: function () {
        var angC, angD;
        do {
            angC = KhanUtil.randRange(30, 150);
            angD = 180 - angC;
        } while (angC === angD);
        return [
            angC,
            angC,
            angD,
            angD
        ];
    },
    kite: function () {
        var angA, angB, angC;
        do {
            angA = KhanUtil.randRange(90, 140);
            angB = KhanUtil.randRange(30, 360 - 2 * angA - 30);
            angC = 360 - angB - 2 * angA;
        } while (angA === angB);
        return [
            angB,
            angA,
            angC,
            angA
        ];
    }
};
$.extend(KhanUtil, {
    createOddShape: function (options) {
        var shape = $.extend({
            width: 10,
            height: 10,
            squares: [],
            sides: []
        }, options);
        var y = shape.height - 1;
        var left = KhanUtil.randRange(0, shape.width - 1);
        var right = KhanUtil.randRange(left + 1, shape.width);
        shape.sides.push({
            start: [
                left,
                y
            ],
            end: [
                right,
                y
            ],
            length: right - left,
            labelPos: 'above'
        });
        var leftStart = y;
        var rightStart = y;
        _(right - left).times(function (dx) {
            shape.squares.push([
                left + dx,
                y
            ]);
        });
        while (y > 2) {
            y -= 1;
            var prevLeft = left;
            var prevRight = right;
            left = KhanUtil.randRangeWeighted(0, prevRight - 1, prevLeft, 0.7);
            right = KhanUtil.randRangeWeighted(Math.max(left, prevLeft) + 1, shape.width, prevRight, 0.7);
            _(right - left).times(function (dx) {
                shape.squares.push([
                    left + dx,
                    y
                ]);
            });
            if (left !== prevLeft) {
                shape.sides.push({
                    start: [
                        prevLeft,
                        leftStart
                    ],
                    end: [
                        prevLeft,
                        y
                    ],
                    length: leftStart - y,
                    labelPos: 'left'
                });
                shape.sides.push({
                    start: [
                        prevLeft,
                        y
                    ],
                    end: [
                        left,
                        y
                    ],
                    length: Math.abs(left - prevLeft),
                    labelPos: 'center'
                });
                leftStart = y;
            }
            if (right !== prevRight) {
                shape.sides.push({
                    start: [
                        prevRight,
                        rightStart
                    ],
                    end: [
                        prevRight,
                        y
                    ],
                    length: rightStart - y,
                    labelPos: 'right'
                });
                shape.sides.push({
                    start: [
                        prevRight,
                        y
                    ],
                    end: [
                        right,
                        y
                    ],
                    length: Math.abs(right - prevRight),
                    labelPos: 'center'
                });
                rightStart = y;
            }
        }
        shape.sides.push({
            start: [
                left,
                leftStart
            ],
            end: [
                left,
                1
            ],
            length: leftStart - 1,
            labelPos: 'left'
        });
        shape.sides.push({
            start: [
                right,
                rightStart
            ],
            end: [
                right,
                1
            ],
            length: rightStart - 1,
            labelPos: 'right'
        });
        shape.sides.push({
            start: [
                left,
                1
            ],
            end: [
                right,
                1
            ],
            length: right - left,
            labelPos: 'below'
        });
        shape.perimeter = _.reduce(shape.sides, function (perimeter, side) {
            return perimeter + side.length;
        }, 0);
        shape.area = shape.squares.length;
        shape.numSides = shape.sides.length;
        shape.labelSquares = function () {
            _.each(shape.squares, function (square, n) {
                KhanUtil.currentGraph.label([
                    square[0] + 0.5,
                    square[1] - 0.5
                ], n + 1, 'center', false);
            });
        };
        shape.labelSides = function () {
            _.each(shape.sides, function (side) {
                KhanUtil.currentGraph.label([
                    (side.start[0] + side.end[0]) / 2,
                    (side.start[1] + side.end[1]) / 2
                ], side.length, side.labelPos);
            });
        };
        return shape;
    }
});
KhanUtil.solveTriangle = function (triangle) {
    var sides = triangle.sides;
    var angles = triangle.angles;
    var numSides = _.reduce(sides, function (n, side) {
        return n + (typeof side === 'number' ? 1 : 0);
    }, 0);
    var numAngles = _.reduce(angles, function (n, angle) {
        return n + (typeof angle === 'number' ? 1 : 0);
    }, 0);
    if (numSides === 2) {
        var missingSide = sides.indexOf(null);
        var side1 = sides[(missingSide + 1) % 3];
        var side2 = sides[(missingSide + 2) % 3];
        sides[missingSide] = Math.sqrt(side1 * side1 + side2 * side2 - 2 * side1 * side2 * Math.cos(angles[missingSide] * Math.PI / 180));
        numSides = 3;
    }
    if (numSides === 3) {
        angles = _.map(angles, function (angle, n) {
            var oppSide = sides[n];
            var adjSide1 = sides[(n + 1) % 3];
            var adjSide2 = sides[(n + 2) % 3];
            return Math.acos((adjSide1 * adjSide1 + adjSide2 * adjSide2 - oppSide * oppSide) / (2 * adjSide1 * adjSide2));
        });
        angles = _.map(angles, KhanUtil.toDegrees);
    }
    if (numAngles === 2) {
        var missingAngle = angles.indexOf(null);
        angles[missingAngle] = 180 - angles[(missingAngle + 1) % 3] - angles[(missingAngle + 2) % 3];
        numAngles = 3;
    }
    if (numAngles === 3 && numSides >= 1) {
        var knownSide = sides.indexOf(sides[0] || sides[1] || sides[2]);
        sides[(knownSide + 1) % 3] = sides[knownSide] * Math.sin(angles[(knownSide + 1) % 3] * Math.PI / 180) / Math.sin(angles[knownSide] * Math.PI / 180);
        sides[(knownSide + 2) % 3] = sides[knownSide] * Math.sin(angles[(knownSide + 2) % 3] * Math.PI / 180) / Math.sin(angles[knownSide] * Math.PI / 180);
    }
    triangle.sides = sides;
    triangle.angles = angles;
    triangle.isRight = function () {
        return this.angles[0] === 90 || this.angles[1] === 90 || this.angles[2] === 90;
    };
    triangle.isScalene = function () {
        return this.angles[0] !== this.angles[1] && this.angles[1] !== this.angles[2] && this.angles[0] !== this.angles[2];
    };
    triangle.isNotDegenerate = function () {
        return this.sides[1] + this.sides[2] > this.sides[0] && this.sides[0] + this.sides[2] > this.sides[1] && this.sides[0] + this.sides[1] > this.sides[2];
    };
    return triangle;
};
KhanUtil.Graphie.prototype.addTriangle = function (triangle) {
    var graphie = this;
    triangle = $.extend({
        sides: [],
        angles: [],
        points: [],
        sideLabels: [],
        angleLabels: [],
        vertexLabels: [],
        labels: [],
        rot: 0,
        xPos: 0,
        yPos: 0,
        width: 10,
        height: 10,
        color: KhanUtil.BLUE
    }, triangle);
    var rotatePoint = function (point, angle) {
        var matrix = kmatrix.makeMatrix([
            [
                Math.cos(angle),
                -Math.sin(angle),
                0
            ],
            [
                Math.sin(angle),
                Math.cos(angle),
                0
            ],
            [
                0,
                0,
                1
            ]
        ]);
        var vector = kmatrix.makeMatrix([
            [point[0]],
            [point[1]],
            [1]
        ]);
        var prod = kmatrix.matrixMult(matrix, vector);
        return [
            prod[0][0],
            prod[1][0]
        ];
    };
    var findCenterPoints = function (triangle, points) {
        var Ax = points[0][0];
        var Ay = points[0][1];
        var Bx = points[1][0];
        var By = points[1][1];
        var Cx = points[2][0];
        var Cy = points[2][1];
        var D = 2 * (Ax * (By - Cy) + Bx * (Cy - Ay) + Cx * (Ay - By));
        var a = triangle.sides[0];
        var b = triangle.sides[1];
        var c = triangle.sides[2];
        var P = a + b + c;
        var x1 = (a * Ax + b * Bx + c * Cx) / P;
        var y1 = (a * Ay + b * By + c * Cy) / P;
        var x = ((Ay * Ay + Ax * Ax) * (By - Cy) + (By * By + Bx * Bx) * (Cy - Ay) + (Cy * Cy + Cx * Cx) * (Ay - By)) / D;
        var y = ((Ay * Ay + Ax * Ax) * (Cx - Bx) + (By * By + Bx * Bx) * (Ax - Cx) + (Cy * Cy + Cx * Cx) * (Bx - Ax)) / D;
        return {
            circumCenter: [
                x,
                y
            ],
            centroid: [
                1 / 3 * (Ax + Bx + Cx),
                1 / 3 * (Ay + By + Cy)
            ],
            inCenter: [
                x1,
                y1
            ]
        };
    };
    triangle.draw = function () {
        if (triangle.set != null) {
            triangle.set.remove();
        }
        _.each(triangle.labels, function (lbl) {
            lbl.remove();
        });
        triangle.set = graphie.raphael.set();
        triangle.set.push(graphie.path(triangle.points.concat([true]), { stroke: triangle.color }));
        var centerPoints = findCenterPoints(triangle, triangle.points);
        _(3).times(function (i) {
            if (triangle.angleLabels[i] != null) {
                var ang = Math.atan2(centerPoints.inCenter[1] - triangle.points[i][1], centerPoints.inCenter[0] - triangle.points[i][0]);
                var labelDist = (3.51470560176242 - 0.5687298702748785) * Math.exp(-0.037587715462826674 * triangle.angles[i]) + 0.5687298702748785;
                triangle.labels.push(graphie.label([
                    triangle.points[i][0] + Math.cos(ang) * labelDist,
                    triangle.points[i][1] + Math.sin(ang) * labelDist
                ], triangle.angleLabels[i], 'center'));
            }
        });
        _(3).times(function (i) {
            if (triangle.sideLabels[i] != null) {
                var x = (triangle.points[(i + 1) % 3][0] + triangle.points[(i + 2) % 3][0]) / 2;
                var y = (triangle.points[(i + 1) % 3][1] + triangle.points[(i + 2) % 3][1]) / 2;
                var ang;
                if (triangle.angles[i] < 90) {
                    ang = Math.atan2(y - centerPoints.circumCenter[1], x - centerPoints.circumCenter[0]);
                } else if (triangle.angles[i] > 90) {
                    ang = Math.atan2(centerPoints.circumCenter[1] - y, centerPoints.circumCenter[0] - x);
                } else {
                    ang = Math.atan2(y - centerPoints.centroid[1], x - centerPoints.centroid[0]);
                }
                triangle.labels.push(graphie.label([
                    x,
                    y
                ], triangle.sideLabels[i], ang));
            }
        });
        _(3).times(function (i) {
            if (triangle.vertexLabels[i] != null) {
                var ang = Math.atan2(triangle.points[i][1] - centerPoints.inCenter[1], triangle.points[i][0] - centerPoints.inCenter[0]);
                var labelDist = 0.4;
                var lbl = graphie.label([
                    triangle.points[i][0] + Math.cos(ang) * labelDist,
                    triangle.points[i][1] + Math.sin(ang) * labelDist
                ], triangle.vertexLabels[i], 'center');
                lbl.css('color', triangle.color);
                triangle.labels.push(lbl);
            }
        });
    };
    triangle.findAltitude = function (n) {
        var p1 = triangle.points[n];
        var p2 = triangle.points[(n + 1) % 3];
        var p3 = triangle.points[(n + 2) % 3];
        var v1 = [
            p1[0] - p2[0],
            p1[1] - p2[1]
        ];
        var v2 = [
            p3[0] - p2[0],
            p3[1] - p2[1]
        ];
        var dot1 = v1[0] * v2[0] + v1[1] * v2[1];
        var dot2 = v2[0] * v2[0] + v2[1] * v2[1];
        var s = dot1 / dot2;
        return [
            p1,
            [
                p2[0] + v2[0] * s,
                p2[1] + v2[1] * s
            ]
        ];
    };
    triangle.points[2] = [
        0,
        0
    ];
    triangle.points[1] = [
        triangle.sides[0],
        0
    ];
    triangle.points[0] = [
        Math.cos(triangle.angles[2] * Math.PI / 180) * triangle.sides[1],
        Math.sin(triangle.angles[2] * Math.PI / 180) * triangle.sides[1]
    ];
    triangle.points[0] = rotatePoint(triangle.points[0], triangle.rot * Math.PI / 180);
    triangle.points[1] = rotatePoint(triangle.points[1], triangle.rot * Math.PI / 180);
    triangle.points[2] = rotatePoint(triangle.points[2], triangle.rot * Math.PI / 180);
    var minX = _.min(_.map(triangle.points, function (p) {
        return p[0];
    }));
    var maxX = _.max(_.map(triangle.points, function (p) {
        return p[0];
    }));
    var minY = _.min(_.map(triangle.points, function (p) {
        return p[1];
    }));
    var maxY = _.max(_.map(triangle.points, function (p) {
        return p[1];
    }));
    var xScale = triangle.width / (maxX - minX);
    var yScale = triangle.height / (maxY - minY);
    var scale = _.min([
        xScale,
        yScale
    ]);
    triangle.width = (maxX - minX) * scale;
    triangle.height = (maxY - minY) * scale;
    triangle.points = _.map(triangle.points, function (p) {
        return [
            (p[0] - minX) * scale + triangle.xPos,
            (p[1] - minY) * scale + triangle.yPos
        ];
    });
    return triangle;
};
},{"./graphie.js":4,"./kline.js":5,"./kmatrix.js":6}],4:[function(require,module,exports){
var kpoint = require('./kpoint.js');
var kvector = require('./kvector.js');
require('./tex.js');
require('./tmpl.js');
var Graphie = KhanUtil.Graphie = function () {
};
function cartToPolar(coord, angleInRadians) {
    var r = Math.sqrt(Math.pow(coord[0], 2) + Math.pow(coord[1], 2));
    var theta = Math.atan2(coord[1], coord[0]);
    if (theta < 0) {
        theta += 2 * Math.PI;
    }
    if (!angleInRadians) {
        theta = theta * 180 / Math.PI;
    }
    return [
        r,
        theta
    ];
}
function polar(r, th) {
    if (typeof r === 'number') {
        r = [
            r,
            r
        ];
    }
    th = th * Math.PI / 180;
    return [
        r[0] * Math.cos(th),
        r[1] * Math.sin(th)
    ];
}
var intervalIDs = [];
function cleanupIntervals() {
    _.each(intervalIDs, function (intervalID) {
        window.clearInterval(intervalID);
    });
    intervalIDs.length = 0;
}
$.extend(KhanUtil, {
    unscaledSvgPath: function (points) {
        if (points[0] === true) {
            return '';
        }
        return $.map(points, function (point, i) {
            if (point === true) {
                return 'z';
            }
            return (i === 0 ? 'M' : 'L') + point[0] + ' ' + point[1];
        }).join('');
    },
    getDistance: function (point1, point2) {
        return kpoint.distanceToPoint(point1, point2);
    },
    coordDiff: function (startCoord, endCoord) {
        return _.map(endCoord, function (val, i) {
            return endCoord[i] - startCoord[i];
        });
    },
    snapCoord: function (coord, snap) {
        return _.map(coord, function (val, i) {
            return KhanUtil.roundToNearest(snap[i], val);
        });
    },
    findAngle: function (point1, point2, vertex) {
        if (vertex === undefined) {
            var x = point1[0] - point2[0];
            var y = point1[1] - point2[1];
            if (!x && !y) {
                return 0;
            }
            return (180 + Math.atan2(-y, -x) * 180 / Math.PI + 360) % 360;
        } else {
            return KhanUtil.findAngle(point1, vertex) - KhanUtil.findAngle(point2, vertex);
        }
    },
    graphs: {}
});
_.extend(Graphie.prototype, {
    cartToPolar: cartToPolar,
    polar: polar
});
var labelDirections = {
    'center': [
        -0.5,
        -0.5
    ],
    'above': [
        -0.5,
        -1
    ],
    'above right': [
        0,
        -1
    ],
    'right': [
        0,
        -0.5
    ],
    'below right': [
        0,
        0
    ],
    'below': [
        -0.5,
        0
    ],
    'below left': [
        -1,
        0
    ],
    'left': [
        -1,
        -0.5
    ],
    'above left': [
        -1,
        -1
    ]
};
KhanUtil.createGraphie = function (el) {
    var xScale = 40, yScale = 40, xRange, yRange;
    $(el).css('position', 'relative');
    var raphael = Raphael(el);
    $(el).children('div').css('position', 'absolute');
    var currentStyle = {
        'stroke-width': 2,
        'fill': 'none'
    };
    var scaleVector = function (point) {
        if (typeof point === 'number') {
            return scaleVector([
                point,
                point
            ]);
        }
        var x = point[0], y = point[1];
        return [
            x * xScale,
            y * yScale
        ];
    };
    var scalePoint = function scalePoint(point) {
        if (typeof point === 'number') {
            return scalePoint([
                point,
                point
            ]);
        }
        var x = point[0], y = point[1];
        return [
            (x - xRange[0]) * xScale,
            (yRange[1] - y) * yScale
        ];
    };
    var unscalePoint = function (point) {
        if (typeof point === 'number') {
            return unscalePoint([
                point,
                point
            ]);
        }
        var x = point[0], y = point[1];
        return [
            x / xScale + xRange[0],
            yRange[1] - y / yScale
        ];
    };
    var unscaleVector = function (point) {
        if (typeof point === 'number') {
            return unscaleVector([
                point,
                point
            ]);
        }
        return [
            point[0] / xScale,
            point[1] / yScale
        ];
    };
    var setLabelMargins = function (span, size) {
        var $span = $(span);
        var direction = $span.data('labelDirection');
        $span.css('visibility', '');
        if (typeof direction === 'number') {
            var x = Math.cos(direction);
            var y = Math.sin(direction);
            var scale = Math.min(size[0] / 2 / Math.abs(x), size[1] / 2 / Math.abs(y));
            $span.css({
                marginLeft: -size[0] / 2 + x * scale,
                marginTop: -size[1] / 2 - y * scale
            });
        } else {
            var multipliers = labelDirections[direction || 'center'];
            $span.css({
                marginLeft: Math.round(size[0] * multipliers[0]),
                marginTop: Math.round(size[1] * multipliers[1])
            });
        }
    };
    var svgPath = function (points, alreadyScaled) {
        return $.map(points, function (point, i) {
            if (point === true) {
                return 'z';
            } else {
                var scaled = alreadyScaled ? point : scalePoint(point);
                return (i === 0 ? 'M' : 'L') + KhanUtil.bound(scaled[0]) + ' ' + KhanUtil.bound(scaled[1]);
            }
        }).join('');
    };
    var svgParabolaPath = function (a, b, c) {
        var computeParabola = function (x) {
            return (a * x + b) * x + c;
        };
        if (a === 0) {
            var points = _.map(xRange, function (x) {
                return [
                    x,
                    computeParabola(x)
                ];
            });
            return svgPath(points);
        }
        var xVertex = -b / (2 * a);
        var distToEdge = Math.max(Math.abs(xVertex - xRange[0]), Math.abs(xVertex - xRange[1]));
        var xPoint = xVertex + distToEdge;
        var vertex = [
            xVertex,
            computeParabola(xVertex)
        ];
        var point = [
            xPoint,
            computeParabola(xPoint)
        ];
        var control = [
            vertex[0],
            vertex[1] - (point[1] - vertex[1])
        ];
        var dx = Math.abs(vertex[0] - point[0]);
        var left = [
            vertex[0] - dx,
            point[1]
        ];
        var right = [
            vertex[0] + dx,
            point[1]
        ];
        var points = _.map([
            left,
            control,
            right
        ], scalePoint);
        var values = _.map(_.flatten(points), KhanUtil.bound);
        return 'M' + values[0] + ',' + values[1] + ' Q' + values[2] + ',' + values[3] + ' ' + values[4] + ',' + values[5];
    };
    var svgSinusoidPath = function (a, b, c, d) {
        var quarterPeriod = Math.abs(Math.PI / (2 * b));
        var computeSine = function (x) {
            return a * Math.sin(b * x - c) + d;
        };
        var computeDerivative = function (x) {
            return a * b * Math.cos(c - b * x);
        };
        var coordsForOffset = function (initial, i) {
            var x0 = initial + quarterPeriod * i;
            var x1 = x0 + quarterPeriod;
            var xCoords = [
                x0,
                x0 * 2 / 3 + x1 * 1 / 3,
                x0 * 1 / 3 + x1 * 2 / 3,
                x1
            ];
            var yCoords = [
                computeSine(x0),
                computeSine(x0) + computeDerivative(x0) * (x1 - x0) / 3,
                computeSine(x1) - computeDerivative(x1) * (x1 - x0) / 3,
                computeSine(x1)
            ];
            return _.map(_.zip(xCoords, yCoords), scalePoint);
        };
        var extent = xRange[1] - xRange[0];
        var numQuarterPeriods = Math.ceil(extent / quarterPeriod) + 1;
        var initial = c / b;
        var distToEdge = initial - xRange[0];
        initial -= quarterPeriod * Math.ceil(distToEdge / quarterPeriod);
        var coords = coordsForOffset(initial, 0);
        var path = 'M' + coords[0][0] + ',' + coords[0][1] + ' C' + coords[1][0] + ',' + coords[1][1] + ' ' + coords[2][0] + ',' + coords[2][1] + ' ' + coords[3][0] + ',' + coords[3][1];
        for (var i = 1; i < numQuarterPeriods; i++) {
            coords = coordsForOffset(initial, i);
            path += ' C' + coords[1][0] + ',' + coords[1][1] + ' ' + coords[2][0] + ',' + coords[2][1] + ' ' + coords[3][0] + ',' + coords[3][1];
        }
        return path;
    };
    $.extend(KhanUtil, { svgPath: svgPath });
    var processAttributes = function (attrs) {
        var transformers = {
            scale: function (scale) {
                if (typeof scale === 'number') {
                    scale = [
                        scale,
                        scale
                    ];
                }
                xScale = scale[0];
                yScale = scale[1];
                raphael.setSize((xRange[1] - xRange[0]) * xScale, (yRange[1] - yRange[0]) * yScale);
            },
            clipRect: function (pair) {
                var point = pair[0], size = pair[1];
                point[1] += size[1];
                return { 'clip-rect': scalePoint(point).concat(scaleVector(size)).join(' ') };
            },
            strokeWidth: function (val) {
                return { 'stroke-width': parseFloat(val) };
            },
            rx: function (val) {
                return {
                    rx: scaleVector([
                        val,
                        0
                    ])[0]
                };
            },
            ry: function (val) {
                return {
                    ry: scaleVector([
                        0,
                        val
                    ])[1]
                };
            },
            r: function (val) {
                var scaled = scaleVector([
                    val,
                    val
                ]);
                return {
                    rx: scaled[0],
                    ry: scaled[1]
                };
            }
        };
        var processed = {};
        $.each(attrs || {}, function (key, value) {
            var transformer = transformers[key];
            if (typeof transformer === 'function') {
                $.extend(processed, transformer(value));
            } else {
                var dasherized = key.replace(/([A-Z]+)([A-Z][a-z])/g, '$1-$2').replace(/([a-z\d])([A-Z])/g, '$1-$2').toLowerCase();
                processed[dasherized] = value;
            }
        });
        return processed;
    };
    var addArrowheads = function arrows(path) {
        var type = path.constructor.prototype;
        if (type === Raphael.el) {
            if (path.type === 'path' && typeof path.arrowheadsDrawn === 'undefined') {
                var w = path.attr('stroke-width'), s = 0.6 + 0.4 * w;
                var l = path.getTotalLength();
                var set = raphael.set();
                var head = raphael.path('M-3 4 C-2.75 2.5 0 0.25 0.75 0C0 -0.25 -2.75 -2.5 -3 -4');
                var end = path.getPointAtLength(l - 0.4);
                var almostTheEnd = path.getPointAtLength(l - 0.75 * s);
                var angle = Math.atan2(end.y - almostTheEnd.y, end.x - almostTheEnd.x) * 180 / Math.PI;
                var attrs = path.attr();
                delete attrs.path;
                var subpath = path.getSubpath(0, l - 0.75 * s);
                subpath = raphael.path(subpath).attr(attrs);
                subpath.arrowheadsDrawn = true;
                path.remove();
                head.rotate(angle, 0.75, 0).scale(s, s, 0.75, 0).translate(almostTheEnd.x, almostTheEnd.y).attr(attrs).attr({
                    'stroke-linejoin': 'round',
                    'stroke-linecap': 'round'
                });
                head.arrowheadsDrawn = true;
                set.push(subpath);
                set.push(head);
                return set;
            }
        } else if (type === Raphael.st) {
            for (var i = 0, l = path.items.length; i < l; i++) {
                arrows(path.items[i]);
            }
        }
        return path;
    };
    var drawingTools = {
        circle: function (center, radius) {
            return raphael.ellipse.apply(raphael, scalePoint(center).concat(scaleVector([
                radius,
                radius
            ])));
        },
        rect: function (x, y, width, height) {
            var corner = scalePoint([
                x,
                y + height
            ]);
            var dims = scaleVector([
                width,
                height
            ]);
            return raphael.rect.apply(raphael, corner.concat(dims));
        },
        ellipse: function (center, radii) {
            return raphael.ellipse.apply(raphael, scalePoint(center).concat(scaleVector(radii)));
        },
        fixedEllipse: function (center, radii, maxScale) {
            var scaledPoint = scalePoint(center);
            var scaledRadii = scaleVector(radii);
            var padding = 2;
            var width = 2 * scaledRadii[0] * maxScale + padding;
            var height = 2 * scaledRadii[1] * maxScale + padding;
            var left = scaledPoint[0] - width / 2;
            var top = scaledPoint[1] - height / 2;
            var wrapper = document.createElement('div');
            $(wrapper).css({
                position: 'absolute',
                width: width + 'px',
                height: height + 'px',
                left: left + 'px',
                top: top + 'px'
            });
            var localRaphael = Raphael(wrapper, width, height);
            var visibleShape = localRaphael.ellipse(width / 2, height / 2, scaledRadii[0], scaledRadii[1]);
            return {
                wrapper: wrapper,
                visibleShape: visibleShape
            };
        },
        arc: function (center, radius, startAngle, endAngle, sector) {
            startAngle = (startAngle % 360 + 360) % 360;
            endAngle = (endAngle % 360 + 360) % 360;
            var cent = scalePoint(center);
            var radii = scaleVector(radius);
            var startVector = polar(radius, startAngle);
            var endVector = polar(radius, endAngle);
            var startPoint = scalePoint([
                center[0] + startVector[0],
                center[1] + startVector[1]
            ]);
            var endPoint = scalePoint([
                center[0] + endVector[0],
                center[1] + endVector[1]
            ]);
            var largeAngle = ((endAngle - startAngle) % 360 + 360) % 360 > 180;
            return raphael.path('M' + startPoint.join(' ') + 'A' + radii.join(' ') + ' 0 ' + (largeAngle ? 1 : 0) + ' 0 ' + endPoint.join(' ') + (sector ? 'L' + cent.join(' ') + 'z' : ''));
        },
        path: function (points) {
            var p = raphael.path(svgPath(points));
            p.graphiePath = points;
            return p;
        },
        fixedPath: function (points, center, createPath) {
            points = _.map(points, scalePoint);
            center = center ? scalePoint(center) : null;
            createPath = createPath || svgPath;
            var pathLeft = _.min(_.pluck(points, 0));
            var pathRight = _.max(_.pluck(points, 0));
            var pathTop = _.min(_.pluck(points, 1));
            var pathBottom = _.max(_.pluck(points, 1));
            var padding = [
                4,
                4
            ];
            var extraOffset = [
                pathLeft,
                pathTop
            ];
            points = _.map(points, function (point) {
                return kvector.add(kvector.subtract(point, extraOffset), kvector.scale(padding, 0.5));
            });
            var width = pathRight - pathLeft + padding[0];
            var height = pathBottom - pathTop + padding[1];
            var left = extraOffset[0] - padding[0] / 2;
            var top = extraOffset[1] - padding[1] / 2;
            var wrapper = document.createElement('div');
            $(wrapper).css({
                position: 'absolute',
                width: width + 'px',
                height: height + 'px',
                left: left + 'px',
                top: top + 'px',
                transformOrigin: center ? width / 2 + center[0] + 'px ' + (height / 2 + center[1]) + 'px' : null
            });
            var localRaphael = Raphael(wrapper, width, height);
            var visibleShape = localRaphael.path(createPath(points));
            return {
                wrapper: wrapper,
                visibleShape: visibleShape
            };
        },
        scaledPath: function (points) {
            var p = raphael.path(svgPath(points, true));
            p.graphiePath = points;
            return p;
        },
        line: function (start, end) {
            return this.path([
                start,
                end
            ]);
        },
        parabola: function (a, b, c) {
            return raphael.path(svgParabolaPath(a, b, c));
        },
        fixedLine: function (start, end, thickness) {
            var padding = [
                thickness,
                thickness
            ];
            start = scalePoint(start);
            end = scalePoint(end);
            var extraOffset = [
                Math.min(start[0], end[0]),
                Math.min(start[1], end[1])
            ];
            start = kvector.add(kvector.subtract(start, extraOffset), kvector.scale(padding, 0.5));
            end = kvector.add(kvector.subtract(end, extraOffset), kvector.scale(padding, 0.5));
            var left = extraOffset[0] - padding[0] / 2;
            var top = extraOffset[1] - padding[1] / 2;
            var width = Math.abs(start[0] - end[0]) + padding[0];
            var height = Math.abs(start[1] - end[1]) + padding[1];
            var wrapper = document.createElement('div');
            $(wrapper).css({
                position: 'absolute',
                width: width + 'px',
                height: height + 'px',
                left: left + 'px',
                top: top + 'px',
                transformOrigin: start[0] + 'px ' + start[1] + 'px'
            });
            var localRaphael = Raphael(wrapper, width, height);
            var path = 'M' + start[0] + ' ' + start[1] + ' ' + 'L' + end[0] + ' ' + end[1];
            var visibleShape = localRaphael.path(path);
            visibleShape.graphiePath = [
                start,
                end
            ];
            return {
                wrapper: wrapper,
                visibleShape: visibleShape
            };
        },
        sinusoid: function (a, b, c, d) {
            return raphael.path(svgSinusoidPath(a, b, c, d));
        },
        grid: function (xr, yr) {
            var step = currentStyle.step || [
                1,
                1
            ];
            var set = raphael.set();
            var x = step[0] * Math.ceil(xr[0] / step[0]);
            for (; x <= xr[1]; x += step[0]) {
                set.push(this.line([
                    x,
                    yr[0]
                ], [
                    x,
                    yr[1]
                ]));
            }
            var y = step[1] * Math.ceil(yr[0] / step[1]);
            for (; y <= yr[1]; y += step[1]) {
                set.push(this.line([
                    xr[0],
                    y
                ], [
                    xr[1],
                    y
                ]));
            }
            return set;
        },
        label: function (point, text, direction, latex) {
            latex = typeof latex === 'undefined' || latex;
            var $span = $('<span>').addClass('graphie-label');
            if (!latex) {
                $span.html(text);
            }
            var pad = currentStyle['label-distance'];
            $span.css($.extend({}, currentStyle, {
                position: 'absolute',
                padding: (pad != null ? pad : 7) + 'px'
            })).data('labelDirection', direction).appendTo(el);
            $span.setPosition = function (point) {
                var scaledPoint = scalePoint(point);
                $span.css({
                    left: scaledPoint[0],
                    top: scaledPoint[1]
                });
            };
            $span.setPosition(point);
            var span = $span[0];
            $span.processMath = function (math, force) {
                KhanUtil.processMath(span, math, force, function () {
                    var width = span.scrollWidth;
                    var height = span.scrollHeight;
                    setLabelMargins(span, [
                        width,
                        height
                    ]);
                });
            };
            if (latex) {
                $span.processMath(text, false);
            } else {
                var width = span.scrollWidth;
                var height = span.scrollHeight;
                setLabelMargins(span, [
                    width,
                    height
                ]);
            }
            return $span;
        },
        plotParametric: function (fn, range, shade, fn2) {
            fn2 = fn2 || function (t) {
                return [
                    t,
                    0
                ];
            };
            currentStyle.strokeLinejoin || (currentStyle.strokeLinejoin = 'round');
            currentStyle.strokeLinecap || (currentStyle.strokeLinecap = 'round');
            var min = range[0], max = range[1];
            var step = (max - min) / (currentStyle['plot-points'] || 800);
            if (step === 0) {
                step = 1;
            }
            var paths = raphael.set();
            var points = [];
            var lastDiff = KhanUtil.coordDiff(fn(min), fn2(min));
            var lastFlip = min;
            for (var t = min; t <= max; t += step) {
                var top = fn(t);
                var bottom = fn2(t);
                var diff = KhanUtil.coordDiff(top, bottom);
                if (diff[1] < 0 !== lastDiff[1] < 0 && Math.abs(diff[1] - lastDiff[1]) > 2 * yScale || Math.abs(diff[1]) > 10000000 || isNaN(diff[1])) {
                    if (shade) {
                        points.push(top);
                        for (var u = t - step; u >= lastFlip; u -= step) {
                            points.push(fn2(u));
                        }
                        lastFlip = t;
                    }
                    paths.push(this.path(points));
                    points = [];
                    if (shade) {
                        points.push(top);
                    }
                } else {
                    points.push(top);
                }
                lastDiff = diff;
            }
            if (shade) {
                for (var u = max - step; u >= lastFlip; u -= step) {
                    points.push(fn2(u));
                }
            }
            paths.push(this.path(points));
            return paths;
        },
        plotPolar: function (fn, range) {
            var min = range[0], max = range[1];
            currentStyle['plot-points'] || (currentStyle['plot-points'] = 2 * (max - min) * xScale);
            return this.plotParametric(function (th) {
                return polar(fn(th), th * 180 / Math.PI);
            }, range);
        },
        plot: function (fn, range, swapAxes, shade, fn2) {
            var min = range[0], max = range[1];
            currentStyle['plot-points'] || (currentStyle['plot-points'] = 2 * (max - min) * xScale);
            if (swapAxes) {
                if (fn2) {
                    throw new Error('Can\'t shade area between functions with swapped axes.');
                }
                return this.plotParametric(function (y) {
                    return [
                        fn(y),
                        y
                    ];
                }, range, shade);
            } else {
                if (fn2) {
                    if (shade) {
                        return this.plotParametric(function (x) {
                            return [
                                x,
                                fn(x)
                            ];
                        }, range, shade, function (x) {
                            return [
                                x,
                                fn2(x)
                            ];
                        });
                    } else {
                        throw new Error('fn2 should only be set when \'shade\' is True.');
                    }
                }
                return this.plotParametric(function (x) {
                    return [
                        x,
                        fn(x)
                    ];
                }, range, shade);
            }
        },
        plotPiecewise: function (fnArray, rangeArray) {
            var paths = raphael.set();
            var self = this;
            _.times(fnArray.length, function (i) {
                var fn = fnArray[i];
                var range = rangeArray[i];
                var fnPaths = self.plotParametric(function (x) {
                    return [
                        x,
                        fn(x)
                    ];
                }, range);
                _.each(fnPaths, function (fnPath) {
                    paths.push(fnPath);
                });
            });
            return paths;
        },
        plotEndpointCircles: function (endpointArray) {
            var circles = raphael.set();
            var self = this;
            _.each(endpointArray, function (coord, i) {
                circles.push(self.circle(coord, 0.15));
            });
            return circles;
        },
        plotAsymptotes: function (fn, range) {
            var min = range[0], max = range[1];
            var step = (max - min) / (currentStyle['plot-points'] || 800);
            var asymptotes = raphael.set(), lastVal = fn(min);
            for (var t = min; t <= max; t += step) {
                var funcVal = fn(t);
                if (funcVal < 0 !== lastVal < 0 && Math.abs(funcVal - lastVal) > 2 * yScale) {
                    asymptotes.push(this.line([
                        t,
                        yScale
                    ], [
                        t,
                        -yScale
                    ]));
                }
                lastVal = funcVal;
            }
            return asymptotes;
        }
    };
    var graphie = new Graphie();
    _.extend(graphie, {
        raphael: raphael,
        init: function (options) {
            var scale = options.scale || [
                40,
                40
            ];
            scale = typeof scale === 'number' ? [
                scale,
                scale
            ] : scale;
            xScale = scale[0];
            yScale = scale[1];
            if (options.range == null) {
                return Khan.error('range should be specified in graph init');
            }
            xRange = options.range[0];
            yRange = options.range[1];
            var w = (xRange[1] - xRange[0]) * xScale, h = (yRange[1] - yRange[0]) * yScale;
            raphael.setSize(w, h);
            $(el).css({
                'width': w,
                'height': h
            });
            this.range = options.range;
            this.scale = scale;
            this.dimensions = [
                w,
                h
            ];
            this.xpixels = w;
            this.ypixels = h;
            return this;
        },
        setInterval: function () {
            var intervalID = Function.prototype.apply.call(window.setInterval, window, arguments);
            intervalIDs.push(intervalID);
            return intervalID;
        },
        style: function (attrs, fn) {
            var processed = processAttributes(attrs);
            if (typeof fn === 'function') {
                var oldStyle = currentStyle;
                currentStyle = $.extend({}, currentStyle, processed);
                var result = fn.call(graphie);
                currentStyle = oldStyle;
                return result;
            } else {
                $.extend(currentStyle, processed);
            }
        },
        scalePoint: scalePoint,
        scaleVector: scaleVector,
        unscalePoint: unscalePoint,
        unscaleVector: unscaleVector,
        svgPath: svgPath,
        svgParabolaPath: svgParabolaPath,
        svgSinusoidPath: svgSinusoidPath
    });
    $.each(drawingTools, function (name) {
        graphie[name] = function () {
            var last = arguments[arguments.length - 1];
            var oldStyle = currentStyle;
            var result;
            if (typeof last === 'object' && !_.isArray(last)) {
                currentStyle = $.extend({}, currentStyle, processAttributes(last));
                var rest = [].slice.call(arguments, 0, arguments.length - 1);
                result = drawingTools[name].apply(drawingTools, rest);
            } else {
                currentStyle = $.extend({}, currentStyle);
                result = drawingTools[name].apply(drawingTools, arguments);
            }
            var type = result.constructor.prototype;
            if (type === Raphael.el || type === Raphael.st) {
                result.attr(currentStyle);
                if (currentStyle.arrows) {
                    result = addArrowheads(result);
                }
            } else if (result instanceof $) {
                result.css(currentStyle);
            }
            currentStyle = oldStyle;
            return result;
        };
    });
    graphie.graphInit = function (options) {
        options = options || {};
        $.each(options, function (prop, val) {
            if (!prop.match(/.*Opacity$/) && prop !== 'range' && typeof val === 'number') {
                options[prop] = [
                    val,
                    val
                ];
            }
            if (prop === 'range' || prop === 'gridRange') {
                if (val.constructor === Array) {
                    if (val[0].constructor !== Array) {
                        options[prop] = [
                            [
                                -val[0],
                                val[0]
                            ],
                            [
                                -val[1],
                                val[1]
                            ]
                        ];
                    }
                } else if (typeof val === 'number') {
                    options[prop] = [
                        [
                            -val,
                            val
                        ],
                        [
                            -val,
                            val
                        ]
                    ];
                }
            }
        });
        var range = options.range || [
                [
                    -10,
                    10
                ],
                [
                    -10,
                    10
                ]
            ], gridRange = options.gridRange || options.range, scale = options.scale || [
                20,
                20
            ], grid = options.grid != null ? options.grid : true, gridOpacity = options.gridOpacity || 0.1, gridStep = options.gridStep || [
                1,
                1
            ], axes = options.axes != null ? options.axes : true, axisArrows = options.axisArrows || '', axisOpacity = options.axisOpacity || 1, axisCenter = options.axisCenter || [
                Math.min(Math.max(range[0][0], 0), range[0][1]),
                Math.min(Math.max(range[1][0], 0), range[1][1])
            ], axisLabels = options.axisLabels != null ? options.axisLabels : false, ticks = options.ticks != null ? options.ticks : true, tickStep = options.tickStep || [
                2,
                2
            ], tickLen = options.tickLen || [
                5,
                5
            ], tickOpacity = options.tickOpacity || 1, labels = options.labels || options.labelStep || false, labelStep = options.labelStep || [
                1,
                1
            ], labelOpacity = options.labelOpacity || 1, unityLabels = options.unityLabels || false, labelFormat = options.labelFormat || function (a) {
                return a;
            }, xLabelFormat = options.xLabelFormat || labelFormat, yLabelFormat = options.yLabelFormat || labelFormat, smartLabelPositioning = options.smartLabelPositioning != null ? options.smartLabelPositioning : true, realRange = [
                [
                    range[0][0] - (range[0][0] > 0 ? 1 : 0),
                    range[0][1] + (range[0][1] < 0 ? 1 : 0)
                ],
                [
                    range[1][0] - (range[1][0] > 0 ? 1 : 0),
                    range[1][1] + (range[1][1] < 0 ? 1 : 0)
                ]
            ];
        if (!_.isArray(unityLabels)) {
            unityLabels = [
                unityLabels,
                unityLabels
            ];
        }
        if (smartLabelPositioning) {
            var minusIgnorer = function (lf) {
                return function (a) {
                    return (lf(a) + '').replace(/-(\d)/g, '\\llap{-}$1');
                };
            };
            xLabelFormat = minusIgnorer(xLabelFormat);
            yLabelFormat = minusIgnorer(yLabelFormat);
        }
        this.init({
            range: realRange,
            scale: scale
        });
        if (grid) {
            this.grid(gridRange[0], gridRange[1], {
                stroke: '#000000',
                opacity: gridOpacity,
                step: gridStep
            });
        }
        if (axes) {
            if (axisArrows === '<->' || axisArrows === true) {
                this.style({
                    stroke: '#000000',
                    opacity: axisOpacity,
                    strokeWidth: 2,
                    arrows: '->'
                }, function () {
                    if (range[1][0] < 0 && range[1][1] > 0) {
                        this.path([
                            axisCenter,
                            [
                                gridRange[0][0],
                                axisCenter[1]
                            ]
                        ]);
                        this.path([
                            axisCenter,
                            [
                                gridRange[0][1],
                                axisCenter[1]
                            ]
                        ]);
                    }
                    if (range[0][0] < 0 && range[0][1] > 0) {
                        this.path([
                            axisCenter,
                            [
                                axisCenter[0],
                                gridRange[1][0]
                            ]
                        ]);
                        this.path([
                            axisCenter,
                            [
                                axisCenter[0],
                                gridRange[1][1]
                            ]
                        ]);
                    }
                });
            } else if (axisArrows === '->' || axisArrows === '') {
                this.style({
                    stroke: '#000000',
                    opacity: axisOpacity,
                    strokeWidth: 2,
                    arrows: axisArrows
                }, function () {
                    this.path([
                        [
                            gridRange[0][0],
                            axisCenter[1]
                        ],
                        [
                            gridRange[0][1],
                            axisCenter[1]
                        ]
                    ]);
                    this.path([
                        [
                            axisCenter[0],
                            gridRange[1][0]
                        ],
                        [
                            axisCenter[0],
                            gridRange[1][1]
                        ]
                    ]);
                });
            }
            if (axisLabels && axisLabels.length === 2) {
                this.label([
                    gridRange[0][1],
                    axisCenter[1]
                ], axisLabels[0], 'right');
                this.label([
                    axisCenter[0],
                    gridRange[1][1]
                ], axisLabels[1], 'above');
            }
        }
        if (ticks) {
            this.style({
                stroke: '#000000',
                opacity: tickOpacity,
                strokeWidth: 1
            }, function () {
                var step = gridStep[0] * tickStep[0], len = tickLen[0] / scale[1], start = gridRange[0][0], stop = gridRange[0][1];
                if (range[1][0] < 0 && range[1][1] > 0) {
                    for (var x = step + axisCenter[0]; x <= stop; x += step) {
                        if (x < stop || !axisArrows) {
                            this.line([
                                x,
                                -len + axisCenter[1]
                            ], [
                                x,
                                len + axisCenter[1]
                            ]);
                        }
                    }
                    for (var x = -step + axisCenter[0]; x >= start; x -= step) {
                        if (x > start || !axisArrows) {
                            this.line([
                                x,
                                -len + axisCenter[1]
                            ], [
                                x,
                                len + axisCenter[1]
                            ]);
                        }
                    }
                }
                step = gridStep[1] * tickStep[1];
                len = tickLen[1] / scale[0];
                start = gridRange[1][0];
                stop = gridRange[1][1];
                if (range[0][0] < 0 && range[0][1] > 0) {
                    for (var y = step + axisCenter[1]; y <= stop; y += step) {
                        if (y < stop || !axisArrows) {
                            this.line([
                                -len + axisCenter[0],
                                y
                            ], [
                                len + axisCenter[0],
                                y
                            ]);
                        }
                    }
                    for (var y = -step + axisCenter[1]; y >= start; y -= step) {
                        if (y > start || !axisArrows) {
                            this.line([
                                -len + axisCenter[0],
                                y
                            ], [
                                len + axisCenter[0],
                                y
                            ]);
                        }
                    }
                }
            });
        }
        if (labels) {
            this.style({
                stroke: '#000000',
                opacity: labelOpacity
            }, function () {
                var step = gridStep[0] * tickStep[0] * labelStep[0], start = gridRange[0][0], stop = gridRange[0][1], xAxisPosition = axisCenter[0] < 0 ? 'above' : 'below', yAxisPosition = axisCenter[0] < 0 ? 'right' : 'left', xShowZero = axisCenter[0] === 0 && axisCenter[1] !== 0, yShowZero = axisCenter[0] !== 0 && axisCenter[1] === 0, axisOffCenter = axisCenter[0] !== 0 || axisCenter[1] !== 0, showUnityX = unityLabels[0] || axisOffCenter, showUnityY = unityLabels[1] || axisOffCenter;
                for (var x = (xShowZero ? 0 : step) + axisCenter[0]; x <= stop; x += step) {
                    if (x < stop || !axisArrows) {
                        this.label([
                            x,
                            axisCenter[1]
                        ], xLabelFormat(x), xAxisPosition);
                    }
                }
                for (var x = -step * (showUnityX ? 1 : 2) + axisCenter[0]; x >= start; x -= step) {
                    if (x > start || !axisArrows) {
                        this.label([
                            x,
                            axisCenter[1]
                        ], xLabelFormat(x), xAxisPosition);
                    }
                }
                step = gridStep[1] * tickStep[1] * labelStep[1];
                start = gridRange[1][0];
                stop = gridRange[1][1];
                for (var y = (yShowZero ? 0 : step) + axisCenter[1]; y <= stop; y += step) {
                    if (y < stop || !axisArrows) {
                        this.label([
                            axisCenter[0],
                            y
                        ], yLabelFormat(y), yAxisPosition);
                    }
                }
                for (var y = -step * (showUnityY ? 1 : 2) + axisCenter[1]; y >= start; y -= step) {
                    if (y > start || !axisArrows) {
                        this.label([
                            axisCenter[0],
                            y
                        ], yLabelFormat(y), yAxisPosition);
                    }
                }
            });
        }
    };
    return graphie;
};
$.fn.graphie = function (problem) {
    if (Khan.query.nographie != null) {
        return;
    }
    return this.find('.graphie, script[type=\'text/graphie\']').addBack().filter('.graphie, script[type=\'text/graphie\']').each(function () {
        var code = $(this).text(), graphie;
        if ($(this).data('graphie') != null) {
            return;
        }
        $(this).empty();
        if ($(this).data('update')) {
            var id = $(this).data('update');
            $(this).remove();
            var area = $('#problemarea').add(problem);
            graphie = area.find('#' + id + '.graphie').data('graphie');
        } else {
            var el = this;
            if ($(this).filter('script')[0] != null) {
                el = $('<div>').addClass('graphie').attr('id', $(this).attr('id')).insertAfter(this)[0];
                $(this).remove();
            }
            graphie = KhanUtil.createGraphie(el);
            $(el).data('graphie', graphie);
            var id = $(el).attr('id');
            if (id) {
                KhanUtil.graphs[id] = graphie;
            }
        }
        if (typeof graphie.graph === 'undefined') {
            graphie.graph = {};
        }
        code = '(function() {' + code + '\n})()';
        KhanUtil.currentGraph = graphie;
        $.tmpl.getVAR(code, graphie);
    }).end();
};
$.fn.graphieCleanup = function (problem) {
    cleanupIntervals();
};
},{"./kpoint.js":8,"./kvector.js":9,"./tex.js":10,"./tmpl.js":11}],5:[function(require,module,exports){
var kpoint = require('./kpoint.js');
var knumber = require('./knumber.js');
var kline = KhanUtil.kline = {
    distanceToPoint: function (line, point) {
        return kpoint.distanceToLine(point, line);
    },
    reflectPoint: function (line, point) {
        return kpoint.reflectOverLine(point, line);
    },
    midpoint: function (line) {
        return [
            (line[0][0] + line[1][0]) / 2,
            (line[0][1] + line[1][1]) / 2
        ];
    },
    equal: function (line1, line2, tolerance) {
        var x1 = line1[0][0];
        var y1 = line1[0][1];
        var x2 = line1[1][0];
        var y2 = line1[1][1];
        return _.every(line2, function (point) {
            var x3 = point[0];
            var y3 = point[1];
            var area = 1 / 2 * Math.abs(x1 * y2 + x2 * y3 + x3 * y1 - x2 * y1 - x3 * y2 - x1 * y3);
            return knumber.equal(area, 0, tolerance);
        });
    },
    intersect: function (px, py, rx, ry, qx, qy, sx, sy) {
        function cross(vx, vy, wx, wy) {
            return vx * wy - vy * wx;
        }
        if (cross(rx, ry, sx, sy) === 0) {
            return cross(qx - px, qy - py, rx, ry) === 0;
        } else {
            var t = cross(qx - px, qy - py, sx, sy) / cross(rx, ry, sx, sy);
            var u = cross(qx - px, qy - py, rx, ry) / cross(rx, ry, sx, sy);
            return 0 <= t && t <= 1 && 0 <= u && u <= 1;
        }
    }
};
module.exports = kline;
},{"./knumber.js":7,"./kpoint.js":8}],6:[function(require,module,exports){
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
},{"./expressions.js":2}],7:[function(require,module,exports){
var DEFAULT_TOLERANCE = 1e-9;
var EPSILON = Math.pow(2, -42);
var knumber = KhanUtil.knumber = {
    DEFAULT_TOLERANCE: DEFAULT_TOLERANCE,
    EPSILON: EPSILON,
    is: function (x) {
        return _.isNumber(x) && !_.isNaN(x);
    },
    equal: function (x, y, tolerance) {
        if (x == null || y == null) {
            return x === y;
        }
        if (tolerance == null) {
            tolerance = DEFAULT_TOLERANCE;
        }
        return Math.abs(x - y) < tolerance;
    },
    sign: function (x, tolerance) {
        return knumber.equal(x, 0, tolerance) ? 0 : Math.abs(x) / x;
    },
    round: function (num, precision) {
        var factor = Math.pow(10, precision);
        return Math.round(num * factor) / factor;
    },
    roundTo: function (num, increment) {
        return Math.round(num / increment) * increment;
    },
    floorTo: function (num, increment) {
        return Math.floor(num / increment) * increment;
    },
    ceilTo: function (num, increment) {
        return Math.ceil(num / increment) * increment;
    },
    isInteger: function (num, tolerance) {
        return knumber.equal(Math.round(num), num, tolerance);
    },
    toFraction: function (decimal, tolerance, max_denominator) {
        max_denominator = max_denominator || 1000;
        tolerance = tolerance || EPSILON;
        var n = [
                1,
                0
            ], d = [
                0,
                1
            ];
        var a = Math.floor(decimal);
        var rem = decimal - a;
        while (d[0] <= max_denominator) {
            if (knumber.equal(n[0] / d[0], decimal, tolerance)) {
                return [
                    n[0],
                    d[0]
                ];
            }
            n = [
                a * n[0] + n[1],
                n[0]
            ];
            d = [
                a * d[0] + d[1],
                d[0]
            ];
            a = Math.floor(1 / rem);
            rem = 1 / rem - a;
        }
        return [
            decimal,
            1
        ];
    }
};
module.exports = knumber;
},{}],8:[function(require,module,exports){
var kvector = require('./kvector.js');
var knumber = require('./knumber.js');
var kpoint = KhanUtil.kpoint = {
    rotateRad: function (point, theta, center) {
        if (center === undefined) {
            return kvector.rotateRad(point, theta);
        } else {
            return kvector.add(center, kvector.rotateRad(kvector.subtract(point, center), theta));
        }
    },
    rotateDeg: function (point, theta, center) {
        if (center === undefined) {
            return kvector.rotateDeg(point, theta);
        } else {
            return kvector.add(center, kvector.rotateDeg(kvector.subtract(point, center), theta));
        }
    },
    distanceToPoint: function (point1, point2) {
        return kvector.length(kvector.subtract(point1, point2));
    },
    distanceToLine: function (point, line) {
        var lv = kvector.subtract(line[1], line[0]);
        var pv = kvector.subtract(point, line[0]);
        var projectedPv = kvector.projection(pv, lv);
        var distancePv = kvector.subtract(projectedPv, pv);
        return kvector.length(distancePv);
    },
    reflectOverLine: function (point, line) {
        var lv = kvector.subtract(line[1], line[0]);
        var pv = kvector.subtract(point, line[0]);
        var projectedPv = kvector.projection(pv, lv);
        var reflectedPv = kvector.subtract(kvector.scale(projectedPv, 2), pv);
        return kvector.add(line[0], reflectedPv);
    },
    compare: function (point1, point2, equalityTolerance) {
        if (point1.length !== point2.length) {
            return point1.length - point2.length;
        }
        for (var i = 0; i < point1.length; i++) {
            if (!knumber.equal(point1[i], point2[i], equalityTolerance)) {
                return point1[i] - point2[i];
            }
        }
        return 0;
    }
};
_.extend(kpoint, {
    is: kvector.is,
    addVector: kvector.add,
    addVectors: kvector.add,
    subtractVector: kvector.subtract,
    equal: kvector.equal,
    polarRadFromCart: kvector.polarRadFromCart,
    polarDegFromCart: kvector.polarDegFromCart,
    cartFromPolarRad: kvector.cartFromPolarRad,
    cartFromPolarDeg: kvector.cartFromPolarDeg,
    round: kvector.round,
    roundTo: kvector.roundTo,
    floorTo: kvector.floorTo,
    ceilTo: kvector.ceilTo
});
module.exports = kpoint;
},{"./knumber.js":7,"./kvector.js":9}],9:[function(require,module,exports){
var knumber = require('./knumber.js');
function arraySum(array) {
    return _.reduce(array, function (memo, arg) {
        return memo + arg;
    }, 0);
}
function arrayProduct(array) {
    return _.reduce(array, function (memo, arg) {
        return memo * arg;
    }, 1);
}
var kvector = KhanUtil.kvector = {
    is: function (vec, length) {
        if (!_.isArray(vec)) {
            return false;
        }
        if (length !== undefined && vec.length !== length) {
            return false;
        }
        return _.all(vec, knumber.is);
    },
    normalize: function (v) {
        return kvector.scale(v, 1 / kvector.length(v));
    },
    length: function (v) {
        return Math.sqrt(kvector.dot(v, v));
    },
    dot: function (a, b) {
        var vecs = _.toArray(arguments);
        var zipped = _.zip.apply(_, vecs);
        var multiplied = _.map(zipped, arrayProduct);
        return arraySum(multiplied);
    },
    add: function () {
        var points = _.toArray(arguments);
        var zipped = _.zip.apply(_, points);
        return _.map(zipped, arraySum);
    },
    subtract: function (v1, v2) {
        return _.map(_.zip(v1, v2), function (dim) {
            return dim[0] - dim[1];
        });
    },
    negate: function (v) {
        return _.map(v, function (x) {
            return -x;
        });
    },
    scale: function (v1, scalar) {
        return _.map(v1, function (x) {
            return x * scalar;
        });
    },
    equal: function (v1, v2, tolerance) {
        return _.all(_.zip(v1, v2), function (pair) {
            return knumber.equal(pair[0], pair[1], tolerance);
        });
    },
    codirectional: function (v1, v2, tolerance) {
        if (knumber.equal(kvector.length(v1), 0, tolerance) || knumber.equal(kvector.length(v2), 0, tolerance)) {
            return true;
        }
        v1 = kvector.normalize(v1);
        v2 = kvector.normalize(v2);
        return kvector.equal(v1, v2, tolerance);
    },
    collinear: function (v1, v2, tolerance) {
        return kvector.codirectional(v1, v2, tolerance) || kvector.codirectional(v1, kvector.negate(v2), tolerance);
    },
    polarRadFromCart: function (v) {
        var radius = kvector.length(v);
        var theta = Math.atan2(v[1], v[0]);
        if (theta < 0) {
            theta += 2 * Math.PI;
        }
        return [
            radius,
            theta
        ];
    },
    polarDegFromCart: function (v) {
        var polar = kvector.polarRadFromCart(v);
        return [
            polar[0],
            polar[1] * 180 / Math.PI
        ];
    },
    cartFromPolarRad: function (radius, theta) {
        if (_.isUndefined(theta)) {
            theta = radius[1];
            radius = radius[0];
        }
        return [
            radius * Math.cos(theta),
            radius * Math.sin(theta)
        ];
    },
    cartFromPolarDeg: function (radius, theta) {
        if (_.isUndefined(theta)) {
            theta = radius[1];
            radius = radius[0];
        }
        return kvector.cartFromPolarRad(radius, theta * Math.PI / 180);
    },
    rotateRad: function (v, theta) {
        var polar = kvector.polarRadFromCart(v);
        var angle = polar[1] + theta;
        return kvector.cartFromPolarRad(polar[0], angle);
    },
    rotateDeg: function (v, theta) {
        var polar = kvector.polarDegFromCart(v);
        var angle = polar[1] + theta;
        return kvector.cartFromPolarDeg(polar[0], angle);
    },
    angleRad: function (v1, v2) {
        return Math.acos(kvector.dot(v1, v2) / (kvector.length(v1) * kvector.length(v2)));
    },
    angleDeg: function (v1, v2) {
        return kvector.angleRad(v1, v2) * 180 / Math.PI;
    },
    projection: function (v1, v2) {
        var scalar = kvector.dot(v1, v2) / kvector.dot(v2, v2);
        return kvector.scale(v2, scalar);
    },
    round: function (vec, precision) {
        return _.map(vec, function (elem, i) {
            return knumber.round(elem, precision[i] || precision);
        });
    },
    roundTo: function (vec, increment) {
        return _.map(vec, function (elem, i) {
            return knumber.roundTo(elem, increment[i] || increment);
        });
    },
    floorTo: function (vec, increment) {
        return _.map(vec, function (elem, i) {
            return knumber.floorTo(elem, increment[i] || increment);
        });
    },
    ceilTo: function (vec, increment) {
        return _.map(vec, function (elem, i) {
            return knumber.ceilTo(elem, increment[i] || increment);
        });
    }
};
module.exports = kvector;
},{"./knumber.js":7}],10:[function(require,module,exports){
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
},{}],11:[function(require,module,exports){
var crc32 = require('./crc32.js');
var localMode;
var VARS = {};
$.tmpl = {
    DATA_ENSURE_LOOPS: 0,
    attr: {
        'data-ensure': function (elem, ensure) {
            return function (elem) {
                var result = !!(ensure && $.tmpl.getVAR(ensure));
                if (!result) {
                    if ($.tmpl.DATA_ENSURE_LOOPS++ > 10000 && localMode) {
                        alert('unsatisfiable data-ensure?');
                        return true;
                    }
                }
                return result;
            };
        },
        'data-if': function (elem, value) {
            var $elem = $(elem);
            value = value && $.tmpl.getVAR(value);
            var $nextElem = $elem.next();
            if ($nextElem.data('lastCond') === undefined) {
                $nextElem.data('lastCond', value);
            }
            if (!value) {
                return [];
            }
        },
        'data-else-if': function (elem, value) {
            var $elem = $(elem);
            var lastCond = $elem.data('lastCond');
            value = !lastCond && value && $.tmpl.getVAR(value);
            var $nextElem = $elem.next();
            if ($nextElem.data('lastCond') === undefined) {
                $nextElem.data('lastCond', lastCond || value);
            }
            if (!value) {
                return [];
            }
        },
        'data-else': function (elem) {
            var $elem = $(elem);
            if ($elem.data('lastCond')) {
                return [];
            }
        },
        'data-each': function (elem, value) {
            var match;
            $(elem).removeAttr('data-each');
            if (match = /^(.+) times(?: as (\w+))?$/.exec(value)) {
                var times = $.tmpl.getVAR(match[1]);
                return {
                    items: $.map(new Array(times), function (e, i) {
                        return i;
                    }),
                    value: match[2],
                    oldValue: VARS[match[2]]
                };
            } else if (match = /^(.*?)(?: as (?:(\w+), )?(\w+))?$/.exec(value)) {
                return {
                    items: $.tmpl.getVAR(match[1]),
                    value: match[3],
                    pos: match[2],
                    oldValue: VARS[match[3]],
                    oldPos: VARS[match[2]]
                };
            }
        },
        'data-unwrap': function (elem) {
            return $(elem).contents();
        },
        'data-video-hint': function (elem) {
            var youtubeIds = $(elem).data('youtube-id');
            if (!youtubeIds) {
                return;
            }
            youtubeIds = youtubeIds.split(/,\s*/);
            var author = $(elem).data('video-hint-author') || 'Sal';
            var msg = $._('Watch %(author)s work through a very similar ' + 'problem:', { author: author });
            var preface = $('<p>').text(msg);
            var wrapper = $('<div>', { 'class': 'video-hint' });
            wrapper.append(preface);
            _.each(youtubeIds, function (youtubeId) {
                var href = 'http://www.khanacademy.org/embed_video?v=' + youtubeId;
                var iframe = $('<iframe>').attr({
                    'frameborder': '0',
                    'scrolling': 'no',
                    'width': '100%',
                    'height': '360px',
                    'src': href
                });
                wrapper.append(iframe);
            });
            return wrapper;
        }
    },
    type: {
        'var': function (elem, value) {
            if (!value && $(elem).children().length > 0) {
                return function (elem) {
                    return $.tmpl.type['var'](elem, elem.innerHTML);
                };
            }
            value = value || $.tmpl.getVAR(elem);
            var name = elem.id;
            if (name) {
                var setVAR = function (name, value) {
                    if (KhanUtil[name]) {
                        Khan.error('Defining variable \'' + name + '\' overwrites utility property of same name.');
                    }
                    VARS[name] = value;
                };
                if (name.indexOf(',') !== -1) {
                    var parts = name.split(/\s*,\s*/);
                    $.each(parts, function (i, part) {
                        if (part.length > 0) {
                            setVAR(part, value[i]);
                        }
                    });
                } else {
                    setVAR(name, value);
                }
            } else {
                if (value == null) {
                    return [];
                } else {
                    var div = $('<div>');
                    var html = div.append(value + ' ').html();
                    return div.html(html.slice(0, -1)).contents();
                }
            }
        }
    },
    getVAR: function (elem, ctx) {
        var code = elem.nodeName ? $(elem).text() : elem;
        if (ctx == null) {
            ctx = {};
        }
        function doEval() {
            with (Math) {
                with (KhanUtil) {
                    with (ctx) {
                        with (VARS) {
                            return eval('(function() { return (' + code + '); })()');
                        }
                    }
                }
            }
        }
        if (Khan.query.debug != null) {
            return doEval();
        } else {
            try {
                return doEval();
            } catch (e) {
                var info;
                if (elem.nodeName) {
                    info = elem.nodeName.toLowerCase();
                    if (elem.id != null && elem.id.length > 0) {
                        info += '#' + elem.id;
                    }
                } else {
                    info = JSON.stringify(code);
                }
                Khan.error('Error while evaluating ' + info, e);
            }
        }
    },
    getVarsHash: function () {
        return crc32(JSON.stringify($.map(VARS, function (value, key) {
            return [
                key,
                String(value)
            ];
        })));
    }
};
if (typeof KhanUtil !== 'undefined') {
    KhanUtil.tmpl = $.tmpl;
}
$.fn.tmplLoad = function (problem, info) {
    VARS = {};
    $.tmpl.DATA_ENSURE_LOOPS = 0;
    localMode = info.localMode;
    if (localMode) {
        $.tmpl.VARS = VARS;
    }
};
$.fn.tmpl = function () {
    for (var i = 0, l = this.length; i < l; i++) {
        traverse(this[i]);
    }
    return this;
    function traverse(elem) {
        var post = [], child = elem.childNodes, ret = process(elem, post);
        if (ret === false) {
            return traverse(elem);
        } else if (ret === undefined) {
        } else if (typeof ret === 'object' && typeof ret.length !== 'undefined') {
            if (elem.parentNode) {
                $.each(ret, function (i, rep) {
                    if (rep.nodeType) {
                        elem.parentNode.insertBefore(rep, elem);
                    }
                });
                $.each(ret, function (i, rep) {
                    traverse(rep);
                });
                elem.parentNode.removeChild(elem);
            }
            return null;
        } else if (ret.items) {
            var origParent = elem.parentNode, origNext = elem.nextSibling;
            $.each(ret.items, function (pos, value) {
                if (ret.value) {
                    VARS[ret.value] = value;
                }
                if (ret.pos) {
                    VARS[ret.pos] = pos;
                }
                var clone = $(elem).clone(true).removeAttr('data-each').removeData('each')[0];
                var conditionals = [
                    'data-if',
                    'data-else-if',
                    'data-else'
                ];
                var declarations = '';
                declarations += ret.pos ? 'var ' + ret.pos + ' = ' + JSON.stringify(pos) + ';' : '';
                declarations += ret.value ? 'var ' + ret.value + ' = ' + JSON.stringify(value) + ';' : '';
                for (var i = 0; i < conditionals.length; i++) {
                    var conditional = conditionals[i];
                    $(clone).find('[' + conditional + ']').each(function () {
                        var code = $(this).attr(conditional);
                        code = '(function() { ' + declarations + ' return ' + code + ' })()';
                        $(this).attr(conditional, code);
                    });
                }
                $(clone).find('.graphie').addBack().filter('.graphie').each(function () {
                    var code = $(this).text();
                    $(this).text(declarations + code);
                });
                if (origNext) {
                    origParent.insertBefore(clone, origNext);
                } else {
                    origParent.appendChild(clone);
                }
                traverse(clone);
            });
            if (ret.value) {
                VARS[ret.value] = ret.oldValue;
            }
            if (ret.pos) {
                VARS[ret.pos] = ret.oldPos;
            }
            $(elem).remove();
            return null;
        }
        for (var i = 0; i < child.length; i++) {
            if (child[i].nodeType === 1 && traverse(child[i]) === null) {
                i--;
            }
        }
        for (var i = 0, l = post.length; i < l; i++) {
            if (post[i](elem) === false) {
                return traverse(elem);
            }
        }
        return elem;
    }
    function process(elem, post) {
        var ret, $elem = $(elem);
        for (var attr in $.tmpl.attr) {
            if ($.tmpl.attr.hasOwnProperty(attr)) {
                var value;
                if (/^data-/.test(attr)) {
                    value = $elem.data(attr.replace(/^data-/, ''));
                } else {
                    value = $elem.attr(attr);
                }
                if (value !== undefined) {
                    ret = $.tmpl.attr[attr](elem, value);
                    if (typeof ret === 'function') {
                        post.push(ret);
                    } else if (ret !== undefined) {
                        return ret;
                    }
                }
            }
        }
        var type = elem.nodeName.toLowerCase();
        if ($.tmpl.type[type] != null) {
            ret = $.tmpl.type[type](elem);
            if (typeof ret === 'function') {
                post.push(ret);
            }
        }
        return ret;
    }
};
$.extend($.expr[':'], {
    inherited: function (el) {
        return $(el).data('inherited');
    }
});
$.fn.extend({
    tmplApply: function (options) {
        options = options || {};
        var attribute = options.attribute || 'id', defaultApply = options.defaultApply || 'replace', parent = {};
        return this.each(function () {
            var $this = $(this), name = $this.attr(attribute), hint = $this.data('apply') && !$this.data('apply').indexOf('hint');
            if (name) {
                if (name in parent && !hint) {
                    parent[name] = $.tmplApplyMethods[$this.data('apply') || defaultApply].call(parent[name], this);
                    if (parent[name] == null) {
                        delete parent[name];
                    }
                } else if ($this.closest(':inherited').length > 0) {
                    parent[name] = this;
                }
            }
        });
    }
});
$.extend({
    tmplApplyMethods: {
        remove: function (elem) {
            $(this).remove();
            $(elem).remove();
        },
        replace: function (elem) {
            $(this).replaceWith(elem);
            return elem;
        },
        splice: function (elem) {
            $(this).replaceWith($(elem).contents());
        },
        append: function (elem) {
            $(this).append(elem);
            return this;
        },
        appendContents: function (elem) {
            $(this).append($(elem).contents());
            $(elem).remove();
            return this;
        },
        prepend: function (elem) {
            $(this).prepend(elem);
            return this;
        },
        prependContents: function (elem) {
            $(this).prepend($(elem).contents());
            $(elem).remove();
            return this;
        },
        before: function (elem) {
            $(this).before(elem);
            return this;
        },
        beforeContents: function (elem) {
            $(this).before($(elem).contents());
            $(elem).remove();
            return this;
        },
        after: function (elem) {
            $(this).after(elem);
            return this;
        },
        afterContents: function (elem) {
            $(this).after($(elem).contents());
            $(elem).remove();
            return this;
        },
        appendVars: function (elem) {
            var parentEnsure = $(this).data('ensure') || '1';
            var childEnsure = $(elem).data('ensure') || '1';
            $(this).data('ensure', '(' + parentEnsure + ') && (' + childEnsure + ')');
            return $.tmplApplyMethods.appendContents.call(this, elem);
        },
        prependVars: function (elem) {
            var parentEnsure = $(this).data('ensure') || '1';
            var childEnsure = $(elem).data('ensure') || '1';
            $(this).data('ensure', '(' + childEnsure + ') && (' + parentEnsure + ')');
            return $.tmplApplyMethods.prependContents.call(this, elem);
        }
    }
});
},{"./crc32.js":1}]},{},[3]);
