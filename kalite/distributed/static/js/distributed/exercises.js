/*

TODO:
    - Fire an event when question has been loaded and displayed (to be used for marking start time on log.)

*/

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

        // store the provided seed as an object attribute, so it will be available after a fetch
        this.listenTo(this, "change:seed", function() { this.seed = this.get("seed") || this.seed; });

    },

    url: function () {
        return "/api/exercise/" + this.get("exercise_id");
    },

    update_if_needed_then: function(callback) {
        if (this.get("exercise_id") !== this.get("name")) {
            this.fetch().then(callback);
        } else {
            _.defer(callback);
        }
    },

    // convert this data into the structure needed by khan-exercises
    as_user_exercise: function () {
        return {
            "basepoints": this.get("basepoints"),
            "description": this.get("description"),
            "title": this.get("display_name"),
            "seed": this.seed,
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

        // keep track of how many points we started out with
        this.listenToOnce(this, "change:points", function() { self.starting_points = self.get("points") });

    },

    save: function() {

        var self = this;

        var already_complete = this.get("complete");

        if (this.get("attempts") > 20 && !this.get("complete")) {
            this.set("struggling", true);
        }

        this.set("complete", this.streak_progress >= 100);

        if (!already_complete && this.get("complete")) {
            this.set("struggling", false);
            this.set("completion_timestamp", statusModel.get_server_time().toJSON());
            this.set("attempts_before_completion", this.get("attempts"));
        }

        Backbone.Model.prototype.save.call(this)
            .success(function(data) {
                // update the top-right point display, now that we've saved the points successfully
                statusModel.set("newpoints", self.get("points") - self.starting_points);
            });
    },

    urlRoot: "/api/exerciselog/"

});

window.ExerciseLogCollection = Backbone.Collection.extend({

    model: ExerciseLogModel,

    initialize: function(options) {
        this.exercise_id = options.exercise_id;
        this.status_model = options.status_model;
    },

    url: function() {
        return "/api/exerciselog/?" + $.param({
            "exercise_id": this.exercise_id,
            "user": this.status_model.get("user_id")
        });
    }

});


window.AttemptLogModel = Backbone.Model.extend({
    /*
    Contains data about the user's response to a particular exercise instance.
    */

    defaults: {
        complete: false,
        points: 0,
        context_type: "",
        context_id: ""
    },

    initialize: function(options) {

    },

    url: function() {
        return "/api/attempt_log/" + this.get("exercise_id");
    }

});


window.AttemptLogCollection = Backbone.Collection.extend({

    model: AttemptLogModel,

    initialize: function(options) {
        this.exercise_id = options.exercise_id;
        this.status_model = options.status_model;
    },

    url: function() {
        return setGetParamDict("/api/attemptlog/",{
            "exercise_id": this.exercise_id,
            "user": this.status_model.get("user_id")
        });
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

window.ExerciseHintView = Backbone.View.extend({

    template: HB.template("exercise/exercise-hint"),

    initialize: function() {

        _.bindAll(this);

        this.render();

        // this.listenTo(this.model, "change", this.render);

    },

    render: function() {
        // this.$el.html(this.template(this.data_model.attributes));
        this.$el.html(this.template());
    }

});


window.ExerciseProgressView = Backbone.View.extend({

    template: HB.template("exercise/exercise-progress"),

    initialize: function() {

        _.bindAll(this);

        this.render();

        this.listenTo(this.model, "change", this.update_streak_bar);
        // this.listenTo(this.collection, "change", this.render);

    },

    render: function() {
        // this.$el.html(this.template(this.data_model.attributes));
        this.$el.html(this.template());
    },

    update_streak_bar: function() {
        // update the streak bar UI
        this.$("#streakbar .progress-bar").css("width", this.model.get("streak_progress") + "%");
        this.$("#totalpoints").html(this.model.get("points") > 0 ? this.model.get("points") : "");
        if (this.model.get("streak_progress") >= 100) {
            this.$("#streakbar .progress-bar").addClass("completed");
            this.$(".hint-reminder").hide();
        }
    }
});

window.ExerciseView = Backbone.View.extend({

    template: HB.template("exercise/exercise"),

    initialize: function() {

        _.bindAll(this);

        // load the info about the exercise itself
        this.data_model = new ExerciseDataModel({exercise_id: this.options.exercise_id});
        this.data_model.fetch();


        this.render();

        this.initialize_khan_exercises_listeners();

        // this.adjust_scratchpad_margin();

    },

    events: {
        "click #scratchpad-show": "adjust_scratchpad_margin",
        "submit .answer-form": "answer_form_submitted"
    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.initialize_listeners();

    },

    initialize_listeners: function() {

        // Catch the "next question" button click event -- needs to be explicit (not in "events")
        this.$("#next-question-button").click(this.next_question_clicked);

        this.listenTo(this.data_model, "change:title", this.update_title);

    },

    initialize_khan_exercises_listeners: function() {

        var self = this;

        $(Khan).bind("loaded", this.khan_loaded);

        $(Exercises).bind("checkAnswer", function() { self.trigger("check_answer", Khan.scoreInput()); });

        $(Exercises).bind("gotoNextProblem", this.goto_next_problem);

        $(Exercises).bind("hintUsed", this.hint_used);

    },

    initialize_new_attempt_model: function(data) {

        var defaults = {
            user: window.statusModel.get("user"),
            exercise_id: this.data_model.get("exercise_id"),
            points: 0,
        };

        this.attempt_model = new AttemptLogModel();

    },

    load_question: function(question_data) {

        var self = this;

        var defaults = {
            seed: Math.floor(Math.random() * 1000)
        };

        var question_data = $.extend(defaults, question_data);

        this.data_model.set(question_data);

        this.$("#workarea").html("<center>" + gettext("Loading...") + "</center>");

        this.data_model.update_if_needed_then(function() {
            var userExercise = self.data_model.as_user_exercise();
            $(Exercises).trigger("readyForNextProblem", {userExercise: userExercise});
        });

    },

    next_question_clicked: function() {

        this.trigger("ready_for_next_question");

        // TODO
        // updateQuestionPoints(false);
        // this.attempt_model.set("hint_used", false);

    },

    adjust_scratchpad_margin: function() {
        if (Khan.scratchpad.isVisible()) {
            this.$(".current-card-contents #problemarea").css("margin-top", "50px");
        } else {
            this.$(".current-card-contents #problemarea").css("margin-top", "10px");
        }
    },

    answer_form_submitted: function(e) {
        e.preventDefault();
        this.$("#check-answer-button").click();
    },

    update_title: function() {
        this.$(".exercise-title").text(this.data_model.get("title"));
    },

    hint_used: function() {
        if (this.log_model.get("hintUsed") || !hintsResetPoints) { // only register the first hint used on a question
            return;
        }
        this.log_model.set("hintUsed", true);
        this.update_streak_progress(false);
    },

    goto_next_problem: function() {
        // When ready for the next problem, hints matter again!
        hintsResetPoints = true;
        this.$(".hint-reminder").toggle(hintsResetPoints); // hide/show message about hints
    },

    khan_loaded: function() {
        $(Exercises).trigger("problemTemplateRendered");
        this.trigger("ready_for_next_question");
    },

    disable_answer_button: function() {
        this.$(".answer-buttons-enabled").hide();
        this.$(".answer-buttons-disabled").show();
    },

    enable_answer_button: function() {
        this.$(".answer-buttons-disabled").hide();
        this.$(".answer-buttons-enabled").show();
    }

});


window.ExercisePracticeView = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        // load the data about the user's overall progress on the exercise
        this.log_model = new ExerciseLogModel({exercise_id: this.options.exercise_id});
        var log_model_deferred = this.log_model.fetch();

        // load the last 10 specific attempts the user made on this exercise
        this.attempt_collection = new AttemptLogCollection({exercise_id: this.options.exercise_id, status_model: window.statusModel});
        var attempt_collection_deferred = this.attempt_collection.fetch();

        this.exercise_view = new ExerciseView({
            el: this.el,
            exercise_id: this.options.exercise_id
        });

        // disable the answer button for now; it will be re-enabled once we have the user data
        this.exercise_view.disable_answer_button();

        this.hint_view = new ExerciseHintView({
            el: this.$(".exercise-hint-wrapper"),
            model: this.log_model
        });

        this.exercise_view.on("check_answer", this.check_answer);
        this.exercise_view.on("ready_for_next_question", this.ready_for_next_question);

        $.when([log_model_deferred, attempt_collection_deferred]).then(this.user_data_loaded);

    },

    user_data_loaded: function() {

        this.progress_view = new ExerciseProgressView({
            el: this.$(".exercise-progress-wrapper"),
            model: this.log_model,
            collection: this.attempt_collection
        });

        this.exercise_view.enable_answer_button();

    },

    check_answer: function(data) {

        // data.guess

        // updatePercentCompleted(data.correct);

        // after giving a correct answer, no penalty for viewing a hint.
        // after giving an incorrect answer, penalty for giving a hint (as a correct answer will give you points)
        // hintsResetPoints = !data.correct;
        // this.$(".hint-reminder").toggle(hintsResetPoints); // hide/show message about hints



    },

    ready_for_next_question: function() {
        this.exercise_view.load_question();
    }

});


window.ExerciseTestView = Backbone.View.extend({

    initialize: function() {

        _.bindAll(this);

        this.exercise_view = new ExerciseView({
            el: this.el,
            exercise_id: this.options.exercise_id
        });

        this.exercise_view.on("check_answer", this.check_answer);

    },

    check_answer: function(data) {

        // prevent the "check answer" button from shaking on incorrect answers
        this.$("#check-answer-button").parent().stop(jumpedToEnd=true);

    }

});
