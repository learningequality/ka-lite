window.ExerciseDataModel = Backbone.Model.extend({
    defaults: {
        basepoints: 0,
        description: "",
        title: "",
        name: "",
        seconds_per_fast_problem: 0,
        author_name: "",
        related_videos: [],
        file_name: ""
    },

    initialize: function() {
        _.bindAll(this);

        this.listenTo(this, 'change', this.updateExerciseData);

        this.fetch();
    },

    url: function () {
        return "/api/exercise/" + this.get("exercise_id");
    },

    updateExerciseData: function () {
        exerciseData = {
            "basepoints": this.basepoints ,
            "description": this.description,
            "title": this.display_name,
            "exerciseModel": {
                "displayName": this.display_name,
                "name": this.name,
                "secondsPerFastProblem": this.seconds_per_fast_problem ,
                "authorName": this.author_name,
                "relatedVideos": this.related_videos,
                "fileName": this.file_name
            }
        };
    }

})

window.ExerciseLogModel = Backbone.Model.extend({

    init: function() {
        _.bindAll(this);

        var self = this;

        this.fetch().success(function(data){
            self.starting_points = self.get("points");
        });
    },

    save: function() {

        var self = this;

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



        Backbone.Model.prototype.save.call(this)
            .success(function(data) {
                // update the top-right point display, now that we've saved the points successfully
                userModel.set("newpoints", self.get("points") - self.starting_points);
            })
    },

    url: function () {
        return "/api/exercise_log" + this.get("exercise_id");
    }

})

window.AttemptLogModel = Backbone.Model.extend({

    url: function() {
        return "/api/attempt_log/" + this.get("exercise_id");
    }

})

window.AttemptLogCollection = Backbone.Collection.extend({

    model: AttemptLogModel,

    url: function() {
        return "/api/attempt_log/" + this.options.exercise_id
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

}

var hintsResetPoints = true; // Sometimes it's OK to view hints (like, after a correct answer)
var answerGiven = null;

window.ExerciseProgressView = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.listenTo(this.model, "change", this.render);

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

