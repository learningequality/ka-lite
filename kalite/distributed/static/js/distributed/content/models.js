window.ContentDataModel = Backbone.Model.extend({
    /*
    Contains data about a content resource itself, with no user-specific data.
    */

    defaults: {
        description: "",
        title: "",
        author_name: "",
        path: ""
    },

    initialize: function() {

        _.bindAll(this);

    },

    url: function () {
        return "/api/content/" + this.get("content_id");
    }

});

window.ContentLogModel = Backbone.Model.extend({
    /*
    Contains summary data about the user's history of interaction with the current exercise.
    */

    defaults: {
        complete: false,
        points: 0,
        views: 0
    },

    initialize: function() {

        _.bindAll(this);

    },

    save: function() {

        var self = this;

        // call the super method that will actually do the saving
        return Backbone.Model.prototype.save.call(this);
    },

    urlRoot: "/api/contentlog/"

});


window.ContentLogCollection = Backbone.Collection.extend({

    model: ContentLogModel,

    initialize: function(models, options) {
        this.content_id = options.content_id;
    },

    url: function() {
        return "/api/contentlog/?" + $.param({
            "exercise_id": this.content_id,
            "user": window.statusModel.get("user_id")
        });
    },

    get_first_log_or_new_log: function() {
        if (this.length > 0) {
            return this.at(0);
        } else { // create a new exercise log if none existed
            return new ContentLogModel({
                "content_id": this.content_id,
                "user": window.statusModel.get("user_uri")
            });
        }
    }

});
