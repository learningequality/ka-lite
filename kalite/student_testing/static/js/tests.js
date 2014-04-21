function nextQuestion() {
        exercise = exercises[i]
        exerciseData = {
        "basepoints": exercise.basepoints ,
        "description": exercise.description,
        "title": exercise.display_name,
        "exerciseModel": {
            "displayName": exercise.display_name,
            "name": exercise.name,
            "secondsPerFastProblem": exercise.seconds_per_fast_problem,
            "authorName": exercise.author_name,
            "relatedVideos": [],
            "fileName": exercise.name + ".html"
        },
        "readOnly": false,
        "percentCompleted": 0,
        "points": 0,
        "starting_points": 0,
        "attempts": 0,
        "exerciseProgress": {
            "level": ""
        },
        "lastCountHints": 0,
        "seed": seed + j
    }
}

function endTest() {
    window.location.href = "/research/?next=test"
}

function saveLogNextQuestion(correct) {

    complete = (i == exercises.length-1 && j == repeats)

    var data = {
        exercise_id: exerciseData.exerciseModel.name,
        correct: correct,
        random_seed: exerciseData.seed,
        test: test,
        index: i,
        repeat: j,
        length: exercises.length,
        complete: complete
    };

    doRequest("/test/api/save_attempt_log", data)
        .success(function(data) {
            show_api_messages(data, "id_student_logs");
            if(!complete) {
                if(j === repeats) {
                    j = 0;
                    i += 1;
                } else {
                    j += 1;
                }
                nextQuestion();
                $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
            } else {
                endTest();
            }
        })
        .fail(function(resp) {
            communicate_api_failure(resp, "id_student_logs");
        });

};

var hintsResetPoints = true; // Sometimes it's OK to view hints (like, after a correct answer)
var exercises = [];
var exerciseData = {};
var complete = false;

$(function() {
    $(Khan).bind("loaded", function() {
        doRequest("/api/flat_topic_tree" + path + "?leaf_type=Exercise")
            .success(function(data) {
            exercises = data
            nextQuestion();
            $(Exercises).trigger("problemTemplateRendered");
            $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
            })
            .fail(function(resp) {
                communicate_api_failure(resp, "id_student_logs");
            });
    });
    $(Exercises).bind("checkAnswer", function(ev, data) {
        $("#check-answer-button").parent().stop(jumpedToEnd=true)
        saveLogNextQuestion(data.correct);
    });
});

function adjust_scratchpad_margin(){
    if (Khan.scratchpad.isVisible()) {
        $(".current-card-contents #problemarea").css("margin-top","50px");
    } else {
        $(".current-card-contents #problemarea").css("margin-top","10px");
    }
}

$(function(){

    adjust_scratchpad_margin();

    $("#scratchpad-show").click(function(){
        _.defer(function() {
            adjust_scratchpad_margin();
        });
    });

    $(".return-link").click(function() {
        window.history.go(-1);
        return false;
    });
});
