var Group = Backbone.Model;

var GroupList = Backbone.Collection.extend({

    url: function() { return ALL_GROUPS_URL; },

    model: Group,

    parse: function(response) {
        return response.objects;
    }

});

var PlaylistEntry = Backbone.Model;

var PlaylistEntryList = Backbone.Collection.extend({

    model: PlaylistEntry
});

var Playlist = Backbone.Model.extend({

    urlRoot: function() { return sprintf("%(root)s", {root: ALL_PLAYLISTS_URL}); },

    parse: function(response) {
        // initialize the assigned groups list

        if(response) {
            var groupList = new GroupList(response.groups_assigned.map(function(groupdata) {
                return new Group(groupdata);
            }));
            response.groups_assigned = groupList;

        }

        return response;
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