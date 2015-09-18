var $ = require("../base/jQuery");

module.exports = function sanitize_string(input_string) {
    return $('<div/>').text(input_string).html();
};