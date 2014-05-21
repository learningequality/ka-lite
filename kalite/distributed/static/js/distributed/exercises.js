window.ExerciseModel = Backbone.Model.Extend({
    defaults: {
        basepoints: 0,
        description: "",
        title: "",
        name: "",
        secondsPerFastProblem: 0,
        authorName: "",
        relatedVideos: [],
        fileName: ""
    },

    fetch: function() {

        var self = this;

        doRequest("/api/exercise/" + this.get("exercise_id"))
            .success(function(data) {
                if (data.length === 0) {
                    return;
                }
                self.set({
                    "basepoints": data.basepoints ,
                    "description": data.description,
                    "title": data.display_name,
                    "lang": data.lang,
                    "name": data.name,
                    "secondsPerFastProblem": data.seconds_per_fast_problem,
                    "authorName": data.author_name,
                    "fileName": data.template
                })
            })
    },
})



function updateStreakBar() {
    // update the streak bar UI
    $("#streakbar .progress-bar").css("width", exerciseData.percentCompleted + "%");
    $("#totalpoints").html(exerciseData.points > 0 ? (exerciseData.points) : "");
    if (exerciseData.percentCompleted >= 100) {
        $("#streakbar .progress-bar").addClass("completed");
        $("#hint-remainder").hide();
    }
}

function updateQuestionPoints(points) {
    // show points for correct question, or none if not answered yet.
    $("#questionpoints").html(points ? (sprintf(gettext("%(points)d points!"), { points : points })) : "");
}

function updatePercentCompleted(correct) {

    // update the streak; increment by 10 if correct, otherwise reset to 0
    if (correct && !exerciseData.hintUsed) {
        exerciseData.percentCompleted += 10;
        if (exerciseData.percentCompleted < 101) {
            bumpprob = Math.floor(Math.random()*100);
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

    // Increment the # of attempts
    exerciseData.attempts++;

    updateStreakBar();

    var data = {
        exercise_id: exerciseData.exerciseModel.name,
        streak_progress: exerciseData.percentCompleted,
        points: exerciseData.points,
        random_seed: exerciseData.seed,
        correct: correct,
        attempts: exerciseData.attempts,
        answer_given: answerGiven
    };

    doRequest("/api/save_exercise_log", data)
        .success(function(data) {
            // update the top-right point display, now that we've saved the points successfully
            userModel.set("newpoints", exerciseData.points - exerciseData.starting_points);
        })
}

var hintsResetPoints = true; // Sometimes it's OK to view hints (like, after a correct answer)
var answerGiven = null;

$(function() {

    $(Khan).bind("loaded", function() {
        exerciseData.seed = Math.floor(Math.random() * 1000);
        $(Exercises).trigger("problemTemplateRendered");
        $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
    });
    $(Khan).on("answerGiven", function (event, answer) {
        answerGiven = answer;
    })
    $(Exercises).bind("checkAnswer", function(ev, data) {
        updatePercentCompleted(data.correct);

        // after giving a correct answer, no penalty for viewing a hint.
        // after giving an incorrect answer, penalty for giving a hint (as a correct answer will give you points)
        hintsResetPoints = !data.correct;
        $("#hint-remainder").toggle(hintsResetPoints); // hide/show message about hints
    });
    $(Exercises).bind("gotoNextProblem", function(ev, data) {
        // When ready for the next problem, hints matter again!
        hintsResetPoints = true;
        $("#hint-remainder").toggle(hintsResetPoints); // hide/show message about hints
    });
    $(Exercises).bind("hintUsed", function(ev, data) {
        if (exerciseData.hintUsed || !hintsResetPoints) { // only register the first hint used on a question
            return;
        }
        exerciseData.hintUsed = true;
        updatePercentCompleted(false);
    });
    basepoints = exerciseData.basepoints;
    $("#next-question-button").click(function() {
        _.defer(function() {
            updateQuestionPoints(false);
            exerciseData.hintUsed = false;
            exerciseData.seed = Math.floor(Math.random() * 1000);
            $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
        });
    });
    doRequest("/api/get_exercise_logs", [exerciseData.exerciseModel.name])
        .success(function(data) {
            if (data.length === 0) {
                return;
            }
            exerciseData.percentCompleted = data[0].streak_progress;
            exerciseData.points = exerciseData.starting_points = data[0].points;
            exerciseData.attempts = data[0].attempts;

            updateStreakBar();
        });
    doRequest("/api/get_exercise_attempt_logs", [exerciseData.exerciseModel.name])
        .success(function(data) {
            if (data.length === 0) {
                return;
            }
            console.log(data);
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
