function nextQuestion() {
    exercise_id = item_sequence[index];
    seed = seed_sequence[index];
    loadExercise(exercise_id, function(exercise) {
        exerciseData = {
            "basepoints": exercise.basepoints ,
            "description": exercise.description,
            "title": exercise.display_name,
            "lang": exercise.lang,
            "exerciseModel": {
                "displayName": exercise.display_name,
                "name": exercise.name,
                "secondsPerFastProblem": exercise.seconds_per_fast_problem,
                "authorName": exercise.author_name,
                "relatedVideos": [],
                "fileName": exercise.template
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
            "seed": seed
        }
        $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
    });
}

function loadExercise(exercise_id, callback) {
    console.log('==> loadExercise', exercise_id);
    doRequest("/api/exercise/" + exercise_id)
        .success(function(data) {
            callback(data);
        })
        .fail(function(resp) {
            handleFailedAPI(resp, "exercise_data");
        }
    );
}


function endTest() {
    window.location.href = "/"
}

function saveLogNextQuestion(correct) {

    complete = (index == item_sequence.length-1)

    var data = {
        exercise_id: exerciseData.exerciseModel.name,
        correct: correct,
        random_seed: exerciseData.seed,
        title: title,
        index: index,
        complete: complete,
        answer_given: answerGiven
    };

    doRequest("/test/api/save_attempt_log", data)
        .success(function(data) {
            show_api_messages(data, "id_student_logs");
            if(!complete) {
                index += 1;
                nextQuestion();
            } else {
                endTest();
            }
        })
        .fail(function(resp) {
            handleFailedAPI(resp, "id_student_logs");
        });

};

var hintsResetPoints = true; // Sometimes it's OK to view hints (like, after a correct answer)
var exercises = [];
var exerciseData = {};
var complete = false;
var answerGiven = null;

$(function() {
    $(Khan).on("answerGiven", function (event, answer) {
        answerGiven = answer;
    })
    $(Khan).bind("loaded", function () {
        $(Exercises).trigger("problemTemplateRendered");
        nextQuestion();
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
});
