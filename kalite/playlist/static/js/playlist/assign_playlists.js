
var groups = new GroupList;
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

        this.listenTo(this.model.get('groups_assigned'), 'add', this.renderGroups);
        this.listenTo(this.model.get('groups_assigned'), 'remove', this.renderGroups);
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
        group.parentModel = this.model;
        this.$el.find('.playlist-groups').append(view.render().el);
    },

    renderGroups: function() {
        this.$el.find('.playlist-groups').empty();
        this.model.get('groups_assigned').map(this.renderGroup);
    },

    drop: function(ev) {
        ev.preventDefault();
        var target = ev.currentTarget;
        var dataTransfer = ev.originalEvent.dataTransfer;
        var groupID = dataTransfer.getData('student-grp-id');
        var group = groups.get(groupID);
        var groups_assigned = this.model.get('groups_assigned')

        if (groups_assigned.findWhere({"id": group.get("id")}) == null) {
            groups_assigned.add(group);
            this.model.save();
        }
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
        if (groups.findWhere({id: dict.id}) != null) {
            this.$el.html(this.template(dict));
        }

        return this;
    },

    events: {
        'click a': 'remove'
    },

    remove: function(ev) {
        ev.preventDefault();
        var group = this.model;
        var parentModel = this.model.parentModel;

        parentModel.get('groups_assigned').remove(group);
        parentModel.save();
    }
});

var AppView = Backbone.View.extend({

    initialize: function() {
        this.listenTo(groups, 'add', this.addNewGroup);
        this.listenTo(groups, 'reset', this.addAllGroups);

        this.listenTo(playlists, 'add', this.addNewPlaylist);
        this.listenTo(playlists, 'reset', this.addAllPlaylists);

        playlists.fetch();
        groups.fetch({ data: $.param({ facility_id: statusModel.get('facility_id') }) });
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
        var title = playlist.get('title');
        if (title.indexOf("Core") > -1){
            $("#core-playlists").append(view.render().el);
        } else if (title.indexOf("Prerequisite") > -1){
            $("#pre-playlists").append(view.render().el);
        } else if (title.indexOf("Advanced") > -1){
            $("#advanced-playlists").append(view.render().el);
        }
    },

    addAllPlaylists: function() {
        playlists.each(this.addNewPlaylist);
    }
});

$(function() {

    $("tr.title+tr").hide();

    statusModel.loaded.then(function() {
        var app = new AppView;
    });

});
