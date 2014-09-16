// Models
window.TopicNode = Backbone.Model.extend({
    url: ("ALL_TOPICS_URL" in window)? ALL_TOPICS_URL : null,

    initialize: function() {
        if (this.get("entity_kind")===undefined && this.get("kind")!==undefined){
            this.set("entity_kind", this.get("kind"));
        }
    }
});

// Collections
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode
});