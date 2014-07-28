/*
 * In this file, an `expression` is some portion of valid TeX enclosed in
 * curly brackets.
 */

 /*
  * Find the index at which an expression ends, i.e., has an unmatched
  * closing curly bracket. This method assumes that we start with a non-open
  * bracket character and end when we've seen more left than right brackets
  * (rather than assuming that we start with a bracket character and wait for
  * bracket equality).
  */
function findEndpoint (tex, currentIndex) {
    var bracketDepth = 0;
    var rightEndpoint;

    for (var i = currentIndex, len = tex.length; i < len; i++) {
        var c = tex[i];

        if (c === '{') {
            bracketDepth++;
        } else if (c === '}') {
            bracketDepth--;
        }

        if (bracketDepth < 0) {
            return i;
        }
    }
    // If we never see unbalanced curly brackets, default to the
    // entire string
    return tex.length;
}


/*
 * Parses an individual set of curly brackets into TeX.
 */
function parseNextExpression (tex, currentIndex) {
    // Find the first '{' and grab subsequent TeX
    // Ex) tex: '{3}{7}', and we want the '3'
    var openBracketIndex = tex.indexOf('{', currentIndex);
    var nextExpIndex = openBracketIndex + 1;

    // Truncate to only contain remaining TeX
    var endpoint = findEndpoint(tex, nextExpIndex);
    var expressionTeX = tex.substring(nextExpIndex, endpoint);
    var parsedExp = parseTex(expressionTeX);

    return {
        endpoint: endpoint,
        expression: parsedExp
    };
}


function getNextFracIndex (tex, currentIndex) {
    var dfrac = "\\dfrac";
    var frac = "\\frac";

    var nextFrac = tex.indexOf(frac, currentIndex);
    var nextDFrac = tex.indexOf(dfrac, currentIndex);

    if (nextFrac > -1 && nextDFrac > -1) {
        return Math.min(nextFrac, nextDFrac);
    } else if (nextFrac > -1) {
        return nextFrac;
    } else if (nextDFrac > -1) {
        return nextDFrac;
    } else {
        return -1;
    }
}


/*
 * Parse a TeX expression into something interpretable by input-number.
 * The process is exclusively concerned with parsing fractions, i.e., \dfracs.
 * The basic algorithm splits on \dfracs and then recurs on the subsequent
 * "expressions", i.e., the {} pairs that follow \dfrac. The recursion is to
 * allow for nested \dfrac elements.
 */
function parseTex (tex, currentIndex) {
    // Ex) tex: '2 \dfrac {3}{7}'
    var parsedString = "";
    var currentIndex = 0;
    var nextFrac = getNextFracIndex(tex, currentIndex);

    // For each \dfrac, find the two expressions (wrapped in {}) and recur
    while (nextFrac > -1) {
        // Gather first fragment, preceding \dfrac
        // Ex) parsedString: '2 '
        parsedString += tex.substring(currentIndex, nextFrac);

        // Remove everything preceding \dfrac, which has been parsed
        currentIndex = nextFrac;

        // Parse first expression and move index past it
        // Ex) firstParsedExpression.expression: '3'
        var firstParsedExpression = parseNextExpression(
            tex, currentIndex
        );
        currentIndex = firstParsedExpression.endpoint + 1;

        // Parse second expression
        // Ex) secondParsedExpression.expression: '7'
        var secondParsedExpression = parseNextExpression(
            tex, currentIndex
        );
        currentIndex = secondParsedExpression.endpoint + 1;

        // Add expressions to running total of parsed expressions
        // Ex) parsedString: '2 3/7'
        if (parsedString.length) {
            parsedString += " ";
        }
        parsedString += firstParsedExpression.expression + "/" +
            secondParsedExpression.expression;

        // Find next DFrac, relative to currentIndex
        nextFrac = getNextFracIndex(tex, currentIndex);
    }

    // Add remaining TeX, which is \dfrac-free
    var rightEndpoint = findEndpoint(
        tex, currentIndex
    );
    parsedString += tex.substring(currentIndex, rightEndpoint);

    return parsedString;
}

module.exports = parseTex;
