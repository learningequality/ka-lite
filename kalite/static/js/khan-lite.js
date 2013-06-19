// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// add the CSRF token to all ajax requests
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    cache: false,
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function doRequest(url, data) {
    return $.ajax({
        url: url,
        type: data ? "POST" : "GET",
        data: data ? JSON.stringify(data) : "",
        contentType: "application/json",
        dataType: "json"
    });
}


// Generic functions for client-side message passing
//   through our Django-based server-side API

function show_message(msg_class, msg_text, msg_id) {
    // This function is generic--can be called with server-side messages,
    //    or to display purely client-side messages.
    // msg_class includes error, warning, and success
    
    msg_html = "<div class='message " + msg_class + "'";
    if (msg_id) {
        msg_html += " id='" + msg_id + "'"
    }
    msg_html += ">" + msg_text + "</div>"
    alert(msg_html)
    $("#message_container").append(msg_html);
    return $("#message_container");
}

function clear_message(msg_id) {
    // Clear a single message, by ID
    $("#" + msg_id).remove();
    return $("#message_container");
}

function clear_messages() {
    // Clear all messages
    $("#message_container .message").remove();
    return $("#message_container");
}

$(function() {

    // load progress data for all videos linked on page, and render progress circles
    var youtube_ids = $.map($(".progress-circle[data-youtube-id]"), function(el) { return $(el).data("youtube-id") });
    if (youtube_ids.length > 0) {
        doRequest("/api/get_video_logs", youtube_ids).success(function(data) {
            $.each(data, function(ind, video) {
                var newClass = video.complete ? "complete" : "partial";
                $("[data-youtube-id='" + video.youtube_id + "']").addClass(newClass);
            });
        });
    }

    // load progress data for all exercises linked on page, and render progress circles
    var exercise_ids = $.map($(".progress-circle[data-exercise-id]"), function(el) { return $(el).data("exercise-id") });
    if (exercise_ids.length > 0) {
        doRequest("/api/get_exercise_logs", exercise_ids).success(function(data) {
            $.each(data, function(ind, exercise) {
                var newClass = exercise.complete ? "complete" : "partial";
                $("[data-exercise-id='" + exercise.exercise_id + "']").addClass(newClass);
            });
        });
    }


});