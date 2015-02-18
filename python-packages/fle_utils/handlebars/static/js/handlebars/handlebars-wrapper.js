window.HB = (function() {

    var HB = {
        _raw: {},
        _compiled: {}
    }

    HB.template = function(name) {

        var inner_fn = function(context) {

            var tmpl;

            if (HB._compiled[name] !== undefined) { // template is already compiled
                tmpl = HB._compiled[name];
            } else if (HB._raw[name] !== undefined) { // not compiled, but we have raw text, so compile & store
                tmpl = HB._compiled[name] = Handlebars.compile(HB._raw[name]);
            } else { // if we don't have even the template text, there's nothing we can do for now
                throw Error("Could not find template: '" + name + "'");
            }

            return tmpl(context);

        };

        return inner_fn;

    };

    HB.register = function(name, template) {
        if (HB._raw[name] !== undefined) {
            throw Error("Template has already been defined: '" + name + "'");
        }
        HB._raw[name] = template;
    };

    return HB;

})();

