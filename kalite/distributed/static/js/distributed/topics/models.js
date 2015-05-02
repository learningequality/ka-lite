// Models
window.TopicNode = Backbone.Model.extend({

    initialize: function(options) {
        
        if (this.get("entity_kind")===undefined && this.get("kind")!==undefined){
            this.set("entity_kind", this.get("kind"));
        }
    }
});

// Collections
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode,

    initialize: function(options) {

        var self = this;
        
        this.parent = options.parent;

        this.channel = options.channel;

        this.listenToOnce(this, "sync", function() {self.loaded = true;});
    },

    url: function() {
        return ("ALL_TOPICS_URL" in window)? setGetParam(sprintf(ALL_TOPICS_URL, {channel_name: this.channel}), "parent", this.parent) : null;
    }
});