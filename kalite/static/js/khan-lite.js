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
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function doRequest(url, data, method) {
    return $.ajax({
        url: url,
        type: method || "GET",
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: "json"
    });
}

function updatePercentCompleted(correct) {

    if (exerciseData.percentCompleted === 100) {
        return;
    }

    // update the streak; increment by 10 if correct, otherwise reset to 0
    if (correct) {
        exerciseData.percentCompleted += 10;
    } else {
        exerciseData.percentCompleted = 0;
    }

    // max out at the percentage completed at 100%
    exerciseData.percentCompleted = Math.min(exerciseData.percentCompleted, 100);

    // update the streak bar UI
    $("#streakbar .progress-bar").css("width", exerciseData.percentCompleted + "%");
    if (exerciseData.percentCompleted >= 100) {
        $("#streakbar .progress-bar").addClass("completed");
    }

    var data = {
        exercise: exerciseData.exerciseModel.name,
        percentCompleted: exerciseData.percentCompleted
    };

    doRequest("/api/exercises/attempt", data, "POST");

};
