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

}

var hintsResetPoints = true; // Sometimes it's OK to view hints (like, after a correct answer)
var answerGiven = null;

window.ExerciseWrapperView = Backbone.View.extend({

    template: HB.template("exercise/exercise-wrapper"),

    initialize: function() {

        this.render();

    },

    events: {
        // "change .video-language-selector": "languageChange"
    },

    render: function() {

        this.$el.html(this.template(this.model.attributes));

        // this.videoPlayerView = new VideoPlayerView({
        //     el: this.$(".video-player-container"),
        //     model: this.model
        // });

        // this.videoPointView = new VideoPointView({
        //     el: this.$(".points-container"),
        //     model: this.model
        // });

    },

    initialize_khan_exercises_listeners: function() {

    }

});


$(function() {

    window.exerciseWrapperView = new ExerciseWrapperView({
        el: $(".exercise-wrapper"),
        model: new Backbone.Model // temp
    });

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

    basepoints = exerciseData.basepoints;

    $("#next-question-button").click(function() {
        _.defer(function() {
            updateQuestionPoints(false);
            exerciseData.hintUsed = false;
            exerciseData.seed = Math.floor(Math.random() * 1000);
            $(Exercises).trigger("readyForNextProblem", {userExercise: exerciseData});
        });
    });

    adjust_scratchpad_margin();

    $("#scratchpad-show").click(function(){
        _.defer(function() {
            adjust_scratchpad_margin();
        });
    });

});

function adjust_scratchpad_margin(){
    if (Khan.scratchpad.isVisible()) {
        $(".current-card-contents #problemarea").css("margin-top", "50px");
    } else {
        $(".current-card-contents #problemarea").css("margin-top", "10px");
    }
}
