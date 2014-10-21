// Models
window.TopicNode = Backbone.Model.extend({
    url: function() {
        return ("ALL_TOPICS_URL" in window)? sprintf(decodeURIComponent(ALL_TOPICS_URL), {channel_name: this.channel}) : null;
    },

    initialize: function(options) {
        if (this.get("entity_kind")===undefined && this.get("kind")!==undefined){
            this.set("entity_kind", this.get("kind"));
        }
        this.channel = options.channel;
    }
});

// Collections
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode
});