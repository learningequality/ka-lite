window.ExercisePerseusView = Backbone.View.extend({

    template: HB.template("exercise/exercise"),

    initialize: function() {

        _.bindAll(this);

        // load the info about the exercise itself
        this.data_model = new ExerciseDataModel({exercise_id: this.options.exercise_id});
        // this.data_model.fetch();

        this.render();

        _.defer(this.initialize_khan_exercises_listeners);

    },

    events: {
        "submit .answer-form": "answer_form_submitted"
    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.initialize_listeners();

        if ($("#exercise-inline-style").length === 0) {
            // dummy style container that khan-exercises uses to dynamically add styling to an exercise
            $("head").append("<style id='exercise-inline-style'></style>");
        }

    },

    initialize_listeners: function() {

        // Catch the "next question" button click event -- needs to be explicit (not in "events")
        this.$("#next-question-button").click(this.next_question_clicked);

        this.listenTo(this.data_model, "change:title", this.update_title);

        this.listenTo(this.data_model, "change:related_videos", this.render_related_videos);

    },

    initialize_khan_exercises_listeners: function() {

        Khan.loaded.then(this.khan_loaded);

        $(Exercises).bind("checkAnswer", this.check_answer);

        $(Exercises).bind("gotoNextProblem", this.goto_next_problem);

        // TODO (rtibbles): Make this nice, not horrible.
        $(Exercises).bind("newProblem", function (ev, data) {
            if (data.answerType=="number"||data.answerType=="decimal"||data.answerType=="rational"||data.answerType=="improper"||data.answerType=="mixed"){
                window.softwareKeyboardView = new SoftwareKeyboardView({
                    el: $("#solutionarea")
                });
            }
        });

        // some events we only care about if the user is logged in
        if (statusModel.get("is_logged_in")) {
            $(Exercises).bind("hintUsed", this.hint_used);
            $(Exercises).bind("newProblem", this.problem_loaded);
        }

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

    check_answer: function() {

        var data = Khan.scoreInput();

        this.trigger("check_answer", data);

    },

    next_question_clicked: function() {

        this.trigger("ready_for_next_question");

    },

    problem_loaded: function(ev, data) {
        this.trigger("problem_loaded", data);
    },

    answer_form_submitted: function(e) {
        e.preventDefault();
        this.$("#check-answer-button").click();
    },

    update_title: function() {
        this.$(".exercise-title").text(this.data_model.get("title"));
    },

    hint_used: function() {
        this.trigger("hint_used");
    },

    goto_next_problem: function() {

    },

    khan_loaded: function() {
        $(Exercises).trigger("problemTemplateRendered");
        this.trigger("ready_for_next_question");
    },

    render_related_videos: function() {
        if (!this.related_video_view) {
            this.related_video_view = new ExerciseRelatedVideoView({el: this.$(".exercise-related-video-wrapper")});
        }
        var related_videos = this.data_model.get("related_videos");
        this.related_video_view.render({
            has_related_videos: related_videos.length > 0,
            first_video: related_videos[0],
            other_videos: related_videos.slice(1)
        });
    }

});

window.ExercisePerseusPracticeView = Backbone.View.extend({

    initialize: function() {

        var self = this;

        _.bindAll(this);


        window.statusModel.loaded.then(function() {

            self.exercise_view = new ExerciseView({
                el: self.el,
                exercise_id: self.options.exercise_id
            });

            self.exercise_view.on("ready_for_next_question", self.ready_for_next_question);
            self.exercise_view.on("hint_used", self.hint_used);
            self.exercise_view.on("problem_loaded", self.problem_loaded);

            self.hint_view = new ExerciseHintView({
                el: self.$(".exercise-hint-wrapper")
            });

            if (window.statusModel.get("is_logged_in")) {

                self.exercise_view.on("check_answer", self.check_answer);

                // load the data about the user's overall progress on the exercise
                self.log_collection = new ExerciseLogCollection([], {exercise_id: self.options.exercise_id});
                var log_collection_deferred = self.log_collection.fetch();

                // load the last 10 (or however many) specific attempts the user made on self exercise
                self.attempt_collection = new AttemptLogCollection([], {exercise_id: self.options.exercise_id, context_type: self.options.context_type});
                var attempt_collection_deferred = self.attempt_collection.fetch();

                // wait until both the exercise and attempt logs have been loaded before continuing
                self.user_data_loaded_deferred = $.when(log_collection_deferred, attempt_collection_deferred);
                self.user_data_loaded_deferred.then(self.user_data_loaded);

            }
        });
    },

    display_message: function() {

        var context = {
            numerator: ExerciseParams.STREAK_CORRECT_NEEDED,
            denominator: ExerciseParams.STREAK_WINDOW
        };

        if (!this.log_model.get("complete")) {
            if (this.log_model.get("attempts") !== undefined) { // don't display a message if the user is already partway into the streak
                var msg = "";
            } else {
                var msg = gettext("Answer %(numerator)d out of the last %(denominator)d questions correctly to complete your streak.");
            }
        } else {
            context.remaining = ExerciseParams.FIXED_BLOCK_EXERCISES - this.log_model.attempts_since_completion();
            if (!this.current_attempt_log.get("correct") && !this.current_attempt_log.get("complete")) {
                context.remaining++;
            }
            if (context.remaining > 1) {
                var msg = gettext("You have completed your streak.") + " " + gettext("There are %(remaining)d additional questions in this exercise.");
            } else if (context.remaining == 1) {
                var msg = gettext("You have completed your streak.") + " " + gettext("There is 1 additional question in this exercise.");
            } else {
                var msg = gettext("You have completed this exercise.");
            }
        }

        show_message("info", sprintf(msg, context), "id_exercise_status");
    },

    user_data_loaded: function() {

        // get the exercise log model from the queried collection
        this.log_model = this.log_collection.get_first_log_or_new_log();

        // add some dummy attempt logs if needed, to match it up with the exercise log
        // (this is needed because attempt logs were not added until 0.13.0, so many older users have only exercise logs)
        if (this.attempt_collection.length < ExerciseParams.STREAK_WINDOW) {
            var exercise_log_streak_progress = Math.min(this.log_model.get("streak_progress"), 100);
            while (this.attempt_collection.get_streak_progress_percent() < exercise_log_streak_progress) {
                this.attempt_collection.add({correct: true, complete: true, points: this.get_points_per_question()});
            }
        }

        // if the previous attempt was not yet complete, load it up again as the current attempt log model
        if (this.attempt_collection.length > 0 && !this.attempt_collection.at(0).get("completed")) {
            this.current_attempt_log = this.attempt_collection.at(0);
        }

        // store the number of points that are currently in the ExerciseLog, so we can calculate the difference
        // once it changes, for updating the "total points" in the nav bar display
        this.starting_points = this.log_model.get("points");

        this.progress_view = new ExerciseProgressView({
            el: this.$(".exercise-progress-wrapper"),
            model: this.log_model,
            collection: this.attempt_collection
        });

        this.display_message();

    },

    problem_loaded: function(data) {
        this.current_attempt_log.add_response_log_event({
            type: "loaded"
        });
        // if the question hasn't yet been answered (and hence saved), mark the current time as the question load time
        if (this.current_attempt_log.isNew()) {
            this.current_attempt_log.set("timestamp", window.statusModel.get_server_time());
        }

    },

    initialize_new_attempt_log: function(data) {

        var defaults = {
            exercise_id: this.options.exercise_id,
            user: window.statusModel.get("user_uri"),
            context_type: this.options.context_type || "",
            context_id: this.options.context_id || "",
            language: "", // TODO(jamalex): get the current exercise language
            version: window.statusModel.get("version")
        };

        data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        return this.current_attempt_log;

    },

    check_answer: function(data) {

        var check_answer_button = $("#check-answer-button");

        check_answer_button.parent().stop(jumpedToEnd=true)

        check_answer_button.toggleClass("orange", !data.correct).toggleClass("green", data.correct);
        // If answer is incorrect, button turns orangish-red; if answer is correct, button turns back to green (on next page).

        // increment the response count
        this.current_attempt_log.set("response_count", this.current_attempt_log.get("response_count") + 1);

        this.current_attempt_log.add_response_log_event({
            type: "answer",
            answer: data.guess,
            correct: data.correct
        });

        // update and save the exercise and attempt logs
        this.update_and_save_log_models("answer_given", data);

        this.display_message();

    },

    hint_used: function() {

        this.current_attempt_log.add_response_log_event({
            type: "hint"
        });

        this.update_and_save_log_models("hint_used", {correct: false, guess: ""});
    },

    get_points_per_question: function() {
        return this.attempt_collection.calculate_points_per_question(this.exercise_view.data_model.get("basepoints"));
    },

    update_and_save_log_models: function(event_type, data) {

        var self = this;

        // if current attempt log has not been saved, then this is the user's first response to the question
        if (this.current_attempt_log.isNew()) {

            this.current_attempt_log.set({
                correct: data.correct,
                answer_given: data.guess,
                points: data.correct ? this.get_points_per_question() : 0,
                time_taken: new Date(window.statusModel.get_server_time()) - new Date(this.current_attempt_log.get("timestamp"))
            });
            this.attempt_collection.add_new(this.current_attempt_log);

            // only change the streak progress and points if we're not already complete
            if (!this.log_model.get("complete")) {
                this.log_model.set({
                    streak_progress: this.attempt_collection.get_streak_progress_percent(),
                    points: this.attempt_collection.get_streak_points()
                });
            }

            this.log_model.set({
                attempts: this.log_model.get("attempts") + 1
            });

            this.log_model.save()
                .then(function(data) {
                    // update the top-right point display, now that we've saved the points successfully
                    window.statusModel.set("newpoints", self.log_model.get("points") - self.starting_points);
                });

            this.$(".hint-reminder").hide(); // hide message about hints

        }

        // if a correct answer was given, then mark the attempt log as complete
        if (data.correct) {
            this.current_attempt_log.set({
                complete: true
            });
        }

        this.current_attempt_log.save();

    },

    ready_for_next_question: function() {

        var self = this;

        if (this.user_data_loaded_deferred) {

            this.user_data_loaded_deferred.then(function() {

                // if this is the first attempt, or the previous attempt was complete, start a new attempt log
                if (!self.current_attempt_log || self.current_attempt_log.get("complete")) {
                    self.exercise_view.load_question(); // will generate a new random seed to use
                    self.initialize_new_attempt_log({seed: self.exercise_view.data_model.get("seed")});
                } else { // use the seed already established for this attempt
                    self.exercise_view.load_question({seed: self.current_attempt_log.get("seed")});
                }

                self.$(".hint-reminder").show(); // show message about hints

            });

        } else { // not logged in, but just load the next question, for kicks

            self.exercise_view.load_question();

        }


    }

});