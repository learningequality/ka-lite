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

    tagName: "td",

    template: _.template($("#all-groups-list-entry-template").html()),

    className: "student-grp-row",

    attributes: {draggable: true},

    initialize: function(options) {
        this.id = this.model.id;
        this.listenTo(this.model, 'change', this.render);

        playlists.fetch();
    },

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

        playlists.fetch();
        groups.fetch();
    },

    addNewGroup: function(group) {
        var view = new GroupView({model: group});
        $("#student-groups").append(view.render().el);
    },

    addAllGroups: function() {
        groups.each(this.addNewGroup);
    }
});

function appendStudentGrp(id, studentGrpName) {
  var selector = sprintf("tr[playlist-id|=%s] ul", id);
  $(selector).append('<li>'+studentGrpName+'</li>');
}

function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  var target = ev.currentTarget;
  var studentGrpId = target.getAttribute('student-grp-id');
  var studentGrp = target.innerText || target.textContent;
  var dataTransfer = ev.originalEvent.dataTransfer;
  dataTransfer.setData('student-grp', studentGrp);
  dataTransfer.setData('student-grp-id', studentGrpId);
}

function drop(ev) {
  var target = ev.currentTarget;
  var playlistId = target.getAttribute('playlist-id');
  var dataTransfer = ev.originalEvent.dataTransfer;
  ev.preventDefault();
  var studentGrp = dataTransfer.getData('student-grp');
  var studentGrpId = dataTransfer.getData('student-grp-id');
  var ids = [studentGrpId];
  appendStudentGrp(playlistId, studentGrp);

  assignStudentGroups(playlistId, ids);
}

// modify the groups assigned to a playlist
function assignStudentGroups(playlist_id, group_ids_assigned) {
  console.log(ALL_PLAYLISTS_URL);
  var PLAYLIST_DETAIL_URL = ALL_PLAYLISTS_URL + playlist_id + "/"; // note: cleanup to something more readable
  var groups_assigned = group_ids_assigned.map(function (id) { return {"id": id}; });
  doRequest(PLAYLIST_DETAIL_URL,
            {"groups_assigned": groups_assigned},
            {"dataType": "text", // use text so jquery doesn't do the error callback since the server returns an empty response body
             "type": "PATCH"}).success(function(res) {
               console.log(res);
               clear_messages();
              show_message("success", gettext("Successfully updated playlist groups."));
            }).error(function(e) {
              if (e.status === 404) {
                clear_messages();
                show_message("error", gettext("That playlist cannot be found."));
              }
            });
}

function appendPlaylistStudentGroupRow(playlist) {
    return sprintf('<tr class="droppable" playlist-id="%(id)s"><td><ul></ul></td></tr>', playlist);
}

function displayPlaylists() {
    doRequest(ALL_PLAYLISTS_URL).success(function(data) {
        data.objects.map(function(playlist) {
            var playlistTitleRow = sprintf("<tr class='droppable title' playlist-id='%(id)s'><td>%(title)s</td></tr>", playlist);
            var playlistStudentGroupsRow = appendPlaylistStudentGroupRow(playlist);
            $("#playlists").append(playlistTitleRow + playlistStudentGroupsRow);
            $("tr.title").click(function(e) {
                $(e.currentTarget.nextSibling).toggle();
            });

            playlist.groups_assigned.map(function(group) {
                appendStudentGrp(group.id, group.name);
            });
            $(".droppable").on('dragover', allowDrop);
            $(".droppable").on('drop', drop);
        });
    });
}

$(function() {
    // displayGroups();
    displayPlaylists();

    $("tr.title+tr").hide();

    var app = new AppView;

});
