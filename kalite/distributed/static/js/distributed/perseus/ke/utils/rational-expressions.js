(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
$.extend(KhanUtil, {
    getPermutations: function (arr) {
        var permArr = [];
        var usedChars = [];
        function permute(input) {
            for (var i = 0; i < input.length; i++) {
                var term = input.splice(i, 1)[0];
                usedChars.push(term);
                if (input.length === 0) {
                    permArr.push(usedChars.slice());
                }
                permute(input);
                input.splice(i, 0, term);
                usedChars.pop();
            }
            return permArr;
        }
        return permute(arr);
    },
    writeExpressionFraction: function (numerator, denominator) {
        if (denominator.toString() === '1') {
            return numerator.toString();
        }
        if (denominator.toString() === '-1') {
            return numerator.multiply(-1).toString();
        }
        if (numerator.isNegative()) {
            return '-\\dfrac{' + numerator.multiply(-1).toString() + '}{' + denominator.toString() + '}';
        }
        if (denominator.isNegative()) {
            return '-\\dfrac{' + numerator.toString() + '}{' + denominator.multiply(-1).toString() + '}';
        }
        return '\\dfrac{' + numerator.toString() + '}{' + denominator.toString() + '}';
    },
    Term: function (coefficient, variables, degree) {
        this.coefficient = coefficient;
        this.variables = {};
        if (degree === undefined) {
            degree = 1;
        }
        if (typeof variables === 'string') {
            for (var i = 0; i < variables.length; i++) {
                this.variables[variables.charAt(i)] = degree;
            }
        } else if (variables !== undefined) {
            this.variables = variables;
        }
        this.variableString = '';
        for (var vari in this.variables) {
            if (this.variables[vari] !== 0) {
                this.variableString += vari + this.variables[vari];
            } else {
                delete this.variables[vari];
            }
        }
        this.isNegative = function () {
            return this.coefficient < 0;
        };
        this.add = function (expression) {
            var copy = [
                this.coefficient,
                this.variables
            ];
            if (expression instanceof KhanUtil.RationalExpression) {
                return expression.add(this);
            } else if (expression instanceof KhanUtil.Term) {
                return new KhanUtil.RationalExpression([
                    copy,
                    [
                        expression.coefficient,
                        expression.variables
                    ]
                ]);
            } else {
                return new KhanUtil.RationalExpression([
                    copy,
                    expression
                ]);
            }
        };
        this.isOne = function () {
            return this.toString() === '1';
        };
        this.evaluate = function (values) {
            var value = this.coefficient;
            if (typeof values === 'number') {
                _.each(this.variables, function (v) {
                    value *= Math.pow(values, v);
                });
            } else {
                _.each(this.variables, function (v, i) {
                    value *= Math.pow(values[i], v);
                });
            }
            return value;
        };
        this.multiply = function (term) {
            if (term instanceof KhanUtil.RationalExpression) {
                return term.multiply(this);
            }
            var coefficient = this.coefficient;
            var variables = _.clone(this.variables);
            if (typeof term === 'number') {
                coefficient *= term;
            } else {
                coefficient *= term.coefficient;
                for (var i in term.variables) {
                    if (variables[i] != null) {
                        variables[i] += term.variables[i];
                    } else {
                        variables[i] = term.variables[i];
                    }
                }
            }
            return new KhanUtil.Term(coefficient, variables);
        };
        this.divide = function (term) {
            var coefficient = this.coefficient;
            var variables = _.clone(this.variables);
            if (typeof term === 'number') {
                coefficient /= term;
            } else {
                coefficient /= term.coefficient;
                for (var i in term.variables) {
                    if (variables[i]) {
                        variables[i] -= term.variables[i];
                    } else {
                        variables[i] = -term.variables[i];
                    }
                }
            }
            return new KhanUtil.Term(coefficient, variables);
        };
        this.getGCD = function (expression) {
            if (expression instanceof KhanUtil.RationalExpression) {
                return expression.getGCD(this);
            }
            if (typeof expression === 'number') {
                return KhanUtil.getGCD(this.coefficient, expression);
            }
            var coefficient = KhanUtil.getGCD(this.coefficient, expression.coefficient);
            var variables = {};
            for (var i in this.variables) {
                if (expression.variables[i]) {
                    variables[i] = Math.min(this.variables[i], expression.variables[i]);
                }
            }
            return new KhanUtil.Term(coefficient, variables);
        };
        this.toString = function (includeSign) {
            if (this.coefficient === 0) {
                return '';
            }
            var s = '';
            if (includeSign) {
                s += this.coefficient >= 0 ? ' + ' : ' - ';
            } else if (this.coefficient < 0) {
                s += '-';
            }
            var coefficient = Math.abs(this.coefficient);
            if (!(coefficient === 1 && this.variableString !== '')) {
                s += coefficient;
            }
            _.each(this.variables, function (degree, i) {
                if (degree === 0) {
                    return;
                }
                s += i;
                if (degree !== 1) {
                    s += '^' + degree;
                }
            });
            return s;
        };
        this.toStringFactored = function () {
            return this.toString();
        };
        this.getEvaluateString = function (values, includeSign, color) {
            var s = '';
            if (includeSign) {
                s += this.coefficient >= 0 ? ' + ' : ' - ';
            } else if (this.coefficient < 0) {
                s += '-';
            }
            var coefficient = Math.abs(this.coefficient);
            if (!(coefficient === 1 && this.variableString !== '')) {
                s += coefficient;
                if (this.variableString !== '') {
                    s += '\\cdot';
                }
            }
            _.each(this.variables, function (degree, i) {
                var value = typeof values === 'number' ? values : values[i];
                if (color !== undefined) {
                    value = '\\' + color + '{' + value + '}';
                }
                s += value < 0 || degree === 1 ? value : '(' + value + ')^' + degree;
            });
            return s;
        };
        this.regex = function () {
            return '^' + this.regexForExpression() + '$';
        };
        this.regexForExpression = function (includeSign) {
            if (this.coefficient === 0) {
                return '';
            }
            var regex;
            if (this.coefficient < 0) {
                regex = includeSign ? '[-\\u2212]\\s*' : '\\s*[-\\u2212]\\s*';
            } else {
                regex = includeSign ? '\\+\\s*' : '\\s*';
            }
            if (!(Math.abs(this.coefficient) === 1 && this.variableString !== '')) {
                regex += Math.abs(this.coefficient);
            }
            var variable_array = [];
            for (var vari in this.variables) {
                if (degree !== 0) {
                    variable_array.push([
                        vari,
                        this.variables[vari]
                    ]);
                }
            }
            if (variable_array.length > 1) {
                var permutations = KhanUtil.getPermutations(variable_array);
                regex += '(?:';
                for (var p = 0; p < permutations.length; p++) {
                    var variables = permutations[p];
                    regex += '(?:';
                    for (var i = 0; i < variables.length; i++) {
                        var vari = variables[i][0];
                        var degree = variables[i][1];
                        regex += degree > 1 ? vari + '\\s*\\^\\s*' + degree : vari;
                    }
                    regex += p < permutations.length - 1 ? ')|' : ')';
                }
                regex += ')';
            } else if (variable_array.length === 1) {
                var vari = variable_array[0][0];
                var degree = variable_array[0][1];
                regex += degree > 1 ? vari + '\\s*\\^\\s*' + degree : vari;
            }
            return regex + '\\s*';
        };
    },
    RationalExpression: function (terms) {
        this.terms = [];
        for (var i = 0; i < terms.length; i++) {
            var term = terms[i];
            var newTerm;
            if (typeof term === 'number') {
                newTerm = new KhanUtil.Term(term);
            } else if (term instanceof KhanUtil.Term) {
                newTerm = new KhanUtil.Term(term.coefficient, term.variables);
            } else {
                newTerm = new KhanUtil.Term(term[0], term[1]);
            }
            if (newTerm.coefficient !== 0) {
                this.terms.push(newTerm);
            }
        }
        this.getCoefficient = function (variable) {
            var coefficient = 0;
            for (var i = 0; i < this.terms.length; i++) {
                if (this.terms[i].variableString === variable) {
                    coefficient += this.terms[i].coefficient;
                }
            }
            return coefficient;
        };
        this.combineLikeTerms = function () {
            var variables = {};
            for (var i = 0; i < this.terms.length; i++) {
                var term = this.terms[i];
                var s = term.variableString;
                if (variables[s]) {
                    variables[s].coefficient += term.coefficient;
                } else {
                    variables[s] = term;
                }
            }
            this.terms = [];
            for (var v in variables) {
                if (variables[v].coefficient !== 0) {
                    this.terms.push(variables[v]);
                }
            }
        };
        this.combineLikeTerms();
        this.isEqualTo = function (that) {
            var n1 = this.terms.length;
            var n2 = that.terms.length;
            if (n1 !== n2) {
                return false;
            }
            for (var i = 0; i < n1; i++) {
                var t1 = this.terms[i];
                var found = false;
                for (var j = 0; j < n2; j++) {
                    var t2 = that.terms[j];
                    if (t1.coefficient === t2.coefficient && t1.variableString === t2.variableString) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    return false;
                }
            }
            return true;
        };
        this.isNegative = function () {
            return this.terms[0].coefficient < 0;
        };
        this.getCoefficentOfTerm = function (variable, degree) {
            var variableString = '';
            if (variable === '') {
                variableString = '';
            } else if (variable !== undefined && degree !== 0) {
                degree = degree || 1;
                variableString = variable + degree;
            }
            for (var i = 0; i < this.terms.length; i++) {
                if (this.terms[i].variableString === variableString) {
                    return this.terms[i].coefficient;
                }
            }
            return 0;
        };
        this.evaluate = function (values) {
            var value = 0;
            for (var i = 0; i < this.terms.length; i++) {
                value += this.terms[i].evaluate(values);
            }
            return value;
        };
        this.add = function (expression) {
            var terms = [];
            for (var i = 0; i < this.terms.length; i++) {
                var term = this.terms[i];
                terms.push([
                    term.coefficient,
                    term.variables
                ]);
            }
            if (expression instanceof KhanUtil.Term) {
                terms.push(new KhanUtil.Term(expression.coefficient, expression.variables));
            } else if (typeof expression === 'number') {
                terms.push(new KhanUtil.Term(expression));
            } else {
                for (var i = 0; i < expression.terms.length; i++) {
                    var term = expression.terms[i];
                    terms.push([
                        term.coefficient,
                        term.variables
                    ]);
                }
            }
            var result = new KhanUtil.RationalExpression(terms);
            result.combineLikeTerms();
            return result;
        };
        this.multiply = function (expression) {
            var multiplyTerms;
            if (expression instanceof KhanUtil.RationalExpression) {
                multiplyTerms = expression.terms;
            } else if (typeof expression === 'number' || expression instanceof KhanUtil.Term) {
                multiplyTerms = [expression];
            } else {
                multiplyTerms = [new KhanUtil.Term(1, expression)];
            }
            var terms = [];
            for (var i = 0; i < multiplyTerms.length; i++) {
                var value = multiplyTerms[i];
                for (var j = 0; j < this.terms.length; j++) {
                    terms.push(this.terms[j].multiply(value));
                }
            }
            return new KhanUtil.RationalExpression(terms);
        };
        this.divide = function (expression) {
            if (expression instanceof KhanUtil.RationalExpression) {
                if (expression.terms.length === 1) {
                    return this.divide(expression.terms[0]);
                }
                var factors1 = this.factor();
                var factors2 = expression.factor();
                if (factors1[1].isEqualTo(factors2[1])) {
                    var value = factors1[0].divide(factors2[0]);
                    return new KhanUtil.RationalExpression([value]);
                } else if (factors1[1].isEqualTo(factors2[1].multiply(-1))) {
                    var value = factors1[0].divide(factors2[0]).multiply(-1);
                    return new KhanUtil.RationalExpression([value]);
                } else {
                    return false;
                }
            } else {
                var terms = [];
                for (var i = 0; i < this.terms.length; i++) {
                    terms.push(this.terms[i].divide(expression));
                }
                return new KhanUtil.RationalExpression(terms);
            }
        };
        this.getGCD = function (that) {
            var t1 = this.getTermsGCD();
            var GCD;
            if (that instanceof KhanUtil.Term) {
                GCD = t1.getGCD(that);
            } else if (that instanceof KhanUtil.RationalExpression) {
                GCD = t1.getGCD(that.getTermsGCD());
            } else {
                return KhanUtil.getGCD(that, t1.coefficient);
            }
            if (GCD.coefficient < 0) {
                GCD.coefficient *= -1;
            }
            return GCD;
        };
        this.getTermsGCD = function () {
            var GCD = this.terms[0];
            for (var i = 0; i < this.terms.length; i++) {
                GCD = GCD.getGCD(this.terms[i]);
            }
            if (this.isNegative()) {
                GCD = GCD.multiply(-1);
            }
            return GCD;
        };
        this.factor = function () {
            var gcd = this.getTermsGCD();
            var factor = this.divide(gcd);
            return [
                gcd,
                factor
            ];
        };
        this.toString = function () {
            if (this.terms.length === 0) {
                return '0';
            }
            var s = this.terms[0].toString();
            for (var i = 1; i < this.terms.length; i++) {
                s += this.terms[i].toString(s !== '');
            }
            return s !== '' ? s : '0';
        };
        this.toStringFactored = function (parenthesise) {
            var factors = this.factor();
            if (this.terms.length === 1 || factors[0].isOne()) {
                if (parenthesise) {
                    return '(' + this.toString() + ')';
                } else {
                    return this.toString();
                }
            }
            var s = factors[0].toString() === '-1' ? '-' : factors[0].toString();
            s += '(' + factors[1].toString() + ')';
            return s;
        };
        this.getEvaluateString = function (values, color) {
            var s = this.terms[0].getEvaluateString(values, false, color);
            for (var i = 1; i < this.terms.length; i++) {
                s += this.terms[i].getEvaluateString(values, true, color);
            }
            return s !== '' ? s : '0';
        };
        this.getTermsRegex = function (permutations, start, stop) {
            var regex = '';
            start = start ? '|(?:^' + start : '|(?:^';
            stop = stop ? stop + '$)' : '$)';
            for (var p = 0; p < permutations.length; p++) {
                regex += start;
                var terms = permutations[p];
                for (var i = 0; i < terms.length; i++) {
                    regex += terms[i].regexForExpression(i);
                }
                regex += stop;
            }
            return regex;
        };
        this.regex = function (allowFactors) {
            var permutations = KhanUtil.getPermutations(this.terms);
            var regex = this.getTermsRegex(permutations).slice(1);
            if (!allowFactors || this.terms.length === 1) {
                return regex;
            }
            var factors = this.factor();
            permutations = KhanUtil.getPermutations(factors[1].terms);
            if (factors[0].isOne()) {
                regex += this.getTermsRegex(permutations, '\\s*\\(', '\\)\\s*');
            } else if (factors[0].toString() === '-1') {
                regex += this.getTermsRegex(permutations, '\\s*[-\\u2212]\\s*\\(', '\\)\\s*');
            } else {
                regex += this.getTermsRegex(permutations, factors[0].regexForExpression() + '\\*?\\s*\\(', '\\)\\s*');
            }
            factors[0] = factors[0].multiply(-1);
            factors[1] = factors[1].multiply(-1);
            permutations = KhanUtil.getPermutations(factors[1].terms);
            if (factors[0].isOne()) {
                regex += this.getTermsRegex(permutations, '\\s*\\(', '\\)\\s*');
            } else if (factors[0].toString === '-1') {
                regex += this.getTermsRegex(permutations, '\\s*[-\\u2212]\\s*\\(', '\\)\\s*');
            } else {
                regex += this.getTermsRegex(permutations, factors[0].regexForExpression() + '\\*?\\s*\\(', '\\)\\s*');
            }
            return regex;
        };
    }
});
},{}]},{},[1]);
