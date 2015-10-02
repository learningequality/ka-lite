var $ = require("../base/jQuery");

// Generates a unique ID for each message - No duplicates.
String.prototype.hashCode = function(){
    var hash = 0, i, char;
    if (this.length === 0) return hash;
    for (i = 0, l = this.length; i < l; i++) {
        char  = this.charCodeAt(i);
        hash  = ((hash<<5)-hash)+char;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

// Generic functions for client-side message passing
//   through our Django-based server-side API
function show_message(msg_class, msg_text, msg_id) {
    // This function is generic--can be called with server-side messages,
    //    or to display purely client-side messages.
    // msg_class includes error, warning, and success
    if (msg_id === undefined) {
        // Only do this if msg_text and its hashCode are both defined
        if ((typeof msg_text !== "undefined" ? msg_text.hashCode : void 0)) {
            msg_id = msg_text.hashCode();
        }
    }

    // Avoid duplicating the same message by removing any existing message with the same id
    if (msg_id) {
        $("#" + msg_id).remove();
    }

    if (!msg_text) {
        return $("#message_container");
    }

    var x_button = '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>';

    if (msg_class === "error") {
        msg_class = "danger";
    }
    var msg_html = "<div class='alert alert-" + msg_class + "'";

    if (msg_id) {
        msg_html += " id='" + msg_id + "'";
    }
    msg_html += ">" + x_button + msg_text + "</div>";
    $("#message_container").append(msg_html);
    return $("#message_container");
}

function clear_messages(msg_type) {
    if (!msg_type) {
        // Clear all messages
        $("#message_container .alert").remove();
    } else {
        $("#message_container .alert-" + msg_type).remove();
    }
    return $("#message_container");
}

function get_message(msg_id) {
    return $("#" + msg_id).text();
}

function show_api_messages(messages) {
    // When receiving an error response object,
    //   show errors reported in that object
    if (!messages) {
        return;
    }
    switch (typeof messages) {
        case "object":
            for (var msg_type in messages) {
                show_message(msg_type, messages[msg_type]);
            }
            break;
        case "string":
            // Should throw an exception, but try to handle gracefully
            show_message("info", messages);
            break;
        default:
            // Programming error; this should not happen
            // NOTE: DO NOT WRAP THIS STRING.
            throw "do not call show_api_messages object of type " + (typeof messages);
    }
}


module.exports = {
    show_message: show_message,
    clear_messages: clear_messages,
    get_message: get_message,
    show_api_messages: show_api_messages
};