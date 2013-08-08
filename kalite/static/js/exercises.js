function updateStreakBar() {
    // update the streak bar UI
    $("#streakbar .progress-bar").css("width", exerciseData.percentCompleted + "%");
    $("#totalpoints").html(exerciseData.points > 0 ? (exerciseData.points) : "")
    if (exerciseData.percentCompleted >= 100) {
        $("#streakbar .progress-bar").addClass("completed");
        $("#hint-remainder").hide();
    }
}

function updateQuestionPoints(points) {
    // show points for correct question, or none if not answered yet.
    $("#questionpoints").html(points ? (points + " " + gettext("points") + "!") : "");
}

function updatePercentCompleted(correct) {

    // update the streak; increment by 10 if correct, otherwise reset to 0
    if (correct && !exerciseData.hintUsed) {
        exerciseData.percentCompleted += 10;
        if (exerciseData.percentCompleted < 101) {
            bumpprob = Math.floor(Math.random()*100)
            bump = (bumpprob < 90) ? 1 : (bumpprob < 99 ? 1.5 : 2);
            inc = Math.ceil(basepoints*bump);
            exerciseData.points += inc;
            updateQuestionPoints(inc);
        }
    } else if (exerciseData.percentCompleted < 100) {
        exerciseData.percentCompleted = 0;
        exerciseData.points = 0;
    }

    // max out at the percentage completed at 100%
    exerciseData.percentCompleted = Math.min(exerciseData.percentCompleted, 100);

    updateStreakBar();

    var data = {
        exercise_id: exerciseData.exerciseModel.name,
        streak_progress: exerciseData.percentCompleted,
        points: exerciseData.points,
        correct: correct
    };

    doRequest("/api/save_exercise_log", data)
        .success(function(data) {
            show_api_messages(data, "id_student_logs")
        })
        .fail(function(resp) {
            communicate_api_failure(resp, "id_student_logs");
        });

};

$(function() {
    $(Exercises).trigger("problemTemplateRendered");
    $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
    $(Khan).bind("checkAnswer", function(ev, data) {
        updatePercentCompleted(data.pass);
    });
    $(Khan).bind("hintUsed", function(ev, data) {
        exerciseData.hintUsed = true;
        if (exerciseData.percentCompleted < 100) {
            exerciseData.percentCompleted = 0;
            exerciseData.points = 0;
        }
        updateStreakBar();
    });
    basepoints = Math.ceil(7*Math.log(exerciseData.exerciseModel.secondsPerFastProblem));
    $("#next-question-button").click(function() {
        _.defer(function() {
            updateQuestionPoints(false);
            exerciseData.hintUsed = false;
            exerciseData.seed = Math.floor(Math.random() * 500);
            $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
        });
    });
    doRequest("/api/get_exercise_logs", [exerciseData.exerciseModel.name])
        .success(function(data) {
            if (data.length === 0) {
                return;
            }
            exerciseData.percentCompleted = data[0].streak_progress;
            exerciseData.points = data[0].points;
            updateStreakBar();

            // Show all messages in "messages" object
            show_api_messages(data.messages, "id_student_logs")
        })
        .fail(function (resp) {
            // Expects to receive messages ({ type: message } format) about failures
            communicate_api_failure(resp, "id_student_logs");
        });
});
