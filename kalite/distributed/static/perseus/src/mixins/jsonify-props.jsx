var WIDGET_PROP_BLACKLIST = require("./widget-prop-blacklist.jsx");

var JsonifyProps = {
    toJSON: function() {
        // Omit props that get passed to all widgets
        return _.omit(this.props, WIDGET_PROP_BLACKLIST);
    }
};

module.exports = JsonifyProps;
