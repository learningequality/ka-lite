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
        views: 0
    },

    urlRoot: "/api/contentlog/"

});


window.ContentLogCollection = Backbone.Collection.extend({

    model: ContentLogModel,

    initialize: function(models, options) {
        this.content_model = options.content_model;
    },

    url: function() {
        return "/api/contentlog/?" + $.param({
            "content_id": this.content_model.get("id"),
            "user": window.statusModel.get("user_id")
        });
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            return new ContentLogModel({
                "content_id": this.content_model.get("id"),
                "content_source": this.content_model.get("source") || "",
                "content_kind": this.content_model.get("kind"),
                "user": window.statusModel.get("user_uri")
            });
        }
    }

});
