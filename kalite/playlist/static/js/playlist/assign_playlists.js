var Group = Backbone.Model;

var GroupList = Backbone.Collection.extend({

    url: function() { return ALL_GROUPS_URL; },

    model: Group,

    parse: function(response) {
        return response.objects;
    }

});

var groups = new GroupList;

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

var playlists = new PlaylistList;


var GroupView  = Backbone.View.extend({

    tagName: "tr",

    className: "student-grp-row",

    attributes: {draggable: true},

    events: {
        'dragstart td': 'drag'
    },

    template: _.template($("#all-groups-list-entry-template").html()),

    initialize: function(options) {
        this.id = this.model.id;
        this.listenTo(this.model, 'change', this.render);
    },

    render: function() {
        var dict = this.model.toJSON();
        this.$el.html(this.template(dict));
        return this;
    },

    drag: function(ev) {
        var target = ev.currentTarget;
        var dataTransfer = ev.originalEvent.dataTransfer;
        var groupID = this.model.id;
        dataTransfer.setData('student-grp-id', groupID);
    }
});

var PlaylistView = Backbone.View.extend({

    tagName: "tr",

    className: "droppable title",

    template: _.template($("#playlist-template").html()),

    initialize: function() {
        _.bindAll(this);        // so that 'this' would always refer to PlaylistView in all methods

        this.listenTo(this.model.get('groups_assigned'), 'add', this.renderGroup);
        this.listenTo(this.model.get('groups_assigned'), 'reset', this.renderGroups);
    },

    events: {
        'drop': 'drop',
        'dragover': 'allowDrop'
    },

    render: function() {
        var playlist = this;
        var dict = this.model.toJSON();
        this.$el.html(this.template(dict));


        this.renderGroups();

        return this;
    },

    renderGroup: function(group) {
        var view = new PlaylistGroupView({model: group});
        this.$el.find('.playlist-groups').append(view.render().el);
    },

    renderGroups: function() {
        this.model.get('groups_assigned').map(this.renderGroup);
    },

    drop: function(ev) {
        ev.preventDefault();
        var target = ev.currentTarget;
        var dataTransfer = ev.originalEvent.dataTransfer;
        var groupID = dataTransfer.getData('student-grp-id');
        var group = groups.get(groupID);

        this.model.get('groups_assigned').add(group);
        this.model.save();
    },

    allowDrop: function(ev) {
        ev.preventDefault();
        ev.stopPropagation();
    }
});

var PlaylistGroupView = Backbone.View.extend({

    tagName: "tr",

    template: _.template($("#playlist-group-template").html()),

    render: function() {
        var dict = this.model.toJSON();
        this.$el.html(this.template(dict));

        return this;
    }
});

var AppView = Backbone.View.extend({

    initialize: function() {
        this.listenTo(groups, 'add', this.addNewGroup);
        this.listenTo(groups, 'reset', this.addAllGroups);

        this.listenTo(playlists, 'add', this.addNewPlaylist);
        this.listenTo(playlists, 'reset', this.addAllPlaylists);

        playlists.fetch();
        groups.fetch();
    },

    addNewGroup: function(group) {
        var view = new GroupView({model: group});
        $("#student-groups").append(view.render().el);
    },

    addAllGroups: function() {
        groups.each(this.addNewGroup);
    },

    addNewPlaylist: function(playlist) {
        var view = new PlaylistView({model: playlist});
        $("#playlists").append(view.render().el);
    },

    addAllPlaylists: function() {
        playlists.each(this.addNewPlaylist);
    }
});

$(function() {

    $("tr.title+tr").hide();

    var app = new AppView;

});
