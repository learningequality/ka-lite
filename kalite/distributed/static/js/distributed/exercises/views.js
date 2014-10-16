window.ExerciseView = Backbone.View.extend({

    template: HB.template("exercise/exercise"),

    initialize: function() {

        _.bindAll(this);

        // load the info about the exercise itself
        this.data_model = new ExerciseDataModel({exercise_id: this.options.exercise_id});
        if (this.data_model.exercise_id) {
            this.data_model.fetch();
        }

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

        // TODO-BLOCKER(jamalex): does this need to wait on something, to avoid race conditions?
        _.defer(this.khan_loaded);
        if (Khan.loaded) {
            Khan.loaded.then(this.khan_loaded);
        }


        $(Exercises).bind("checkAnswer", this.check_answer);

        $(Exercises).bind("gotoNextProblem", this.goto_next_problem);

        // TODO (rtibbles): Make this nice, not horrible.
        $(Exercises).bind("newProblem", function (ev, data) {
            if (data.answerType=="number"||data.answerType=="decimal"||data.answerType=="rational"||data.answerType=="improper"||data.answerType=="mixed"){
                self.software_keyboard_view = new SoftwareKeyboardView({
                    el: self.$("#solutionarea")
                });
            }
        });

        // some events we only care about if the user is logged in
        if (statusModel.get("is_logged_in")) {
            $(Exercises).bind("hintUsed", this.hint_used);
            $(Exercises).bind("newProblem", this.problem_loaded);
        }

    },

    load_exercises_when_ready: function() {
        var self = this;
        Khan.loaded.then(function() {

            var userExercise = self.data_model.as_user_exercise();
            $(Exercises).trigger("readyForNextProblem", {userExercise: userExercise});

        });
    },

    load_question: function(question_data) {

        var self = this;

        var defaults = {
            seed: Math.floor(Math.random() * 200),
            framework: "khan-exercises"
        };

        var question_data = $.extend(defaults, question_data);

        this.data_model.set(question_data);

        this.$("#workarea").html("<center>" + gettext("Loading...") + "</center>");

        this.data_model.update_if_needed_then(function() {

            var framework = self.data_model.get_framework();

            Exercises.setCurrentFramework(framework);

            if (framework == "khan-exercises") {

                if (Khan.loaded === undefined) {
                    $.getScript(KHAN_EXERCISES_SCRIPT_URL, self.load_exercises_when_ready);
                } else {
                    self.load_exercises_when_ready();
                }

            } else if (framework == "perseus") {

                $(Exercises).trigger("clearExistingProblem");

                var i = Math.floor(Math.random() * self.data_model.get("all_assessment_items").length);
                var item = new AssessmentItemModel({id: self.data_model.get("all_assessment_items")[i].id});

                item.fetch().then(function() {
                    Exercises.PerseusBridge.load().then(function() {
                        Exercises.PerseusBridge.render_item(item.get_item_data());
                        // Exercises.PerseusBridge.render_item(item_data);
                        $(Exercises).trigger("newProblem", {
                            userExercise: null,
                            numHints: Exercises.PerseusBridge.itemRenderer.getNumHints()
                        });
                    });
                });

            } else {
                throw "Unknown framework: " + framework;
            }

        });

    },


    check_answer: function() {
        var data;
        if (this.data_model.get_framework() == "khan-exercises") {
            data = Khan.scoreInput();
        } else {
            data = Exercises.PerseusBridge.scoreInput();
        }

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
        $(Exercises).trigger("clearExistingProblem");
    },

    update_title: function() {
        this.$(".exercise-title").text(this.data_model.get("title"));
    },

    hint_used: function() {
        this.trigger("hint_used");
    },

    goto_next_problem: function() {

    },

    suppress_button_feedback: function() {
        // hide the "Correct! Next question..." button
        this.$("#next-question-button").hide();

        // hide the "Next Question" button and prevent it from shaking
        this.$("#check-answer-button")
            .hide()
            .stop(jumpedToEnd=true)
            .css("width", "100%")
                .parent()
                .stop(jumpedToEnd=true);
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
    },

    close: function() {
        if (this.related_video_view) {
            this.related_video_view.remove();
        }
        this.remove();
    }

});


window.ExercisePracticeView = Backbone.View.extend({

    initialize: function() {

        var self = this;

        _.bindAll(this);

        window.statusModel.loaded.then(function() {

            self.exercise_view = new ExerciseView({
                el: self.el,
                exercise_id: self.options.exercise_id
            });

            self.listenTo(self.exercise_view, "ready_for_next_question", self.ready_for_next_question);
            self.listenTo(self.exercise_view, "hint_used", self.hint_used);
            self.listenTo(self.exercise_view, "problem_loaded", self.problem_loaded);

            self.hint_view = new ExerciseHintView({
                el: self.$(".exercise-hint-wrapper")
            });

            self.listenTo(self.exercise_view, "check_answer", self.check_answer);

            if (window.statusModel.get("is_logged_in")) {

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
        
        var msg;

        if (!this.log_model.get("complete")) {
            if (this.log_model.get("attempts") > 0) { // don't display a message if the user is already partway into the streak
                msg = "";
            } else {
                msg = gettext("Answer %(numerator)d out of the last %(denominator)d questions correctly to complete your streak.");
            }
        } else {
            context.remaining = ExerciseParams.FIXED_BLOCK_EXERCISES - this.log_model.attempts_since_completion();
            if (!this.current_attempt_log.get("correct") && !this.current_attempt_log.get("complete")) {
                context.remaining++;
            }
            if (context.remaining > 1) {
                msg = gettext("You have completed your streak.") + " " + gettext("There are %(remaining)d additional questions in this exercise.");
            } else if (context.remaining == 1) {
                msg = gettext("You have completed your streak.") + " " + gettext("There is 1 additional question in this exercise.");
            } else {
                msg = gettext("You have completed this exercise.");
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

        check_answer_button.toggleClass("orange", !data.correct).toggleClass("green", data.correct);
        // If answer is incorrect, button turns orangish-red; if answer is correct, button turns back to green (on next page).

        if (window.statusModel.get("is_logged_in")) {

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

        }

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


    },

    close: function() {
        this.exercise_view.close();
        if (this.hint_view) {
            this.hint_view.remove();
        }
        if (this.progress_view) {
            this.progress_view.remove();
        }
        this.remove();
    }

});


window.ExerciseTestView = Backbone.View.extend({

    start_template: HB.template("exercise/test-start"),

    stop_template: HB.template("exercise/test-stop"),

    initialize: function() {

        _.bindAll(this);

        if (window.statusModel.get("is_logged_in")) {

            // load the data about this particular test
            this.test_model = new TestDataModel({test_id: this.options.test_id});
            var test_model_deferred = this.test_model.fetch();

            // load the data about the user's overall progress on the test
            this.log_collection = new TestLogCollection([], {test_id: this.options.test_id});
            var log_collection_deferred = this.log_collection.fetch();

            this.user_data_loaded_deferred = $.when(log_collection_deferred, test_model_deferred).then(this.user_data_loaded);

        }

    },

    finish_test: function() {
        if (this.log_model.get("complete")) {
            this.$el.html(this.stop_template());

            // TODO-BLOCKER(jamalex): with exam mode redirect enabled, where does this lead you?
            this.$(".stop-test").click(function() { window.location.href = "/"; });

            return true;
        }
    },

    user_data_loaded: function() {

        // get the test log model from the queried collection
        if(!this.log_model){
            this.log_model = this.log_collection.get_first_log_or_new_log();
        }

        if(!this.log_model.get("started")){
            this.$el.html(this.start_template());

            $("#start-test").click(this.start_test);

        } else {

            if(this.log_model.get("complete")){
                this.finish_test();
            } else {

                this.listenTo(this.log_model, "complete", this.finish_test);

                var question_data = this.log_model.get_item_data(this.test_model);

                var data = $.extend({el: this.el}, question_data);

                this.initialize_new_attempt_log(question_data);

                this.exercise_view = new ExerciseView(data);
                this.exercise_view.$("#check-answer-button").attr("value", gettext("Submit Answer"));

                // don't render the related videos box on tests
                this.exercise_view.stopListening(this.data_model, "change:related_videos");

                this.listenTo(this.exercise_view, "check_answer", this.check_answer);
                this.listenTo(this.exercise_view, "problem_loaded", this.problem_loaded);
                this.listenTo(this.exercise_view, "ready_for_next_question", this.ready_for_next_question);
            }
        }

    },

    start_test: function() {
        this.log_model.set({"started": true});
        model_save_deferred = this.log_model.save();
        this.user_data_loaded();
        this.ready_for_next_question();
        this.problem_loaded();
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
            context_type: "test",
            context_id: this.options.test_id || "",
            language: "", // TODO(jamalex): get the current exercise language
            version: window.statusModel.get("version")
        };

        var data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        return this.current_attempt_log;

    },

    check_answer: function(data) {

        this.exercise_view.suppress_button_feedback();

        // increment the response count
        this.current_attempt_log.set("response_count", this.current_attempt_log.get("response_count") + 1);

        this.current_attempt_log.add_response_log_event({
            type: "answer",
            answer: data.guess,
            correct: data.correct
        });

        // update and save the exercise and attempt logs
        this.update_and_save_log_models("answer_given", data);
    },

    update_and_save_log_models: function(event_type, data) {

        // if current attempt log has not been saved, then this is the user's first response to the question
        if (this.current_attempt_log.isNew()) {

            this.current_attempt_log.set({
                correct: data.correct,
                answer_given: data.guess,
                time_taken: new Date(window.statusModel.get_server_time()) - new Date(this.current_attempt_log.get("timestamp")),
                complete: true
            });

            this.log_model.set({
                index: this.log_model.get("index") + 1
            });

            if(data.correct) {
                this.log_model.set({
                    total_correct: this.log_model.get("total_correct") + 1
                });
            }

            this.log_model.save();

        }

        this.current_attempt_log.save();

        this.ready_for_next_question();

    },

    ready_for_next_question: function() {

        var self = this;

        this.user_data_loaded_deferred.then(function() {

            self.exercise_view.load_question(self.log_model.get_item_data());
            self.initialize_new_attempt_log(self.log_model.get_item_data());
            $("#next-question-button").remove();

        });

    },

    close: function() {
        this.exercise_view.close();
        this.remove();
    }

});


window.ExerciseQuizView = Backbone.View.extend({

    stop_template: HB.template("exercise/quiz-stop"),

    initialize: function(options) {

        _.bindAll(this);

        this.points = 0;

        if (window.statusModel.get("is_logged_in")) {

            this.quiz_model = options.quiz_model;

            // load the data about the user's overall progress on the test
            this.log_collection = new QuizLogCollection([], {quiz: this.options.context_id});
            var log_collection_deferred = this.log_collection.fetch();

            this.user_data_loaded_deferred = log_collection_deferred.then(this.user_data_loaded);

        } else {

            // TODO(jamalex): why can't poor account-less users quiz themselves? :(
            this.$el.html("<h3>" + gettext("Sorry, you must be logged in to do a quiz.") + "</h3><br/><br/><br/>");

        }

    },

    finish_quiz: function() {
        this.$el.html(this.stop_template({
            correct: this.log_model.get_latest_response_log_item(),
            total_number: this.log_model.get("total_number")
        }));

        if(this.log_model.get("attempts")==1){
            if(this.points > 0){
                var purchased_model = new PurchasedStoreItemModel({
                    item: "/api/store/storeitem/gift_card/",
                    purchased_at: window.statusModel.get_server_time(),
                    reversible: false,
                    context_id: 0, // TODO-BLOCKER: put the current unit in here
                    context_type: "unit",
                    user: window.statusModel.get("user_uri"),
                    value: this.points
                });
                purchased_model.save();

                statusModel.set("newpoints", statusModel.get("newpoints") + this.points);
            }
        }

        var self = this;

        $("#stop-quiz").click(function(){self.trigger("complete");});
    },

    user_data_loaded: function() {

        // get the quiz log model from the queried collection
        if(!this.log_model){
            this.log_model = this.log_collection.get_first_log_or_new_log();
        }

        this.listenTo(this.log_model, "complete", this.finish_quiz);

        var question_data = this.log_model.get_item_data(this.quiz_model);

        var data = $.extend({el: this.el}, question_data);

        this.exercise_view = new ExerciseView(data);
        this.exercise_view.$("#check-answer-button").attr("value", gettext("Submit Answer"));

        this.listenTo(this.exercise_view, "check_answer", this.check_answer);
        this.listenTo(this.exercise_view, "ready_for_next_question", this.ready_for_next_question);
        this.listenTo(this.exercise_view, "problem_loaded", this.problem_loaded);

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
            context_type: "quiz",
            context_id: this.options.context_id || "",
            language: "", // TODO(jamalex): get the current exercise language
            version: window.statusModel.get("version"),
            seed: this.exercise_view.data_model.seed
        };

        var data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        return this.current_attempt_log;

    },

    check_answer: function(data) {

        this.exercise_view.suppress_button_feedback();

        // increment the response count
        this.current_attempt_log.set("response_count", this.current_attempt_log.get("response_count") + 1);

        this.current_attempt_log.add_response_log_event({
            type: "answer",
            answer: data.guess,
            correct: data.correct
        });

        // update and save the exercise and attempt logs
        this.update_and_save_log_models("answer_given", data);
    },

    update_and_save_log_models: function(event_type, data) {

        // if current attempt log has not been saved, then this is the user's first response to the question
        if (this.current_attempt_log.isNew()) {

            this.current_attempt_log.set({
                correct: data.correct,
                answer_given: data.guess,
                time_taken: new Date(window.statusModel.get_server_time()) - new Date(this.current_attempt_log.get("timestamp")),
                complete: true
            });

            this.log_model.set({
                index: this.log_model.get("index") + 1
            });

            if((!this.log_model.get("complete")) && data.correct){
                this.points += this.exercise_view.data_model.get("basepoints");
            }

            this.log_model.add_response_log_item(data);

            this.log_model.save();

        }

        this.current_attempt_log.save();

        this.ready_for_next_question();

    },

    ready_for_next_question: function() {

        var self = this;

        this.user_data_loaded_deferred.then(function() {

            self.exercise_view.load_question(self.log_model.get_item_data());
            self.initialize_new_attempt_log(self.log_model.get_item_data());

        });

    },

    close: function() {
        if (this.exercise_view) {
            this.exercise_view.close();
        }
        this.remove();
    }

});


window.ExerciseHintView = Backbone.View.extend({

    template: HB.template("exercise/exercise-hint"),

    initialize: function() {

        _.bindAll(this);

        this.render();

    },

    render: function() {
            this.$el.html(this.template());
    }

});


window.ExerciseProgressView = Backbone.View.extend({

    template: HB.template("exercise/exercise-progress"),

    initialize: function() {

        _.bindAll(this);

        this.render();

        this.listenTo(this.model, "change", this.update_streak_bar);
        this.listenTo(this.collection, "add", this.update_attempt_display);

    },

    render: function() {
            // this.$el.html(this.template(this.data_model.attributes));
        this.$el.html(this.template());
        this.update_streak_bar();
        this.update_attempt_display();

    },

    update_streak_bar: function() {
            // update the streak bar UI
        this.$(".progress-bar")
            .css("width", this.model.get("streak_progress") + "%")
            .toggleClass("completed", this.model.get("complete"));
        this.$(".progress-points").html(this.model.get("points") > 0 ? "(" + this.model.get("points") + " " + gettext("points") + ")" : "");
    },

    update_attempt_display: function() {

        var attempt_text = "";

        this.collection.forEach(function(model) {
                attempt_text = (model.get("correct") ? "<span><b>&#10003;</b></span> " : "<span>&#10007;</span> ") + attempt_text;
        });

        this.$(".attempts").html(attempt_text);
        this.$(".attempts span:last").css("font-size", "1.1em");
    }
});


window.ExerciseRelatedVideoView = Backbone.View.extend({

    template: HB.template("exercise/exercise-related-videos"),

    render: function(data) {

        var self = this;

        this.$el.html(this.template(data));

        // the following is adapted from khan-exercises/related-videos.js to recreate thumbnail hover effect
        // TODO(jamalex): this can all probably be replaced by a simple CSS3 rule
        var captionHeight = 45;
        var marginTop = 23;
        var options = {duration: 150, queue: false};
        this.$(".related-video-box")
            .delegate(".thumbnail", "mouseenter mouseleave", function(e) {
                    var isMouseEnter = e.type === "mouseenter";
                self.$(e.currentTarget).find(".thumbnail_label").animate(
                        {marginTop: marginTop + (isMouseEnter ? 0 : captionHeight)},
                        options)
                    .end()
                    .find(".thumbnail_teaser").animate(
                        {height: (isMouseEnter ? captionHeight : 0)},
                        options);
            });

    }

});

function seeded_shuffle(source_array, random) {
    var array = source_array.slice(0);
    var m = array.length, t, i;

    // While there remain elements to shuffle…
    while (m) {

        // Pick a remaining element…
        i = Math.floor(random() * m--);

        // And swap it with the current element.
        t = array[m];
        array[m] = array[i];
        array[i] = t;
    }

    return array;
}
