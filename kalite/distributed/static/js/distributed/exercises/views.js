window.ExerciseHintView = BaseView.extend({

    template: HB.template("exercise/exercise-hint"),

    initialize: function() {

        _.bindAll(this);

        this.render();

    },

    render: function() {
        this.$el.html(this.template());
    }

});


window.ExerciseProgressView = BaseView.extend({

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
            if (model.has("correct")) {
                attempt_text = (model.get("correct") ? "<span class='correct'><b>&#10003;</b></span> " : "<span class='incorrect'>&#10007;</span> ") + attempt_text;
            }
        });

        this.$(".attempts").html(attempt_text);
        this.$(".attempts span:last").css("font-size", "1.1em");
    }
});


window.ExerciseRelatedVideoView = BaseView.extend({

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


window.ExerciseView = BaseView.extend({

    template: HB.template("exercise/exercise"),

    initialize: function() {

        _.bindAll(this);

        // load the info about the exercise itself
        this.data_model = new ExerciseDataModel({exercise_id: this.options.exercise_id});
        if (this.data_model.exercise_id) {
            this.data_model.fetch();
        }
        // Solved the issue: https://github.com/learningequality/ka-lite/issues/2127.
        Khan.query.debug = null;
        this.render();

        _.defer(this.initialize_khan_exercises_listeners);

    },

    events: {
        "submit .answer-form": "answer_form_submitted",
        "keyup .perseus-input": "click_check_answer_button",
        "click .perseus-input": "assign_input_id",
        "keyup #solutionarea>input": "click_check_answer_button"
    },

    assign_input_id: function(e) {
        $(".perseus-input").each(function () {
            if ( $(this).prop("id").length > 0 ) {
                $(this).removeAttr("id");
            }
        });
        $(e.currentTarget).attr("id", "selected-input");

    },

    click_check_answer_button: function(e) {
        if(e.keyCode == $.ui.keyCode.ENTER) {
            $("#check-answer-button").trigger("click");
        }
    },

    render: function() {

        var data = $.extend(this.data_model.attributes, {test_id: this.options.test_id});

        this.$el.html(this.template(data));

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

        var self = this;

        // TODO-BLOCKER(jamalex): does this need to wait on something, to avoid race conditions?
        if(Khan.loaded) {
            Khan.loaded.then(this.khan_loaded);
        } else {
            _.defer(this.khan_loaded);
        }

        this.listenTo(Exercises, "checkAnswer", this.check_answer);

        this.listenTo(Exercises, "gotoNextProblem", this.goto_next_problem);

        // TODO (rtibbles): Make this nice, not horrible.
        this.listenTo(Exercises, "newProblem", function (ev, data) {
            var answerType = data.answerType;
            if (typeof answerType === "undefined") {
                answerType = (_.flatten((Exercises.PerseusBridge.itemRenderer.getInputPaths() || [[""]])) || [""]).join();
            }

            if (answerType == "multiple") {
                answerType = $("span.sol").map(function(index, item){return $(item).attr("data-forms");}).get().join();
            }

            var checkVal = /number|decimal|rational|proper|improper|mixed|radical|integer|cuberoot/gi;

            if (checkVal.test(answerType)){
                if (typeof self.software_keyboard_view === "undefined") {
                    self.software_keyboard_view = new SoftwareKeyboardView({
                        el: self.$("#software-keyboard-container")
                    });
                }
                if (Exercises.getCurrentFramework()==="khan-exercises"){
                    self.software_keyboard_view.set_input("#solutionarea :input");
                    self.software_keyboard_view.inputs.click(function(event){
                        self.software_keyboard_view.inputs.removeAttr("id");
                        $(event.target).attr("id", "selected-input");
                    });
                } else {
                    self.software_keyboard_view.set_input(".perseus-input:input");
                }
                self.software_keyboard_view.show();
                self.listenTo(self.software_keyboard_view, "enter_pressed", function(){$("#check-answer-button").trigger("click");});
            } else if (typeof self.software_keyboard_view !== "undefined") {
                self.software_keyboard_view.hide();
                self.stopListening(self.software_keyboard_view);
            }
        });

        // some events we only care about if the user is logged in
        if (statusModel.get("is_logged_in")) {
            this.listenTo(Exercises, "hintUsed", this.hint_used);
            this.listenTo(Exercises, "newProblem", this.problem_loaded);
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

        if (typeof question_data === "undefined" || question_data === null) {
            question_data = {};
        }

        var self = this;

        if (typeof question_data.attempts !== "undefined") {

            var attempts = question_data.attempts;
            delete question_data.attempts;

        }

        var defaults = {
            seed: Math.floor(Math.random() * 200)
        };

        question_data = $.extend(defaults, question_data);

        this.data_model.set(question_data);

        this.$("#workarea").html("<center>" + gettext("Loading...") + "</center>");


        // Khan Exercises now moves the solution area around and fails to put it back again after
        // So put it back if it is missing
        if (this.$("#solutionarea").length === 0) {
            $(".solutionarea-placeholder").after('<div id="solutionarea" class="solutionarea fancy-scrollbar"></div>');
        }

        this.data_model.update_if_needed_then(function() {

            if (!self.data_model.get("available")) {
                return self.warn_exercise_not_available();
            }

            var framework = self.data_model.get_framework();

            Exercises.setCurrentFramework(framework);

            if (framework == "khan-exercises") {


                if (Khan.loaded === undefined) {
                    require([window.sessionModel.get("KHAN_EXERCISES_SCRIPT_URL")], self.load_exercises_when_ready);
                } else {
                    self.load_exercises_when_ready();
                }

            } else if (framework == "perseus") {

                self.get_assessment_item(attempts);

            } else {
                throw "Unknown framework: " + framework;
            }

        });

    },

    warn_exercise_not_available: function () {
        show_message("warning", gettext("This content was not found! Please contact your coach or an admin to have it downloaded."));
        this.$("#workarea").html("");
        return false;
    },

    get_assessment_item: function(attempts) {
        var self = this;

        var item_index;

        var assessment_items = self.data_model.get("all_assessment_items") || [];

        if (assessment_items.length === 0) {
            return this.warn_exercise_not_available();
        }

        if (typeof attempts !== "undefined") {

            item_index = attempts % assessment_items.length;

        } else {

            item_index = Math.floor(Math.random() * assessment_items.length);

        }

        // TODO(jamalex): remove this once we figure out why assessment_items[item_index] is an unparsed string
        var current_item = assessment_items[item_index];
        if (typeof current_item == "string") {
            current_item = JSON.parse(current_item);
        }

        self.data_model.set("assessment_item_id", current_item.id);

        $(Exercises).trigger("clearExistingProblem");

        var item = new AssessmentItemModel({id: self.data_model.get("assessment_item_id")});

        clear_messages();


        // Do this in this way, so that if the view is closed prior to the fetch completing
        // successfully, the listens will have been unbound, and the callbacks will not get
        // called.
        this.listenToOnce(item, "sync", self.render_perseus_exercise);
        this.listenToOnce(item, "error", function() {
            self.get_assessment_item(attempts+1);
        });

        item.fetch();
    },

    render_perseus_exercise: function(item) {
        var self = this;
        require([window.sessionModel.get("KHAN_EXERCISES_SCRIPT_URL")], function() {
            // The exercise view can get closed before these loads finish happening, so check
            // that it is still open before proceeding - otherwise, errors can ensue.
            if (!self.closed) {
                Exercises.PerseusBridge.load().then(function() {
                    if (!self.closed) {
                        Exercises.PerseusBridge.render_item(item.get_item_data());
                        $(Exercises).trigger("newProblem", {
                            userExercise: null,
                            numHints: Exercises.PerseusBridge.itemRenderer.getNumHints()
                        });
                    }
                });
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
        this.$("input").qtip("destroy", /* immediate */ true);
        this.closed = true;
        this.remove();
    }

});

window.ExerciseWrapperBaseView = BaseView.extend({

    /**
    * This base class is intended to be extended by all wrappers for the ExerciseView defined above.
    * Methods required on a class extended from this:
    *
    * load_user_data - this method should define the logic for loading any existing user data from the server,
    * ordinarily this data should include both a log_model for the view, and an attempt_collection which records
    * the history of attempts on this activity.
    *
    * user_data_loaded - once the user data is loaded, this should determine how any missing data should be
    * accounted for
    *
    * new_question_data - this should determine the logic for selecting the next question to be displayed, in
    * some cases this may simply mean incrementing a seed or assessment_item_id, in others, it may involve
    * changing the exercise being used.
    *
    * log_model_complete_data - determines what kind of information should be set on the log model for the
    * view if the log model is not already completed.
    *
    * log_model_update_data - determines what kind of information should be set on the log model, regardless
    * of its current 'complete' state.
    *
    * Optional Methods:
    *
    * initialize_subviews - if any views can be initialized straight away, these should be defined in here
    *
    * correct_updates - any updates to make if the question is answered correctly.
    */

    initialize: function() {

        var self = this;

        _.bindAll(this);

        window.statusModel.loaded.then(function() {

            if (self.initialize_subviews) {
                self.initialize_subviews();
            }

            if (window.statusModel.get("is_logged_in")) {

                self.load_user_data();

            }
        });
    },

    initialize_new_attempt_log: function(data) {

        var seed = "";
        var assessment_item_id = "";

        if (this.exercise_view) {
            if (this.exercise_view.data_model) {
                seed = this.exercise_view.data_model.seed || seed;
                assessment_item_id = this.exercise_view.data_model.assessment_item_id || assessment_item_id;
            }
        }

        var defaults = {
            exercise_id: this.options.exercise_id,
            user: window.statusModel.get("user_uri"),
            context_type: this.options.context_type || "",
            context_id: this.options.context_id || "",
            language: "", // TODO(jamalex): get the current exercise language
            version: window.statusModel.get("version"),
            seed: seed,
            assessment_item_id: assessment_item_id
        };

        data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        this.attempt_collection.add(this.current_attempt_log);

        return this.current_attempt_log;

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

    ready_for_next_question: function() {

        var self = this;

        if (this.user_data_loaded_deferred) {

            this.user_data_loaded_deferred.then(function() {

                // if this is the first attempt, or the previous attempt was complete, start a new attempt log
                if (!self.current_attempt_log || self.current_attempt_log.get("complete")) {

                    // will generate a new random seed to use
                    // or in the case of an assessment item exercise, will use number of attempts
                    // to index into next assessment item.

                    self.exercise_view.load_question(self.new_question_data());

                    self.initialize_new_attempt_log({
                        seed: self.exercise_view.data_model.get("seed"),
                        assessment_item_id: self.exercise_view.data_model.get("assessment_item_id"),
                        context_type: self.options.context_type
                    });

                } else { // use the seed already established for this attempt
                    self.exercise_view.load_question({
                        seed: self.current_attempt_log.get("seed"),
                        assessment_item_id: self.current_attempt_log.get("assessment_item_id")
                    });
                }

                self.$(".hint-reminder").show(); // show message about hints

            });

        } else { // not logged in, but just load the next question, for kicks

            self.exercise_view.load_question();

        }


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

            // only change the streak progress and points if we're not already complete
            if (!this.log_model.get("complete")) {
                this.attempt_collection.add_new(this.current_attempt_log);
                if (this.log_model_complete_data) {
                    this.log_model.set(this.log_model_complete_data());
                }
            }

            this.log_model.set(this.log_model_update_data());

            this.log_model.save();

            this.$(".hint-reminder").hide(); // hide message about hints

        }

        // if a correct answer was given, then mark the attempt log as complete
        if (data.correct) {
            this.current_attempt_log.set({
                complete: true
            });
            if (this.correct_updates) {
                this.correct_updates();
            }
        }

        this.current_attempt_log.save();

    },

    update_total_points: function(data) {
        // update the top-right point display, now that we've saved the points successfully
        if (this.log_model.has("points")) {
            window.statusModel.update_total_points(this.log_model.get("points") - this.status_points);
            this.status_points = this.log_model.get("points");
        }
    },

    get_points_per_question: function() {
        return this.attempt_collection.calculate_points_per_question(this.exercise_view.data_model.get("basepoints"));
    },

    check_answer: function(data) {

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

        }

    }

});


window.ExercisePracticeView = ExerciseWrapperBaseView.extend({

    initialize_subviews: function() {
        this.exercise_view = this.add_subview(ExerciseView, {
            el: this.el,
            exercise_id: this.options.exercise_id
        });

        this.listenTo(this.exercise_view, "ready_for_next_question", this.ready_for_next_question);
        this.listenTo(this.exercise_view, "hint_used", this.hint_used);
        this.listenTo(this.exercise_view, "problem_loaded", this.problem_loaded);

        this.hint_view = this.add_subview(ExerciseHintView, {
            el: this.$(".exercise-hint-wrapper")
        });

        this.listenTo(this.exercise_view, "check_answer", this.check_answer);
    },

    load_user_data: function() {

        // load the data about the user's overall progress on the exercise
        this.log_collection = new ExerciseLogCollection([], {exercise_id: this.options.exercise_id});
        var log_collection_deferred = this.log_collection.fetch();

        // load the last 10 (or however many) specific attempts the user made on this exercise
        this.attempt_collection = new AttemptLogCollection([], {exercise_id: this.options.exercise_id, context_type__in: ["playlist", "exercise"]});
        var attempt_collection_deferred = this.attempt_collection.fetch();

        // wait until both the exercise and attempt logs have been loaded before continuing
        this.user_data_loaded_deferred = $.when(log_collection_deferred, attempt_collection_deferred);
        this.user_data_loaded_deferred.then(this.user_data_loaded);

    },

    new_question_data: function() {
        return {attempts: this.log_model.get("attempts")};
    },

    user_data_loaded: function() {

        // get the exercise log model from the queried collection
        this.log_model = this.log_collection.get_first_log_or_new_log();

        this.listenTo(this.log_model, "sync", this.update_total_points);

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
        this.status_points = this.log_model.get("points");

        this.progress_view = this.add_subview(ExerciseProgressView, {
            el: this.$(".exercise-progress-wrapper"),
            model: this.log_model,
            collection: this.attempt_collection
        });

        this.display_message();

    },


    check_answer: function(data) {

        var check_answer_button = $("#check-answer-button");

        check_answer_button.toggleClass("orange", !data.correct).toggleClass("green", data.correct);
        // If answer is incorrect, button turns orangish-red; if answer is correct, button turns back to green (on next page).

        return ExerciseWrapperBaseView.prototype.check_answer.call(this, data);

    },

    hint_used: function() {

        this.current_attempt_log.add_response_log_event({
            type: "hint"
        });

        this.update_and_save_log_models("hint_used", {correct: false, guess: ""});
    },

    log_model_complete_data: function() {
        return {
            streak_progress: this.attempt_collection.get_streak_progress_percent(),
            points: this.attempt_collection.get_streak_points()
        };
    },

    log_model_update_data: function() {
        return {
            attempts: this.log_model.get("attempts") + 1
        };
    },

    display_message: function() {
        var msg;

        var context = {
            numerator: ExerciseParams.STREAK_CORRECT_NEEDED,
            denominator: ExerciseParams.STREAK_WINDOW
        };

        if (!this.log_model.get("complete")) {
            if (this.log_model.get("attempts") > 0) { // don't display a message if the user is already partway into the streak
                msg = "";
            } else {
                msg = gettext("Answer %(numerator)d out of the last %(denominator)d questions correctly to complete your streak.");
            }
        } else {
            msg = gettext("You have finished this exercise!");
        }
        show_message("info", sprintf(msg, context));
    }

});


window.ExerciseTestView = ExerciseWrapperBaseView.extend({

    start_template: HB.template("exercise/test-start"),

    stop_template: HB.template("exercise/test-stop"),

    load_user_data: function() {

        // load the data about this particular test
        this.test_model = new TestDataModel({test_id: this.options.test_id});
        var test_model_deferred = this.test_model.fetch();

        this.attempt_collection = new AttemptLogCollection();

        // load the data about the user's overall progress on the test
        this.log_collection = new TestLogCollection([], {test_id: this.options.test_id});
        var log_collection_deferred = this.log_collection.fetch();

        this.user_data_loaded_deferred = $.when(log_collection_deferred, test_model_deferred).then(this.user_data_loaded);
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

        this.listenTo(this.log_model, "sync", this.update_total_points);

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
                data = $.extend(data, {test_id: this.options.test_id});

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


    check_answer: function(data) {

        this.exercise_view.suppress_button_feedback();

        return ExerciseWrapperBaseView.prototype.check_answer.call(this, data);
    },

    update_and_save_log_models: function(event_type, data) {

        ExerciseWrapperBaseView.prototype.update_and_save_log_models.call(this, event_type, data);

        this.ready_for_next_question();
    },

    new_question_data: function() {
        return this.log_model.get_item_data();
    },

    log_model_update_data: function() {
        return {
            index: this.log_model.get("index") + 1
        };
    },

    correct_updates: function() {
        this.log_model.set({
            total_correct: this.log_model.get("total_correct") + 1
        });
    }

});


window.ExerciseQuizView = ExerciseWrapperBaseView.extend({

    stop_template: HB.template("exercise/quiz-stop"),

    load_user_data: function() {

        this.quiz_model = options.quiz_model;

        this.attempt_collection = new AttemptLogCollection();

        // load the data about the user's overall progress on the test
        this.log_collection = new QuizLogCollection([], {quiz: this.options.context_id});
        var log_collection_deferred = this.log_collection.fetch();

        this.user_data_loaded_deferred = log_collection_deferred.then(this.user_data_loaded);
    },

    finish_quiz: function() {
        this.$el.html(this.stop_template({
            correct: this.log_model.get_latest_response_log_item(),
            total_number: this.log_model.get("total_number")
        }));

        if(this.log_model.get("attempts")==1){
            if(this.points > 0){

                statusModel.update_total_points(statusModel.get("newpoints") + this.points);
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

        this.listenTo(this.log_model, "sync", this.update_total_points);

        this.listenTo(this.log_model, "complete", this.finish_quiz);

        var question_data = this.log_model.get_item_data(this.quiz_model);

        var data = $.extend({el: this.el}, question_data);

        this.exercise_view = this.add_subview(ExerciseView, data);
        this.exercise_view.$("#check-answer-button").attr("value", gettext("Submit Answer"));

        this.listenTo(this.exercise_view, "check_answer", this.check_answer);
        this.listenTo(this.exercise_view, "ready_for_next_question", this.ready_for_next_question);
        this.listenTo(this.exercise_view, "problem_loaded", this.problem_loaded);

    },

    new_question_data: function() {
        return this.log_model.get_item_data();
    },

    correct_updates: function() {
        this.log_model.set({
            points: this.log_model.get("points") + this.get_points_per_question()
        });
    },

    log_model_update_data: function() {
        return {
            index: this.log_model.get("index") + 1
        };
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
