var Backbone = require("base/backbone");
var _ = require("underscore");
var seeded_shuffle = require("utils/shuffle");
var get_params = require("utils/get_params");
var seedrandom = require("seedrandom");

var ContentModels = require("content/models");

var ds = window.ds || {};

var ExerciseParams = {
    STREAK_CORRECT_NEEDED: (ds.distributed || {}).streak_correct_needed || 8,
    STREAK_WINDOW: 10,
    FIXED_BLOCK_EXERCISES: (ds.distributed || {}).fixed_block_exercises || 0
};


var ExerciseDataModel = ContentModels.ContentDataModel.extend({
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

        _.bindAll(this, "url", "update_if_needed_then", "as_user_exercise", "get_framework");

        var self = this;

        // store the provided seed as an object attribute, so it will be available after a fetch
        this.listenTo(this, "change:seed", function() { self.seed = self.get("seed") || self.seed; });

    },

    update_if_needed_then: function(callback) {
        // TODO(jamalex): use a better method for checking status of lazy loading
        if (this.get("id") !== this.get("name")) {
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
    },

    get_framework: function() {
        return this.get("uses_assessment_items") ? "perseus" : "khan-exercises";
    }

});

var AssessmentItemModel = Backbone.Model.extend({

    urlRoot: function() {
        var base = window.sessionModel.get("ALL_ASSESSMENT_ITEMS_URL"); // Has a trailing '/'
        return base.slice(0, base.length - 1); // Remove it so the url can be properly built.
    },

    get_item_data: function() {
        return JSON.parse(this.get("item_data"));
    }

});

var ExerciseLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current exercise.
    */

    defaults: {
        streak_progress: 0,
        points: 0,
        attempts: 0
    },

    initialize: function() {

        _.bindAll(this, "save", "attempts_since_completion", "fixed_block_questions_remaining");

    },

    save: function() {

        var self = this;

        var already_complete = this.get("complete");

        if (this.get("attempts") > 20 && !this.get("complete")) {
            this.set("struggling", true);
        }

        this.set("complete", this.get("streak_progress") >= 100);

        if (!already_complete && this.get("complete")) {
            this.set({
                "struggling": false,
                "completion_timestamp": window.statusModel.get_server_time(),
                "attempts_before_completion": this.get("attempts")
            }, {silent: true});
        }

        this.set("latest_activity_timestamp", window.statusModel.get_server_time(), {silent: true});
        // call the super method that will actually do the saving
        return Backbone.Model.prototype.save.call(this);
    },

    attempts_since_completion: function() {
        if (!this.get("complete")) {
            return 0;
        }
        return this.get("attempts") - this.get("attempts_before_completion");
    },

    fixed_block_questions_remaining: function() {
        return ExerciseParams.FIXED_BLOCK_EXERCISES - this.attempts_since_completion();
    },

    urlRoot: function() {
        return window.sessionModel.get("GET_EXERCISE_LOGS_URL");
    },

});


var ExerciseLogCollection = ContentModels.ContentLogCollection.extend({

    model: ExerciseLogModel,

    model_id_key: "exercise_id",

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            var data = {
                "user": window.statusModel.get("user_uri")
            };
            data[this.model_id_key] = this.content_model.get("id");
            return new this.model(data);
        }
    }

});


var AttemptLogModel = Backbone.Model.extend({
    /*
    Contains data about the user's response to a particular exercise instance.
    */

    urlRoot: function() {
        return window.sessionModel.get("GET_ATTEMPT_LOGS_URL");
    },

    defaults: {
        complete: false,
        points: 0,
        context_type: "",
        context_id: "",
        response_count: 0
    },

    to_object: function() {
        return _.clone(this.attributes);
    },

    add_response_log_event: function(ev) {

        var response_log = this.get("response_log") || [];

        // set the timestamp to the current time
        ev.timestamp = window.statusModel.get_server_time();

        // add the event to the response log list
        response_log.push(ev);

        this.set("response_log", response_log);

    },

    parse: function(response) {
        if (response) {
            if (response.response_log) {
                response.response_log = JSON.parse(response.response_log);
            }
        }
        return response;
    },

    toJSON: function(options) {
        var output = Backbone.Model.prototype.toJSON.call(this);
        if (output.response_log) {
            output.response_log = JSON.stringify(output.response_log);
        }
        return output;
    }

});


var AttemptLogCollection = Backbone.Collection.extend({

    model: AttemptLogModel,

    initialize: function(models, options) {
        this.filters = $.extend({
            "user": window.statusModel.get("user_id"),
            "limit": ExerciseParams.STREAK_WINDOW
        }, options);
    },

    url: function() {
        return get_params.setGetParamDict(this.model.prototype.urlRoot(), this.filters);
    },

    to_objects: function() {
        return this.map(function(model){ return model.to_object(); });
    },

    add_new: function(attemptlog) {
        if (this.length == ExerciseParams.STREAK_WINDOW) {
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
        return Math.min((streak_progress / ExerciseParams.STREAK_CORRECT_NEEDED) * 100, 100);
    },

    get_streak_points: function() {
        // only include attempts that were correct (others won't have points)
        var filtered_attempts = this.filter(function(attempt) { return attempt.get("correct"); });
        // add up and return the total number of points represented by these attempts
        // (only include the latest STREAK_CORRECT_NEEDED attempts, so the user doesn't get too many points)
        var total = 0;
        for (var i = 0; i < Math.min(ExerciseParams.STREAK_CORRECT_NEEDED, filtered_attempts.length); i++) {
            total += filtered_attempts[i].get("points");
        }
        return total;
    },

    calculate_points_per_question: function(basepoints) {
        // for comparability with the original algorithm (when a streak of 10 was needed),
        // we calibrate the points awarded for each question (note that there are no random bonuses now)
        return Math.round((basepoints * 10) / ExerciseParams.STREAK_CORRECT_NEEDED);
    }

});


var TestDataModel = Backbone.Model.extend({
    /*
    Contains data about a particular student test.
    */

    url: function() {
        return "/test/api/test/" + this.get("test_id") + "/";
    }
});


var TestLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current test.
    */

    defaults: {
        index: 0,
        complete: false,
        started: false
    },

    init: function(options) {

        _.bindAll(this, "get_item_data", "save");

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

        // TODO (rtibbles): qUnit or other javascript unit testing to set up tests for this code.
        if(typeof(test_data_model)==="object"){

            var random = seedrandom(this.get("user"));

            var items = $.parseJSON(test_data_model.get("ids"));

            var initial_seed = test_data_model.get("seed");

            var repeats = test_data_model.get("repeats");

            // Final seed and item sequences.
            this.seed_sequence = [];

            this.item_sequence = [];

            /*
            Loop over every repeat, adding each exercise_id in turn to item_sequence.
            Increment initial_seed on each inner iteration to give unique seeds across
            all exercises. This will prevent similarly generated exercises from appearing identical.
            This will have the net effect of a fixed sequence of exercise_ids, repeating
            'repeats' times. Build seed sequences per item, so that sequence of seeds can be shuffled
            per item, giving the net result that across tests, the seed/item pairs are matched, but the
            order the seeds appear in within the item repeat blocks is different for each test taker.
            */
            var item_seed_sequence = [];

            for(j=0; j < repeats; j++){
                for(i=0; i < items.length; i++){
                    if(j===0){
                        item_seed_sequence[i] = [];
                    }
                    this.item_sequence.push(items[i]);
                    item_seed_sequence[i].push(initial_seed);
                    initial_seed+=1;
                }
            }
            for(i=0; i < items.length; i++){
                item_seed_sequence[i] = seeded_shuffle(item_seed_sequence[i], random);
            }

            for(j=0; j < repeats; j++){
                for(i=0; i < items.length; i++){
                    this.seed_sequence.push(item_seed_sequence[i][j]);
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


var TestLogCollection = Backbone.Collection.extend({

    model: TestLogModel,

    initialize: function(models, options) {
        this.test_id = options.test_id;
    },

    url: function() {
        return "/test/api/testlog/?" + $.param({
            "test": this.test_id,
            "user": window.statusModel.get("user_id")
        });
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            return new TestLogModel({
                "user": window.statusModel.get("user_uri"),
                "test": this.test_id
            });
        }
    }

});


var QuizDataModel = Backbone.Model.extend({

    defaults: {
        repeats: (ds.distributed || {}).quiz_repeats || 3
    },

    initialize: function() {
        this.set({
            ids: this.get_exercise_ids_from_playlist_entry(this.get("entry")),
            quiz_id: this.get("entry").get("entity_id"),
            seed: this.get("entry").get("seed") || null
        });
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
        return _.map(new Backbone.Collection(temp_collection.slice(left_index)).where({"entity_kind": "Exercise"}), function(value){return value.get("entity_id");});
    }
});


var QuizLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current test.
    */

    defaults: {
        index: 0,
        complete: false,
        attempts: 0,
        total_correct: 0
    },

    init: function(options) {

        _.bindAll(this, "get_item_data", "save", "add_response_log_item", "get_latest_response_log_item");

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

            var random = seedrandom(this.get("user") + this.get("attempts"));

            var items = quiz_data_model.get("ids");

            var repeats = quiz_data_model.get("repeats");

            var initial_seed = seedrandom(this.get("user") + this.get("attempts"))()*1000;

            this.item_sequence = [];

            this.seed_sequence = [];

            for(j=0; j < repeats; j++){
                this.item_sequence.push(items);
                for(i=0; i < items.length; i++){
                    this.seed_sequence.push(initial_seed);
                    initial_seed+=1;
                }
            }

            this.item_sequence = _.flatten(this.item_sequence);

            this.item_sequence = seeded_shuffle(this.item_sequence, random);

        }
        return {
            exercise_id: this.item_sequence[this.get("index")],
            seed: this.seed_sequence[this.get("index")]
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

                    });
                }

                this.trigger("complete");
            }
        }

        Backbone.Model.prototype.save.call(this);
    },

    add_response_log_item: function(data) {

        // inflate the stored JSON if needed
        if (!this._response_log_cache) {
            this._response_log_cache = JSON.parse(this.get("response_log") || "[]");
        }

        if(!this._response_log_cache[this.get("attempts")]){
            this._response_log_cache.push(0);
        }
        // add the event to the response log list
        if(data.correct){
            this._response_log_cache[this.get("attempts")] += 1;
            if(this.get("attempts")===0) {
                this.set({
                    total_correct: this.get("total_correct") + 1
                });
            }
        }
        // deflate the response log list so it will be saved along with the model later
        this.set("response_log", JSON.stringify(this._response_log_cache));

    },

    get_latest_response_log_item: function() {

        // inflate the stored JSON if needed
        if (!this._response_log_cache) {
            this._response_log_cache = JSON.parse(this.get("response_log") || "[]");
        }

        // add the event to the response log list

        return this._response_log_cache[this.get("attempts")-1];

    },

    urlRoot: "/api/playlists/quizlog/"

});


var QuizLogCollection = Backbone.Collection.extend({

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
                "user": window.statusModel.get("user_uri"),
                "quiz": this.quiz
            });
        }
    }

});

module.exports = {
    ExerciseParams: ExerciseParams,
    ExerciseDataModel: ExerciseDataModel,
    ExerciseLogModel: ExerciseLogModel,
    ExerciseLogCollection: ExerciseLogCollection,
    AssessmentItemModel: AssessmentItemModel,
    AttemptLogModel: AttemptLogModel,
    AttemptLogCollection: AttemptLogCollection,
    TestDataModel: TestDataModel,
    TestLogModel: TestLogModel,
    TestLogCollection: TestLogCollection,
    QuizDataModel: QuizDataModel,
    QuizLogModel: QuizLogModel,
    QuizLogCollection: QuizLogCollection
};
