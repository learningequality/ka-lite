var Group = Backbone.Model;

var GroupList = Backbone.Collection.extend({

    url: function() { return ALL_GROUPS_URL; },

    model: Group,

    parse: function(response) {
        return response.objects;
    }

});

var Playlist = Backbone.Model.extend({

    urlRoot: function() { return sprintf("%(root)s", {root: ALL_PLAYLISTS_URL}); },

    initialize: function(attributes) {
        var groupList = new GroupList(this.get('groups_assigned').map(function(groupdata) {
            return new Group(groupdata);
        }));
        this.set({groups_assigned: groupList});
    },

    addGroup: function(group) {
        this.save({groups_assigned: this.groups_assigned + [group]});
    }

});

var PlaylistList = Backbone.Collection.extend({

    model: Playlist,

    url: function() { return ALL_PLAYLISTS_URL; },

    // we make our own parsing mechanism since tastypie includes some metadata in its model list responses
    parse: function(response) {
        return response.objects;
    }
});
