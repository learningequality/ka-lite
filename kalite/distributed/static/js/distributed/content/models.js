var _ = require("underscore");
var Backbone = require("base/backbone");
var get_params = require("utils/get_params");
var setGetParamDict = get_params.setGetParamDict;
var sprintf = require("sprintf-js").sprintf;

var ExtraFieldsBaseModel = Backbone.Model.extend({

    initialize: function() {

        _.bindAll(this, "parse", "toJSON");

    },

    parse: function(response) {
        if (response!==undefined) {
            var extra_fields = response.extra_fields;
            delete response.extra_fields;
            this.database_attrs = Object.keys(response);
            if(extra_fields!==undefined) {
                extra_fields = JSON.parse(extra_fields);
                response = _.extend(response, extra_fields);
            }
        }
        return response;
    },

    toJSON: function() {
        var attributes = _.clone(this.attributes);
        var extra_fields = {};
        for (var property in attributes) {
            if (!_.contains(this.database_attrs, property)) {
                extra_fields[property] = attributes[property];
                delete attributes.property;
            }
        }
        attributes.extra_fields = JSON.stringify(extra_fields);
        return attributes;
    }
});

var ContentDataModel = ExtraFieldsBaseModel.extend({
    /*
    Contains data about a content resource itself, with no user-specific data.
    */

    defaults: {
        description: "",
        title: "",
        author_name: "",
        path: ""
    },

    url: function () {
        return sprintf("/api/content/%s/%s/", this.get("channel"), this.get("id"));
    }

});

var ContentLogModel = ExtraFieldsBaseModel.extend({
    /*
    Contains summary data about the user's history of interaction with the current exercise.
    */

    defaults: {
        complete: false,
        points: 0,
        views: 0,
        progress: 0,
        time_spent: 0
    },

    // Set this here, as models created on the client side do not have it set by parse.
    database_attrs: [
        "user",
        "content_id",
        "points",
        "language",
        "complete",
        "completion_timestamp",
        "completion_counter",
        "time_spent",
        "content_source",
        "content_kind",
        "progress",
        "views",
        "latest_activity_timestamp"
    ],

    initialize: function() {
        _.bindAll(this, "urlRoot", "save", "saveNow", "set_complete");
    },

    urlRoot: function() {
        return window.sessionModel.get("GET_CONTENT_LOGS_URL");
    },

    // We let the view call save whenever it feels like on this model - essentially on every
    // change event that we can register on the content viewer (video playback updating, etc.)
    // However, in order not to overwhelm the server with unnecessary saves, we throttle the save
    // call here. On page exit, 'saveNow' is called to prevent data loss.

    save: _.throttle(function(key, val, options){this.saveNow(key, val, options);}, 30000),

    saveNow: function (key, val, options){
        this.set("latest_activity_timestamp", window.statusModel.get_server_time(), {silent: true});
        Backbone.Model.prototype.save.call(this, key, val, options);
    },

    set_complete: function() {
        var already_complete = this.get("complete");
        this.set({
            progress: 1,
            complete: true,
            completion_counter: (this.get("completion_counter") || 0) + 1
        });
        if (!already_complete) {
            this.set({
                completion_timestamp: window.statusModel.get_server_time()
            });
        }
    }
});


var ContentLogCollection = Backbone.Collection.extend({

    model: ContentLogModel,

    model_id_key: "content_id",

    initialize: function(models, options) {
        options = typeof options !== "undefined" && options !== null ? options : {};
        this.content_model = options.content_model;
        this.content_ids = options.content_ids;
    },

    url: function() {
        data = {
            "user": window.statusModel.get("user_id")
        };
        if (typeof this.content_model !== "undefined") {
            data[this.model_id_key] = this.content_model.get("id");
        } else if (typeof this.content_ids !== "undefined") {
            data[this.model_id_key + "__in"] = this.content_ids;
        }
        return setGetParamDict(this.model.prototype.urlRoot(), data);
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else {
            var data = {
                "content_source": this.content_model.get("source") || "",
                "content_kind": this.content_model.get("kind"),
                "user": window.statusModel.get("user_uri")
            };
            data[this.model_id_key] = this.content_model.get("id");
            return new this.model(data);
        }
    }

});

module.exports = {
    ExtraFieldsBaseModel: ExtraFieldsBaseModel,
    ContentDataModel: ContentDataModel,
    ContentLogModel: ContentLogModel,
    ContentLogCollection: ContentLogCollection
};
