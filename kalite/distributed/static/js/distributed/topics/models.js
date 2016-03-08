var Backbone = require("base/backbone");
var get_params = require("utils/get_params");
var sprintf = require("sprintf-js").sprintf;

// Models
var TopicNode = Backbone.Model.extend({

    initialize: function(options) {
        if (this.get("entity_kind")===undefined && this.get("kind")!==undefined){
            this.set("entity_kind", this.get("kind"));
        }
    }
});

// Collections
var TopicCollection = Backbone.Collection.extend({
    model: TopicNode,

    initialize: function(options) {

        var self = this;
        
        this.parent = options.parent;

        this.channel = options.channel;

        this.listenToOnce(this, "sync", function() {self.loaded = true;});
    },

    url: function() {
        return ("ALL_TOPICS_URL" in window)? get_params.setGetParam(sprintf(ALL_TOPICS_URL, {channel_name: this.channel}), "parent", this.parent) : null;
    }
});

module.exports = {
    TopicNode: TopicNode,
    TopicCollection: TopicCollection
};