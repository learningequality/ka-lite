// Models
window.TopicNode = Backbone.Model.extend({

    coordinates: function () {
        var x_pos = this.get("x_pos") || 0;
        var y_pos = this.get("y_pos") || 0;
        if (x_pos!==0 && y_pos!==0) {
            return [Number(this.get("x_pos")), Number(this.get("y_pos"))];
        } else {
            return null;
        }
        
    }
});

// Collections
window.TopicCollection = Backbone.Collection.extend({
    
    model: TopicNode,

    center_of_mass: function() {
        var x = _.reduce(this.models, function(memo, model){return memo + model.get("x_pos");}, 0)/this.length;
        var y = _.reduce(this.models, function(memo, model){return memo + model.get("y_pos");}, 0)/this.length;
        return [x,y];
    },

    parse: function(response) {
        if (_.isObject(response)) {
            if (_.isArray(response)) {
                return response;
            } else {
                return _.values(response);
            }
        }
    }
});