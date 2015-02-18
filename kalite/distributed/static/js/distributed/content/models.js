window.ExtraFieldsBaseModel = Backbone.Model.extend({

    initialize: function() {

        _.bindAll(this);

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

window.ContentDataModel = ExtraFieldsBaseModel.extend({
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
        return "/api/content/" + this.get("id");
    }

});

window.ContentLogModel = ExtraFieldsBaseModel.extend({
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
        "views"
    ],

    urlRoot: GET_CONTENT_LOGS_URL,

    save: _.throttle(function(){this.saveNow();}, 30000),

    saveNow: function (){
        Backbone.Model.prototype.save.call(this);
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


window.ContentLogCollection = Backbone.Collection.extend({

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
        return setGetParamDict(this.model.prototype.urlRoot, data);
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
