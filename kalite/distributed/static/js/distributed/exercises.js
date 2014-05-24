window.ExerciseDataModel = Backbone.Model.extend({
    /*
    Contains data about an exercise itself, with no user-specific data.
    */

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

        this.listenTo(this, 'change', this.update_exercise_data);

    },

    url: function () {
        return "/api/exercise/" + this.get("exercise_id");
    },

    // update the global "exerciseData" structure needed by khan-exercises
    update_exercise_data: function () {
        window.exerciseData = {
            "basepoints": this.get("basepoints"),
            "description": this.get("description"),
            "title": this.get("display_name"),
            "exerciseModel": {
                "displayName": this.get("display_name"),
                "name": this.get("name"),
                "secondsPerFastProblem": this.get("seconds_per_fast_problem"),
                "authorName": this.get("author_name"),
                "relatedVideos": this.get("related_videos"),
                "fileName": this.get("file_name")
            },
            "exerciseProgress": {
                "level": "" // needed to keep khan-exercises from blowing up
            }
        };
    }
});

window.ExerciseLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current exercise.
    */

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
        return "/api/exercise_log/" + this.get("exercise_id");
    }

})

window.AttemptLogModel = Backbone.Model.extend({
    /*
    Contains data about the user's response to a particular exercise instance.
    */

    url: function() {
        return "/api/attempt_log/" + this.get("exercise_id");
    }

});

window.AttemptLogCollection = Backbone.Collection.extend({

    model: AttemptLogModel,

    initialize: function(options) {
        this.exercise_id = options.exercise_id;
    },

    url: function() {
        return "/api/attempt_log/" + this.exercise_id;
    }

});

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
            inc = Math.ceil(exerciseData.basepoints*bump);
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
        // this.listenTo(this.collection, "change", this.render);

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

        // load the info about the exercise itself
        this.data_model = new ExerciseDataModel({exercise_id: this.options.exercise_id});
        this.data_model.fetch();

        // load the data about the user's overall progress on the exercise
        this.log_model = new ExerciseLogModel({exercise_id: this.options.exercise_id});
        this.log_model.fetch();

        // load the last 10 specific attempts the user made on this exercise
        this.attempt_collection = new AttemptLogCollection({exercise_id: this.options.exercise_id});
        this.attempt_collection.fetch();

        this.render();

        this.exercise_progress_view = new ExerciseProgressView({
            el: this.$(".exercise-progress-wrapper"),
            model: this.log_model,
            collection: this.attempt_collection
        });

        this.initialize_khan_exercises_listeners();

        // this.adjust_scratchpad_margin();

    },

    events: {
        "click #scratchpad-show": "adjust_scratchpad_margin"
    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.initialize_listeners();

    },

    initialize_listeners: function() {

        this.$("#next-question-button").click(this.next_question_clicked); // needs to be explicit (not in "events")

        this.listenTo(this.data_model, "change:title", this.update_title);

    },

    initialize_khan_exercises_listeners: function() {

        var that = this;

        $(Khan).bind("loaded", function() {
            that.data_model.set("seed", Math.floor(Math.random() * 1000));
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
    },

    update_title: function() {
        this.$(".exercise-title").text(this.data_model.get("title"));
    }

});
