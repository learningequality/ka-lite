var Handlebars = require("hbsfy/runtime");
var _ = require("underscore");
var sprintf = require("sprintf-js").sprintf;

Handlebars.registerHelper("ifcond", function(v1, operator, v2, options) {
    switch (operator)
    {
        case "==":
            return (v1==v2)?options.fn(this):options.inverse(this);

        case "!=":
            return (v1!=v2)?options.fn(this):options.inverse(this);

        case "===":
            return (v1===v2)?options.fn(this):options.inverse(this);

        case "!==":
            return (v1!==v2)?options.fn(this):options.inverse(this);

        case "&&":
            return (v1&&v2)?options.fn(this):options.inverse(this);

        case "||":
            return (v1||v2)?options.fn(this):options.inverse(this);

        case "<":
            return (v1<v2)?options.fn(this):options.inverse(this);

        case "<=":
            return (v1<=v2)?options.fn(this):options.inverse(this);

        case ">":
            return (v1>v2)?options.fn(this):options.inverse(this);

        case ">=":
            return (v1>=v2)?options.fn(this):options.inverse(this);

        default:
            return eval(""+v1+operator+v2)?options.fn(this):options.inverse(this); // jshint ignore:line
    }
});


Handlebars.registerHelper("_", function(i18n_key) {

    // TODO(jamalex): make sure this is getting picked up and included in the po files
    return sprintf(gettext(i18n_key), this);

});

// from https://gist.github.com/TastyToast/5053642
Handlebars.registerHelper ('truncate', function (str, len) {
    if (!str) {
        return "";
    }
    if (str.length > len && str.length > 0) {
        var new_str = str + " ";
        new_str = str.substr (0, len);
        new_str = str.substr (0, new_str.lastIndexOf(" "));
        new_str = (new_str.length > 0) ? new_str : str.substr (0, len);

        return new Handlebars.SafeString ( new_str +'...' ); 
    }
    return str;
});

// from http://stackoverflow.com/questions/19646244/handlebars-js-access-object-value-with-a-variable-key
Handlebars.registerHelper('withItem', function(object, options) {
    return options.fn(object[options.hash.key]);
});

// A little bit of magic to let us use Django JS Reverse directly from inside a Handlebars template
// Simply pass any arguments that you might otherwise use in order
Handlebars.registerHelper('url', function(url_name) {
    var ref;
    // Make check more robust so that undefined urls also return empty string
    if (((ref = window.Urls) !== undefined ? ref[url_name] : void 0) !== undefined) {
        var args = Array.prototype.slice.call(arguments, 1, -1);
        return window.Urls[url_name].apply(window.Urls, args);
    } else {
        if (!window.Urls) {
            console.warn("Django Reverse JS not loaded");
        } else if (!window.Urls[url_name]) {
            console.warn("Url name invalid");
        }
        return "";
    }
});

Handlebars.registerHelper("math", function(lvalue, operator, rvalue, options) {
    lvalue = parseFloat(lvalue);
    rvalue = parseFloat(rvalue);

    return {
        "+": lvalue + rvalue,
        "-": lvalue - rvalue,
        "*": lvalue * rvalue,
        "/": lvalue / rvalue,
        "%": lvalue % rvalue
    }[operator];
});

Handlebars.registerHelper("datetime", function(datetime_string, options) {
    var date = new Date(datetime_string);
    return date.toLocaleString();
});

Handlebars.registerHelper("ifObject", function(candidate, options){
    if (_.isObject(candidate)) {
        return options.fn(this);
    } else {
        return options.inverse(this);
    }
});

module.exports = Handlebars;
