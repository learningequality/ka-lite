// Models
window.ExerciseNode = Backbone.Model.extend({
    
});

// Collections
window.ExerciseCollection = Backbone.Collection.extend({
    url: ("ALL_EXERCISES_URL" in window)? ALL_EXERCISES_URL : null,
    model: ExerciseNode,

    parse: function(response) {
        return _.values(response);
    }
});