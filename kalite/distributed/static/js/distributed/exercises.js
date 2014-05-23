window.ExerciseDataModel = Backbone.Model.extend({
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

    initialize: function() {
        _.bindAll(this);

        this.fetch();

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

window.ExerciseLogModel = Backbone.Model.extend({

    exerciseModel: null,

    save: function() {

        var already_complete = this.complete;

        if (this.attempts > 20 && !this.complete) {
          this.struggling = True;
        }

        this.complete = this.streak_progress >= 100;

        if (!already_complete && this.complete) {
          this.struggling = False;
          this.completion_timestamp = userModel.get_server_time().toJSON();
          this.attempts_before_completion = this.attempts;
        }

        var data = {
            exercise_id: this.exerciseModel.name,
            streak_progress: this.percentCompleted,
            points: this.points,
            random_seed: this.exerciseModel.seed,
            correct: this.correct,
            attempts: this.attempts,
            answer_given: answerGiven
        };

        doRequest("/api/save_exercise_log", data)
            .success(function(data) {
                // update the top-right point display, now that we've saved the points successfully
                userModel.set("newpoints", this.points - this.starting_points);
            })
    },

    fetch: function() {
        doRequest("/api/get_exercise_logs", [this.exerciseModel.name])
            .success(function(data) {
                if (data.length === 0) {
                    return;
                }
                this.set(data);
                this.starting_points = data[0].points;
            });
    }
})

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

    var data = {
        exercise_id: exerciseData.exerciseModel.name,
        streak_progress: exerciseData.percentCompleted,
        points: exerciseData.points,
        random_seed: exerciseData.seed,
        correct: correct,
        attempts: exerciseData.attempts,
        answer_given: answerGiven // TODO(jamalex): refactor me!
    };

    doRequest("/api/save_exercise_log", data)
        .success(function(data) {
            // update the top-right point display, now that we've saved the points successfully
            userModel.set("newpoints", exerciseData.points - exerciseData.starting_points);
        })
}

var hintsResetPoints = true; // Sometimes it's OK to view hints (like, after a correct answer)
var answerGiven = null;

window.ExerciseProgressView = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.listenTo(model, "change", this.render);

        this.render();

    },

    render: function() {
        this.update_streak_bar();
    },

    update_streak_bar: function() {
        // update the streak bar UI
        this.$("#streakbar .progress-bar").css("width", this.model.get("streak_progress") + "%");
        this.$("#totalpoints").html(this.model.get("points") > 0 ? this.model.get("points") : "");
        if (this.model.get("streak_progress") >= 100) {
            this.$("#streakbar .progress-bar").addClass("completed");
            this.$("#hint-remainder").hide();
        }
    }


});

window.ExerciseWrapperView = Backbone.View.extend({

    template: HB.template("exercise/exercise-wrapper"),

    initialize: function() {

        _.bindAll(this);

        this.render();

        this.exercise_progress_view = new ExerciseProgressView({
            el: this.$(".exercise-progress-wrapper"),
            model: this.model
        });

        this.initialize_khan_exercises_listeners();

        // this.adjust_scratchpad_margin();

    },

    events: {
        "click #scratchpad-show": "adjust_scratchpad_margin"
    },

    render: function() {

        this.$el.html(this.template(this.model.attributes));

        this.initialize_listeners();

    },

    initialize_listeners: function() {
        this.$("#next-question-button").click(this.next_question_clicked); // needs to be explicit (not in "events")
    },

    initialize_khan_exercises_listeners: function() {

        $(Khan).bind("loaded", function() {
            exerciseData.seed = Math.floor(Math.random() * 1000);
            $(Exercises).trigger("problemTemplateRendered");
            $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
        });

        $(Khan).on("answerGiven", function (event, answer) {
            answerGiven = answer;
        });

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

    },

    next_question_clicked: function() {
        alert("woo")
        updateQuestionPoints(false);
        exerciseData.hintUsed = false;
        exerciseData.seed = Math.floor(Math.random() * 1000);
        $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
    },

    adjust_scratchpad_margin: function() {
        if (Khan.scratchpad.isVisible()) {
            this.$(".current-card-contents #problemarea").css("margin-top", "50px");
        } else {
            this.$(".current-card-contents #problemarea").css("margin-top", "10px");
        }
    }

});


$(function() {

    window.exerciseWrapperView = new ExerciseWrapperView({
        el: $(".exercise-wrapper"),
        model: new Backbone.Model // temp
    });

    basepoints = exerciseData.basepoints;

});

