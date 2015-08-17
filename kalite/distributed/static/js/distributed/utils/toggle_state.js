var $ = require("../base/jQuery");

module.exports = function toggle_state(state, status) {
    $("." + (status ? "not-" : "") + state + "-only").hide();
    $("." + (!status ? "not-" : "") + state + "-only").show();
    // Use display block setting instead of inline to prevent misalignment of navbar items.
    $(".nav ." + (!status ? "not-" : "") + state + "-only").css("display", "block");
};