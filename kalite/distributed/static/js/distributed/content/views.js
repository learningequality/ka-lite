window.ContentBaseView = BaseView.extend({
    initialize: function() {

        _.bindAll(this);

        var self = this;

        window.statusModel.loaded.then(function() {
            // load the info about the content itself
            self.data_model = new ContentDataModel({id: self.options.id});
            if (self.data_model.get("id")) {
                self.data_model.fetch().then(function() {

                    if (window.statusModel.get("is_logged_in")) {

                        self.log_collection = new ContentLogCollection([], {content_model: self.data_model});
                        self.log_collection.fetch().then(self.user_data_loaded);

                    }
                });
            }

        });
    }
});

window.ContentPointsView = Backbone.View.extend({

    initialize: function() {
        this.listenTo(this.model, "change", this.render);
    },

    render: function() {
        this.$el.html(Number(this.model.get("points")));
    }
});