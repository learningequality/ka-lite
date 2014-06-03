
// add some dummy features onto the Exercises object to make khan-exercises.js happy
window.Exercises = {
    completeStack: {
        getUid: function() { return 0; },
        getCustomStackID: function() { return 0; }
    },
    currentCard: {
        attributes: {},
        get: function() {}
    },
    RelatedVideos: {
        render: function() {}
    },
    getCurrentFramework: function() { return "khan-exercises"; },
    incompleteStack: [0],
    PerseusBridge: {
        cleanupProblem: function() {}
    }
};


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
            "lastCountHints": 0, // TODO: could store and pass down number of hints used
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

    defaults: {
        streak_progress: 0
    },

    initialize: function() {

        _.bindAll(this);

    },

    save: function() {

        var self = this;

        var already_complete = this.get("complete");

        if (this.get("attempts") > 20 && !this.get("complete")) {
            this.set("struggling", true);
        }

        this.set("complete", this.get("streak_progress") >= 100);

        if (!already_complete && this.get("complete")) {
            this.set("struggling", false);
            this.set("completion_timestamp", window.statusModel.get_server_time());
            this.set("attempts_before_completion", this.get("attempts"));
        }

        // call the super method that will actually do the saving
        return Backbone.Model.prototype.save.call(this);
    },

    urlRoot: "/api/exerciselog/"

});

window.ExerciseLogCollection = Backbone.Collection.extend({

    model: ExerciseLogModel,

    initialize: function(models, options) {
        this.exercise_id = options.exercise_id;
    },

    url: function() {
        return "/api/exerciselog/?" + $.param({
            "exercise_id": this.exercise_id,
            "user": window.statusModel.get("user_id")
        });
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            return new ExerciseLogModel({
                "exercise_id": this.exercise_id,
                "user": window.statusModel.get("user_uri")
            });
        }
    }

});


window.AttemptLogModel = Backbone.Model.extend({
    /*
    Contains data about the user's response to a particular exercise instance.
    */

    urlRoot: "/api/attemptlog/",

    defaults: {
        complete: false,
        points: 0,
        context_type: "",
        context_id: "",
        response_count: 0,
        response_log: "[]"
    },

    initialize: function(options) {

    },

    add_response_log_event: function(ev) {

        // inflate the stored JSON if needed
        if (!this._response_log_cache) {
            this._response_log_cache = JSON.parse(this.get("response_log") || "[]");
        }

        // set the timestamp to the current time
        ev.timestamp = window.statusModel.get_server_time();

        // add the event to the response log list
        this._response_log_cache.push(ev);

        // deflate the response log list so it will be saved along with the model later
        this.set("response_log", JSON.stringify(this._response_log_cache));

    }

});


window.AttemptLogCollection = Backbone.Collection.extend({

    model: AttemptLogModel,

    STREAK_WINDOW: 10,
    STREAK_CORRECT_NEEDED: 8,

    initialize: function(models, options) {
        this.exercise_id = options.exercise_id;
        this.context_type = options.context_type;
    },

    url: function() {
        return "/api/attemptlog/?" + $.param({
            "exercise_id": this.exercise_id,
            "user": window.statusModel.get("user_id"),
            "limit": this.STREAK_WINDOW,
            "context_type": this.context_type
        });
    },

    add_new: function(attemptlog) {
        if (this.length == this.STREAK_WINDOW) {
            this.pop();
        }
        this.unshift(attemptlog);
    },

    get_streak_progress: function() {
        var count = 0;
        this.forEach(function(model) {
            count += model.get("correct") ? 1 : 0;
        });
        return count;
    },

    get_streak_progress_percent: function() {
        var streak_progress = this.get_streak_progress();
        return Math.min((streak_progress / this.STREAK_CORRECT_NEEDED) * 100, 100);
    },

    get_streak_points: function() {
        // only include attempts that were correct (others won't have points)
        var filtered_attempts = this.filter(function(attempt) { return attempt.get("correct"); });
        // add up and return the total number of points represented by these attempts
        // (only include the latest STREAK_CORRECT_NEEDED attempts, so the user doesn't get too many points)
        var total = 0;
        for (var i = 0; i < Math.min(this.STREAK_CORRECT_NEEDED, filtered_attempts.length); i++) {
            total += filtered_attempts[i].get("points");
        }
        return total;
    },

    calculate_points_per_question: function(basepoints) {
        // for comparability with the original algorithm (when a streak of 10 was needed),
        // we calibrate the points awarded for each question (note that there are no random bonuses now)
        return Math.round((basepoints * 10) / this.STREAK_CORRECT_NEEDED);
    }

});

window.TestDataModel = Backbone.Model.extend({
    /*
    Contains data about a particular student test.
    */

    url: function() {
        return "/test/api/test/" + this.get("title") + "/"
    }
})

window.TestLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current test.
    */

    defaults: {
        index: 0,
        complete: false,
        started: false
    },

    init: function(options) {

        _.bindAll(this);

        var self = this;

    },

    get_item_data: function(test_data_model) {
        /*
        This function is designed to give a deterministic test sequence for an individual, based
        on their userModel URI. As such, each individual will always have the same generated test
        sequence, but it is, for all intents and purposes, randomized across individuals.
        */

        /*
        Seed random generator here so that it increments all seed randomization blocks.
        If seeded inside each call to the function, then the blocks of seeds for each user
        would be identically shuffled.
        */
        if(typeof(test_data_model)==="object"){

            var random = new Math.seedrandom(this.get("user"));

            var items = $.parseJSON(test_data_model.get("ids"));

            var initial_seed = test_data_model.get("seed");

            var repeats = test_data_model.get("repeats");

            var block_seeds = [];

            // Create list of seeds incremented from initial_seed, one for every repeat.
            for(i=0; i < repeats; i++){
                block_seeds.push(initial_seed + i);
            }

            // Cache random shuffling of block seeds for each exercise_id.
            var shuffled_block_seeds_gen = {}

            // Final seed and item sequences.
            this.seed_sequence = []

            this.item_sequence = []

            /*
            Loop over every repeat, adding each exercise_id in turn to item_sequence.
            On first loop, create shuffled copy of block_seeds for each exercise_id.
            Add seed from shuffled block_seeds copy to seed_sequence.
            This will have the net effect of a fixed sequence of exercise_ids, repeating
            'repeats' times, with each exercise_id having a shuffled sequence of seeds across blocks.
            */
            for(j=0; j < repeats; j++){
                for(i=0; i < items.length; i++){
                    if(j==0){
                        shuffled_block_seeds_gen[i] = seeded_shuffle(block_seeds, random);
                    }
                    this.item_sequence.push(items[i]);
                    this.seed_sequence.push(shuffled_block_seeds_gen[i][j]);
                }
            }
        }
        return {
            seed: this.seed_sequence[this.get("index")],
            exercise_id: this.item_sequence[this.get("index")]
        };
    },

    save: function() {

        var self = this;

        var already_complete = this.get("complete");

        if(this.item_sequence){

            if(!this.get("total_number")){
                this.set({
                    total_number: this.item_sequence.length
                });
            }

            if((this.get("index") == this.item_sequence.length) && !already_complete){
                this.set({
                    complete: true
                });
                this.trigger("complete");
            }
        }

        Backbone.Model.prototype.save.call(this);
    },

    urlRoot: "/test/api/testlog/"

});

window.TestLogCollection = Backbone.Collection.extend({

    model: TestLogModel,

    initialize: function(models, options) {
        this.title = options.title;
    },

    url: function() {
        return "/test/api/testlog/?" + $.param({
            "title": this.title,
            "user": window.statusModel.get("user_id")
        });
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            return new TestLogModel({
                "user": window.statusModel.get("user_uri")
            });
        }
    }

});

var QuizDataModel = Backbone.Model.extend({

    defaults: {
        repeats: 3
    },

    initialize: function() {
        this.set({
            ids: this.get_exercise_ids_from_playlist_entry(this.get("entry")),
            quiz_id: this.get("entry").get("entity_id"),
            seed: this.get("entry").get("seed") || null
        })
    },

    get_exercise_ids_from_playlist_entry: function(entry) {
        var temp_collection = entry.collection.slice(0, _.indexOf(entry.collection, entry));
        var left_index = _.reduceRight(entry.collection.slice(0, _.indexOf(entry.collection, entry)), function(memo, value, index){
                if(!memo && value.get("entity_kind")==="Quiz"){
                    return index;
                } else {
                    return memo;
                }
            }, 0);
        return _.map(new Backbone.Collection(temp_collection.slice(left_index)).where({"entity_kind": "Exercise"}), function(value){return value.get("entity_id")});
    }
})

window.QuizLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current test.
    */

    defaults: {
        index: 0,
        complete: false,
        attempts: 0
    },

    init: function(options) {

        _.bindAll(this);

        var self = this;

    },

    get_item_data: function(quiz_data_model) {
        /*
        This function is designed to give a deterministic quiz sequence for an individual, based
        on their userModel URI. As such, each individual will always have the same generated quiz
        sequence, but it is, for all intents and purposes, randomized across individuals.
        */

        /*
        Seed random generator here so that it increments all seed randomization blocks.
        If seeded inside each call to the function, then the blocks of seeds for each user
        would be identically shuffled.
        */
        if(typeof(quiz_data_model)==="object"){

            var random = new Math.seedrandom(this.get("user") + this.get("attempts"));

            var items = quiz_data_model.get("ids");

            var repeats = quiz_data_model.get("repeats");

            this.item_sequence = [];

            for(j=0; j < repeats; j++){
                this.item_sequence.push(items);
            }

            this.item_sequence = _.flatten(this.item_sequence);

            this.item_sequence = seeded_shuffle(this.item_sequence, random);
        }
        return {
            exercise_id: this.item_sequence[this.get("index")]
        };
    },

    save: function() {

        var self = this;

        var already_complete = this.get("complete");

        if(this.item_sequence){

            if(!this.get("total_number")){
                this.set({
                    total_number: this.item_sequence.length
                });
            }

            if((this.get("index") == this.item_sequence.length)){

                this.set({
                    index: 0,
                    attempts: this.get("attempts") + 1
                });

                if(!already_complete) {
                    this.set({
                        complete: true

                    })
                }

                this.trigger("complete");
            }
        }

        Backbone.Model.prototype.save.call(this)
    },

    add_response_log_item: function(data) {

        // inflate the stored JSON if needed
        if (!this._response_log_cache) {
            this._response_log_cache = JSON.parse(this.get("response_log") || "[]");
        }

        if(this._response_log_cache[this.get("attempts")]){
            this._response_log_cache.push(0);
        }
        // add the event to the response log list
        if(data.correct){
            this._response_log_cache[this.get("attempts")] += 1;
            if(this.get("attempts")==0) {
                this.set({
                    total_correct: this.get("total_correct") + 1
                });
            }
        }

        // deflate the response log list so it will be saved along with the model later
        this.set("response_log", JSON.stringify(this._response_log_cache));

    },

    urlRoot: "/api/playlists/quizlog/"

});

window.QuizLogCollection = Backbone.Collection.extend({

    model: QuizLogModel,

    initialize: function(models, options) {
        this.quiz = options.quiz;
    },

    url: function() {
        return "/api/playlists/quizlog/?" + $.param({
            "quiz": this.quiz,
            "user": window.statusModel.get("user_id")
        });
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            return new QuizLogModel({
                "user": window.statusModel.get("user_uri")
            });
        }
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


window.ExerciseView = Backbone.View.extend({

    template: HB.template("exercise/exercise"),

    initialize: function() {

        _.bindAll(this);

        // load the info about the exercise itself
        this.data_model = new ExerciseDataModel({exercise_id: this.options.exercise_id});
        this.data_model.fetch();

        this.render();

        _.defer(this.initialize_khan_exercises_listeners);

    },

    events: {
        "submit .answer-form": "answer_form_submitted"
    },

    render: function() {

        this.$el.html(this.template(this.data_model.attributes));

        this.initialize_listeners();

        if ($("#exercise-inline-style").length == 0) {
            // dummy style container that khan-exercises uses to dynamically add styling to an exercise
            $("head").append("<style id='exercise-inline-style'></style>");
        }

    },

    initialize_listeners: function() {

        // Catch the "next question" button click event -- needs to be explicit (not in "events")
        this.$("#next-question-button").click(this.next_question_clicked);

        this.listenTo(this.data_model, "change:title", this.update_title);

    },

    initialize_khan_exercises_listeners: function() {

        var self = this;

        Khan.loaded.then(this.khan_loaded);

        $(Exercises).bind("checkAnswer", this.check_answer);

        $(Exercises).bind("gotoNextProblem", this.goto_next_problem);

        $(Exercises).bind("hintUsed", this.hint_used);

        $(Exercises).bind("newProblem", this.problem_loaded);

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
    }

});


window.ExercisePracticeView = Backbone.View.extend({

    initialize: function() {

        var self = this;

        _.bindAll(this);

        this.exercise_view = new ExerciseView({
            el: this.el,
            exercise_id: this.options.exercise_id
        });

        this.exercise_view.on("ready_for_next_question", this.ready_for_next_question);
        this.exercise_view.on("hint_used", this.hint_used);
        this.exercise_view.on("problem_loaded", this.problem_loaded);

        this.hint_view = new ExerciseHintView({
            el: this.$(".exercise-hint-wrapper")
        });

        window.statusModel.loaded.then(function() {

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

    user_data_loaded: function() {

        // get the exercise log model from the queried collection
        this.log_model = this.log_collection.get_first_log_or_new_log();

        // add some dummy attempt logs if needed, to match it up with the exercise log
        // (this is needed because attempt logs were not added until 0.13.0, so many older users have only exercise logs)
        if (this.attempt_collection.length < this.attempt_collection.STREAK_WINDOW) {
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

        var data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        return this.current_attempt_log;

    },

    check_answer: function(data) {

        $("#check-answer-button").parent().stop(jumpedToEnd=true)

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

    }

});


window.ExerciseTestView = Backbone.View.extend({

    start_template: HB.template("exercise/test-start"),

    stop_template: HB.template("exercise/test-stop"),

    initialize: function() {

        _.bindAll(this);

        if (window.statusModel.get("is_logged_in")) {

            // load the data about this particular test
            this.test_model = new TestDataModel({title: this.options.title})
            var test_model_deferred = this.test_model.fetch()

            // load the data about the user's overall progress on the test
            this.log_collection = new TestLogCollection([], {title: this.options.title});
            var log_collection_deferred = this.log_collection.fetch();

            this.user_data_loaded_deferred = $.when(log_collection_deferred, test_model_deferred).then(this.user_data_loaded);

        }

    },

    finish_test: function() {
        if(this.log_model.get("complete")){
            this.$el.html(this.stop_template())

            $("#stop-test").click(function(){window.location.href = "/"})

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

            this.listenTo(this.log_model, "complete", this.finish_test);

            var question_data = this.log_model.get_item_data(this.test_model);

            var data = $.extend({el: this.el}, question_data);

            this.initialize_new_attempt_log(question_data);

            this.exercise_view = new ExerciseView(data);

            this.exercise_view.on("check_answer", this.check_answer);
            this.exercise_view.on("problem_loaded", this.problem_loaded);
            this.exercise_view.on("ready_for_next_question", this.ready_for_next_question);
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
            context_type: "test" || "",
            context_id: this.options.title || "",
            language: "", // TODO(jamalex): get the current exercise language
            version: window.statusModel.get("version")
        };

        var data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        return this.current_attempt_log;

    },

    check_answer: function(data) {

        $("#check-answer-button").val("Next Question").show()

        $("#check-answer-button").parent().stop(jumpedToEnd=true)

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
            $("#next-question-button").remove()

        });

    }

});

window.ExerciseQuizView = Backbone.View.extend({

    stop_template: HB.template("exercise/quiz-stop"),

    initialize: function(options) {

        _.bindAll(this);

        if (window.statusModel.get("is_logged_in")) {

            this.quiz_model = options.quiz_model;

            // load the data about the user's overall progress on the test
            this.log_collection = new QuizLogCollection([], {quiz: this.quiz_model.get("quiz_id")});
            var log_collection_deferred = this.log_collection.fetch();

            this.user_data_loaded_deferred = $.when(log_collection_deferred).then(this.user_data_loaded);

        }

    },

    finish_quiz: function() {
        this.$el.html(this.stop_template())

        var self = this;

        $("#stop-quiz").click(function(){self.trigger("complete");})
    },

    user_data_loaded: function() {

        // get the quiz log model from the queried collection
        if(!this.log_model){
            this.log_model = this.log_collection.get_first_log_or_new_log();
        }

        this.listenTo(this.log_model, "complete", this.finish_quiz);

        var question_data = this.log_model.get_item_data(this.quiz_model);

        var data = $.extend({el: this.el}, question_data);

        this.initialize_new_attempt_log(question_data);

        this.exercise_view = new ExerciseView(data);

        this.exercise_view.on("check_answer", this.check_answer);
        this.exercise_view.on("problem_loaded", this.problem_loaded);
        this.exercise_view.on("ready_for_next_question", this.ready_for_next_question);

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
            context_type: "quiz" || "",
            context_id: this.options.title || "",
            language: "", // TODO(jamalex): get the current exercise language
            version: window.statusModel.get("version")
        };

        var data = $.extend(defaults, data);

        this.current_attempt_log = new AttemptLogModel(data);

        return this.current_attempt_log;

    },

    check_answer: function(data) {

        $("#check-answer-button").val("Next Question").show()

        $("#check-answer-button").parent().stop(jumpedToEnd=true)

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

    }

});


function seeded_shuffle(source_array, random) {
    var array = source_array.slice(0)
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
