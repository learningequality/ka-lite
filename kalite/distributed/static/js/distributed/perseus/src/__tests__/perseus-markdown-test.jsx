var assert = require("assert");
var nodeUtil = require("util");
var _ = require("underscore");

var PerseusMarkdown = require("../perseus-markdown.jsx");
var parse = PerseusMarkdown.parse;
var characterCount = PerseusMarkdown.characterCount;

// TODO(aria): Don't duplicate these two methods from simple-markdown:

// A pretty-printer that handles `undefined` and functions better
// than JSON.stringify
// Important because some AST node fields can be undefined, and
// if those don't show up in the assert output, it can be
// very confusing to figure out how the actual and expected differ
var prettyPrintAST = (ast) => {
    return nodeUtil.inspect(ast, {
        depth: null,
        colors: false
    });
};

var validateParse = function(parsed, expected) {
    if (!_.isEqual(parsed, expected)) {
        var parsedStr = prettyPrintAST(parsed);
        var expectedStr = prettyPrintAST(expected);
        // assert.fail doesn't seem to print the
        // expected and actual anymore, so we just
        // throw our own exception.
        throw new Error("Expected:\n" +
            expectedStr +
            "\n\nActual:\n" +
            parsedStr
        );
    }
};

var htmlThroughReact = function(parsed) {
    var output = PerseusMarkdown.basicOutput(parsed);
    var rawHtml = React.renderToStaticMarkup(
        React.DOM.div(null, output)
    );
    var innerHtml = rawHtml
        .replace(/^<div>/, '')
        .replace(/<\/div>$/, '');
    var simplifiedHtml = innerHtml
        .replace(/>\n*/g, '>')
        .replace(/\n*</g, '<')
        .replace(/\s+/g, ' ');
    return simplifiedHtml;
};

var htmlFromMarkdown = function(source) {
    return htmlThroughReact(parse(source));
};

var assertParsesToReact = function(source, html) {
    var actualHtml = htmlFromMarkdown(source);
    if (actualHtml !== html) {
        console.warn(actualHtml);
        console.warn(html);
    }
    assert.strictEqual(actualHtml, html);
};

var validateCount = (source, expectedCount) => {
    assert.equal(characterCount(source),
                 expectedCount,
                 "characterCount(" + source + ") !== " + expectedCount);
};

describe("perseus markdown", () => {
    describe("parser", () => {
        it("should parse math", () => {
            var parsed = parse("$y = x + 1$");
            validateParse(parsed, [{
                type: "paragraph",
                content: [{
                    type: "math",
                    content: "y = x + 1"
                }]
            }]);

            var parsed2 = parse("hi $y = x + 1$ there");
            validateParse(parsed2, [{
                type: "paragraph",
                content: [
                    {type: "text", content: "hi "},
                    {type: "math", content: "y = x + 1"},
                    {type: "text", content: " there"},
                ]
            }]);
        });

        it("should parse nested math", () => {
            var parsed = parse("$y = \\text{$x + 1$}$");
            validateParse(parsed, [{
                type: "paragraph",
                content: [{
                    type: "math",
                    content: "y = \\text{$x + 1$}"
                }]
            }]);

            var parsed2 = parse(
                "$ x^2 \\text{blah $math \\text{something $more math$} $ } $"
            );
            validateParse(parsed2, [{
                type: "paragraph",
                content: [{
                    type: "math",
                    content: " x^2 \\text{blah $math " +
                        "\\text{something $more math$} $ } "
                }]
            }]);
        });

        it("should allow escaping in math", () => {
            var parsed = parse("$\\\\$");
            validateParse(parsed, [{
                type: "paragraph",
                content: [{
                    type: "math",
                    content: "\\\\"
                }]
            }]);

            var parsed2 = parse("$\\$$");
            validateParse(parsed2, [{
                type: "paragraph",
                content: [{
                    type: "math",
                    content: "\\$"
                }]
            }]);

            var parsed3 = parse("${$");
            validateParse(parsed3, [{
                type: "paragraph",
                content: [
                    {type: "text", content: "$"},
                    {type: "text", content: "{"},
                    {type: "text", content: "$"},
                ]
            }]);

            var parsed4 = parse("$\\{$");
            validateParse(parsed4, [{
                type: "paragraph",
                content: [{
                    type: "math",
                    content: "\\{"
                }]
            }]);

            var parsed4 = parse("hello $ escaped dollar \\$ $ not math");
            validateParse(parsed4, [{
                type: "paragraph",
                content: [
                    {type: "text", content: "hello "},
                    {type: "math", content: " escaped dollar \\$ "},
                    {type: "text", content: " not math"},
                ]
            }]);
        });

        it("should break on paragraphs", () => {
            var parsed = parse("hello $ single dollar");
            validateParse(parsed, [{
                type: "paragraph",
                content: [
                    {type: "text", content: "hello "},
                    {type: "text", content: "$ single dollar"},
                ]
            }]);

            var parsed2 = parse(
                "hello $ single dollar paragraph\n\n not math"
            );
            validateParse(parsed2, [
                {
                    type: "paragraph",
                    content: [
                        {type: "text", content: "hello "},
                        {type: "text", content: "$ single dollar paragraph"},
                    ]
                },
                {
                    type: "paragraph",
                    content: [
                        {type: "text", content: " not math"},
                    ]
                },
            ]);

            var parsed3 = parse("hello $ bad { math $");
            validateParse(parsed3, [{
                type: "paragraph",
                content: [
                    {type: "text", content: "hello "},
                    {type: "text", content: "$ bad "},
                    {type: "text", content: "{ math "},
                    {type: "text", content: "$"},
                ]
            }]);

        });

        it("should parse widget types and ids", () => {
            var parsed = parse("[[☃ test 1]]");
            validateParse(parsed, [{
                type: "paragraph",
                content: [{
                    type: "widget",
                    widgetType: "test",
                    id: "test 1"
                }]
            }]);

            var parsed2 = parse("[[☃ test 1]]+[[☃ input-number 2]]");
            validateParse(parsed2, [{
                type: "paragraph",
                content: [
                    {
                        type: "widget",
                        widgetType: "test",
                        id: "test 1"
                    },
                    {
                        type: "text",
                        content: "+"
                    },
                    {
                        type: "widget",
                        widgetType: "input-number",
                        id: "input-number 2"
                    },
                ]
            }]);

            var parsed3 = parse("*[[☃ test 2]]* [[☃ input-number 1]]");
            validateParse(parsed3, [{
                type: "paragraph",
                content: [
                    {
                        type: "em",
                        content: [{
                            type: "widget",
                            widgetType: "test",
                            id: "test 2"
                        }]
                    },
                    {
                        type: "text",
                        content: " "
                    },
                    {
                        type: "widget",
                        widgetType: "input-number",
                        id: "input-number 1"
                    },
                ]
            }]);
        });

        it("should allow escaping widget identifiers", () => {
            var parsed = parse("\\[[☃ test 1]]");
            validateParse(parsed, [{
                type: "paragraph",
                content: [
                    {content: "[", type: "text"},
                    {content: "[☃ test 1", type: "text"},
                    {content: "]", type: "text"},
                    {content: "]", type: "text"},
                ]
            }]);
        });

        it("should parse widgets next to each other as widgets", () => {
            var parsed = parse("[[☃ test 1]][[☃ test 2]]");
            validateParse(parsed, [{
                type: "paragraph",
                content: [
                    {type: "widget", widgetType: "test", id: "test 1"},
                    {type: "widget", widgetType: "test", id: "test 2"},
                ]
            }]);

            var parsed2 = parse("[[☃ test 1]] [[☃ test 2]]");
            validateParse(parsed2, [{
                type: "paragraph",
                content: [
                    {type: "widget", widgetType: "test", id: "test 1"},
                    {type: "text", content: " "},
                    {type: "widget", widgetType: "test", id: "test 2"},
                ]
            }]);
        });

        it("should parse multiple columns", () => {
            var parsed = parse(
                "hi\n\n" +
                "=====\n\n" +
                "there\n\n"
            );
            validateParse(parsed, [{
                type: "columns",
                col1: [
                    {
                        type: "paragraph",
                        content: [{
                            type: "text",
                            content: "hi",
                        }],
                    },
                ],
                col2: [
                    {
                        type: "paragraph",
                        content: [{
                            type: "text",
                            content: "there",
                        }],
                    },
                ],
            }]);
        });
    });

    describe("output", () => {
        it("should output paragraphs", () => {
            assertParsesToReact(
                "para!",
                // This is overridden in Renderer
                '<div class="paragraph">para!</div>'
            );
        });

        it("should output columns", () => {
            assertParsesToReact(
                "col1\n\n" +
                "=====\n\n" +
                "col2",
                '<div class="perseus-two-columns">' +
                '<div class="perseus-column">' +
                '<div class="paragraph">col1</div>' +
                '</div>' +
                '<div class="perseus-column">' +
                '<div class="paragraph">col2</div>' +
                '<div class="sat-grafting-area"></div>' +
                '</div>' +
                '</div>'
            );
        });

        it("should render ```alt screenreader blocks", () => {
            assertParsesToReact(
                "```alt\n" +
                "screenreader-only text!\n" +
                "```",
                // I'm not sure this is the best order; it looks like
                // code is parsed before paragraphs, and then the
                // paragraph is parsed internally.
                '<div class="perseus-markdown-alt perseus-sr-only">' +
                '<div class="paragraph">' +
                'screenreader-only text!' +
                '</div>' +
                '</div>'
            );
        });
    });

    describe("characterCount", () => {
        it("should ignore Markdown and widgets but count TeX", () => {
            validateCount("", 0);
            validateCount("-------", 0);

            validateCount("  foo bar baz", 11);
            // Relies on new features of simple-markdown not-yet-landed in
            // perseus
            // TODO(aria): Re-enable once we upgrade simple-markdown
            //validateCount("- foo bar baz", 11);
            validateCount("# foo bar baz", 11);

            validateCount("[text](resource)", 4);
            validateCount("header 1 | header 2\n" +
                          "- | -\n" +
                          "data 1 | data 2\n" +
                          "data 3 | data 4", 40);

            validateCount("  ☃ test 1  ", 8);
            validateCount("[[☃ test 1]]", 0);

            validateCount(" 1234 ", 4);
            validateCount("$1234$", 4);
        });

        it("should only count multiple sequential spaces within code", () => {
            validateCount(         "a s  d   f    ", 7);
            validateCount("    " + "a s  d   f    ", 14);

            validateCount(" 1  2  3 ", 5);
            validateCount("`1  2  3`", 7);

            validateCount("123   4 5  6 7   890", 15);
            validateCount("123  `4 5  6 7`  890", 16);
        });

        it("should count spaces between inline elements", () => {
            validateCount("foo to the bar", 14);
            validateCount("foo *to the* bar", 14);
            validateCount("foo $to the$ bar", 14);
        });

        it("should not count spaces between block elements", () => {
            validateCount("foo\n\nbar", 6);
            validateCount(" foo \n\n bar ", 6);
            validateCount("foo\n\n[[☃ test 1]]\n\nbar", 6);
            validateCount(" foo \n\n [[☃ test 1]] \n\n bar ", 6);
        });
    });
});
