// Models
window.TopicNode = Backbone.Model.extend({
    url: ("ALL_TOPICS_URL" in window)? ALL_TOPICS_URL : null
});

// Collections
window.TopicCollection = Backbone.Collection.extend({
    model: TopicNode
});